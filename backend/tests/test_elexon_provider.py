from collections.abc import Callable
from datetime import date

import httpx
import pytest

from app.core.exceptions import ProviderUnavailableError
from app.services.energy.data.wind.elexon import ElexonWindProvider
from tests.conftest import utc

pytestmark = pytest.mark.anyio

BASE = "https://elexon.test/api"

FORECAST_ROW = {
    "dataset": "WINDFOR",
    "publishTime": "2026-01-09T09:30:00Z",
    "startTime": "2026-01-10T00:00:00Z",
    "generation": 9200,
}


def actual_row(start: str, published: str, mw: float, fuel: str = "WIND") -> dict:
    return {
        "dataset": "FUELHH",
        "publishTime": published,
        "startTime": start,
        "settlementDate": "2026-01-10",
        "settlementPeriod": 1,
        "fuelType": fuel,
        "generation": mw,
    }


def provider(handler: Callable[[httpx.Request], httpx.Response], retries: int = 2):
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return ElexonWindProvider(
        BASE, timeout_seconds=1, retries=retries, backoff_seconds=0, client=client
    )


async def test_maps_forecasts_and_sends_publish_window() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200, json=[FORECAST_ROW])

    records = await provider(handler).get_forecasts(
        utc("2026-01-09T00:00"), utc("2026-01-09T10:40")
    )

    assert records[0].start_time == utc("2026-01-10T00:00")
    assert records[0].publish_time == utc("2026-01-09T09:30")
    assert records[0].generation_mw == 9200
    assert seen[0].url.path == "/api/datasets/WINDFOR/stream"
    assert seen[0].url.params["publishDateTimeFrom"] == "2026-01-09T00:00:00Z"
    assert seen[0].url.params["publishDateTimeTo"] == "2026-01-09T10:40:00Z"


async def test_actuals_keep_wind_only_and_the_newest_revision() -> None:
    rows = [
        actual_row("2026-01-10T00:00:00Z", "2026-01-10T00:30:00Z", 100),
        actual_row("2026-01-10T00:00:00Z", "2026-01-10T01:00:00Z", 105),
        actual_row("2026-01-10T00:00:00Z", "2026-01-10T00:30:00Z", 9999, fuel="CCGT"),
    ]
    records = await provider(lambda _: httpx.Response(200, json=rows)).get_actuals(
        date(2026, 1, 10), date(2026, 1, 10)
    )
    assert [(r.start_time, r.generation_mw) for r in records] == [(utc("2026-01-10T00:00"), 105)]


async def test_retries_server_errors_then_succeeds() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(502) if calls < 3 else httpx.Response(200, json=[FORECAST_ROW])

    records = await provider(handler).get_forecasts(
        utc("2026-01-09T00:00"), utc("2026-01-09T10:40")
    )
    assert calls == 3
    assert len(records) == 1


async def test_gives_up_after_retries_on_timeouts() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("slow", request=request)

    with pytest.raises(ProviderUnavailableError):
        await provider(handler, retries=2).get_forecasts(
            utc("2026-01-09T00:00"), utc("2026-01-09T10:40")
        )
    assert calls == 3


async def test_rate_limits_are_retried() -> None:
    responses = iter([httpx.Response(429), httpx.Response(200, json=[FORECAST_ROW])])
    records = await provider(lambda _: next(responses)).get_forecasts(
        utc("2026-01-09T00:00"), utc("2026-01-09T10:40")
    )
    assert len(records) == 1


async def test_other_httpx_errors_become_provider_errors() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TooManyRedirects("loop", request=request)

    with pytest.raises(ProviderUnavailableError):
        await provider(handler).get_forecasts(utc("2026-01-09T00:00"), utc("2026-01-09T10:40"))


async def test_client_errors_are_not_retried() -> None:
    calls = 0

    def handler(_: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(400, json={"error": "bad"})

    with pytest.raises(ProviderUnavailableError):
        await provider(handler).get_forecasts(utc("2026-01-09T00:00"), utc("2026-01-09T10:40"))
    assert calls == 1


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, text="<html>not json</html>"),
        httpx.Response(200, json={"data": []}),
        httpx.Response(200, json=[{"startTime": "2026-01-10T00:00:00Z"}]),
        httpx.Response(200, json=[{**FORECAST_ROW, "generation": "lots"}]),
    ],
)
async def test_unexpected_payloads_become_provider_errors(response: httpx.Response) -> None:
    with pytest.raises(ProviderUnavailableError):
        await provider(lambda _: response).get_forecasts(
            utc("2026-01-09T00:00"), utc("2026-01-09T10:40")
        )
