from collections.abc import Callable
from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.exceptions import ProviderUnavailableError
from app.services.energy.data.wind.models import ActualRecord, ForecastRecord
from app.services.energy.data.wind.provider import WindDataProvider
from tests.conftest import FakeWindProvider, actual_day, forecast_run

MakeClient = Callable[[WindDataProvider], TestClient]
AT = "2026-01-09T10:40"


def history(days: int, forecast_mw: float, actual_mw: float, publish_clock: str = "07:30"):
    """Forecasts and actuals for the past days."""
    forecasts: list[ForecastRecord] = []
    actuals: list[ActualRecord] = []
    for n in range(1, days + 1):
        day = date(2026, 1, 9) - timedelta(days=n)
        forecasts += forecast_run(
            f"{day - timedelta(days=1)}T{publish_clock}", f"{day}T00:00", 24, forecast_mw
        )
        actuals += actual_day(day, actual_mw)
    return forecasts, actuals


def tomorrow_runs() -> list[ForecastRecord]:
    return (
        forecast_run("2026-01-09T07:30", "2026-01-10T00:00", 24, 100)
        + forecast_run("2026-01-09T09:30", "2026-01-10T00:00", 24, 200)
        + forecast_run("2026-01-09T11:30", "2026-01-10T00:00", 24, 999)
    )


def test_returns_tomorrow_from_the_latest_run_before_at(make_client: MakeClient) -> None:
    client = make_client(FakeWindProvider(forecasts=tomorrow_runs()))
    body = client.get("/api/forecast", params={"at": AT}).json()

    assert body["forecastDay"] == "2026-01-10"
    assert body["forecastPublishedAt"] == "2026-01-09T09:30:00Z"
    assert body["forecastEnergyMwh"] == 24 * 200
    assert len(body["points"]) == 24
    assert body["points"][0] == {"time": "2026-01-10T00:00:00Z", "forecast": 200}


def test_response_uses_camel_case(make_client: MakeClient) -> None:
    body = (
        make_client(FakeWindProvider(forecasts=tomorrow_runs()))
        .get("/api/forecast", params={"at": AT})
        .json()
    )
    assert set(body) == {
        "forecastDay",
        "forecastPublishedAt",
        "forecastEnergyMwh",
        "points",
        "trackRecord",
    }


def test_track_record_over_the_last_30_days(make_client: MakeClient) -> None:
    forecasts, actuals = history(30, forecast_mw=110, actual_mw=100)
    provider = FakeWindProvider(forecasts=forecasts + tomorrow_runs(), actuals=actuals)
    track = make_client(provider).get("/api/forecast", params={"at": AT}).json()["trackRecord"]

    assert track["days"] == 30
    assert track["typicalMissMwh"] == 240
    assert track["accuracy"] == 0.9
    assert track["dailyErrorsMwh"] == [240] * 30


def test_track_record_ignores_runs_published_after_the_same_clock_time(
    make_client: MakeClient,
) -> None:
    forecasts, actuals = history(30, forecast_mw=110, actual_mw=100)
    late, _ = history(30, forecast_mw=5000, actual_mw=100, publish_clock="22:30")
    provider = FakeWindProvider(forecasts=forecasts + late + tomorrow_runs(), actuals=actuals)
    track = make_client(provider).get("/api/forecast", params={"at": AT}).json()["trackRecord"]
    assert track["typicalMissMwh"] == 240


def test_track_record_is_null_without_history(make_client: MakeClient) -> None:
    body = (
        make_client(FakeWindProvider(forecasts=tomorrow_runs()))
        .get("/api/forecast", params={"at": AT})
        .json()
    )
    assert body["trackRecord"] is None


def test_partial_coverage_returns_the_hours_that_exist(make_client: MakeClient) -> None:
    run = forecast_run("2026-01-08T22:30", "2026-01-08T21:00", 49, 150)
    body = (
        make_client(FakeWindProvider(forecasts=run))
        .get("/api/forecast", params={"at": "2026-01-09T01:15"})
        .json()
    )
    assert len(body["points"]) == 22
    assert body["points"][-1]["time"] == "2026-01-10T21:00:00Z"


def test_accepts_an_explicit_utc_offset(make_client: MakeClient) -> None:
    response = make_client(FakeWindProvider(forecasts=tomorrow_runs())).get(
        "/api/forecast", params={"at": "2026-01-09T10:40:00Z"}
    )
    assert response.status_code == 200


def assert_error(response, status: int, code: str) -> None:
    assert response.status_code == status
    assert response.json()["error"]["code"] == code


def test_no_forecast_yet_returns_404(make_client: MakeClient) -> None:
    response = make_client(FakeWindProvider()).get("/api/forecast", params={"at": AT})
    assert_error(response, 404, "FORECAST_NOT_FOUND")


def test_provider_down_returns_503(make_client: MakeClient) -> None:
    provider = FakeWindProvider(error=ProviderUnavailableError())
    response = make_client(provider).get("/api/forecast", params={"at": AT})
    assert_error(response, 503, "PROVIDER_UNAVAILABLE")


def test_unexpected_provider_crash_returns_clean_500(make_client: MakeClient) -> None:
    provider = FakeWindProvider(error=RuntimeError("secret"))
    response = make_client(provider).get("/api/forecast", params={"at": AT})
    assert_error(response, 500, "INTERNAL_ERROR")
    assert "secret" not in response.text


def test_missing_at_returns_422(make_client: MakeClient) -> None:
    response = make_client(FakeWindProvider()).get("/api/forecast")
    assert_error(response, 422, "INVALID_REQUEST")
    assert response.json()["error"]["message"].startswith("at")


@pytest.mark.parametrize("at", ["yesterday", "2026-01-09", "2026-13-01T10:00", "2026-01-09T25:00"])
def test_malformed_at_returns_422(make_client: MakeClient, at: str) -> None:
    response = make_client(FakeWindProvider()).get("/api/forecast", params={"at": at})
    assert_error(response, 422, "INVALID_REQUEST")


@pytest.mark.parametrize("at", ["2025-12-31T23:59", "2026-02-01T00:00"])
def test_at_outside_january_returns_422(make_client: MakeClient, at: str) -> None:
    response = make_client(FakeWindProvider()).get("/api/forecast", params={"at": at})
    assert_error(response, 422, "INVALID_REQUEST")
    assert "2026-01-01" in response.json()["error"]["message"]
