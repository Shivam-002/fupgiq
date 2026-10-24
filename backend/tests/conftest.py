from collections.abc import Callable, Iterator
from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.uk_time import uk_date
from app.dependencies import get_wind_provider
from app.main import create_app
from app.services.energy.data.wind.models import ActualRecord, ForecastRecord
from app.services.energy.data.wind.provider import WindDataProvider


def utc(text: str) -> datetime:
    return datetime.fromisoformat(text).replace(tzinfo=UTC)


def forecast_run(published: str, first_target: str, hours: int, mw: float) -> list[ForecastRecord]:
    start = utc(first_target)
    return [ForecastRecord(start + timedelta(hours=h), utc(published), mw) for h in range(hours)]


def actual_day(day: date, mw: float) -> list[ActualRecord]:
    start = datetime.combine(day, datetime.min.time(), UTC)
    return [ActualRecord(start + timedelta(minutes=30 * n), mw) for n in range(48)]


class FakeWindProvider(WindDataProvider):
    def __init__(
        self,
        forecasts: list[ForecastRecord] | None = None,
        actuals: list[ActualRecord] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.forecasts = forecasts or []
        self.actuals = actuals or []
        self.error = error
        self.forecast_calls: list[tuple[datetime, datetime]] = []
        self.actual_calls: list[tuple[date, date]] = []

    async def get_forecasts(
        self, published_from: datetime, published_to: datetime
    ) -> list[ForecastRecord]:
        self.forecast_calls.append((published_from, published_to))
        if self.error:
            raise self.error
        return [f for f in self.forecasts if published_from <= f.publish_time <= published_to]

    async def get_actuals(self, first_day: date, last_day: date) -> list[ActualRecord]:
        self.actual_calls.append((first_day, last_day))
        if self.error:
            raise self.error
        return [a for a in self.actuals if first_day <= uk_date(a.start_time) <= last_day]


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture
def make_client() -> Iterator[Callable[[WindDataProvider], TestClient]]:
    app = create_app()

    def build(provider: WindDataProvider) -> TestClient:
        app.dependency_overrides[get_wind_provider] = lambda: provider
        return TestClient(app, raise_server_exceptions=False)

    yield build
    app.dependency_overrides.clear()
