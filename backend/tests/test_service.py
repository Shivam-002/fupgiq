import asyncio
from datetime import date, datetime

import pytest

from app.core.exceptions import ForecastNotFoundError, ProviderUnavailableError
from app.services.energy.data.wind.models import ActualRecord, ForecastRecord
from app.services.forecast.service import ForecastService
from tests.conftest import FakeWindProvider, utc

pytestmark = pytest.mark.anyio


class HangingProvider(FakeWindProvider):
    async def get_forecasts(
        self, published_from: datetime, published_to: datetime
    ) -> list[ForecastRecord]:
        await asyncio.sleep(10)
        return []

    async def get_actuals(self, first_day: date, last_day: date) -> list[ActualRecord]:
        await asyncio.sleep(10)
        return []


async def test_a_hanging_provider_becomes_a_clean_503() -> None:
    service = ForecastService(HangingProvider(), track_record_days=30, fetch_timeout_seconds=0.05)
    with pytest.raises(ProviderUnavailableError):
        await service.get_forecast(utc("2026-01-09T10:40"))


async def test_asks_only_for_data_that_existed_at_now() -> None:
    provider = FakeWindProvider()
    service = ForecastService(provider, track_record_days=30, fetch_timeout_seconds=1)
    with pytest.raises(ForecastNotFoundError):
        await service.get_forecast(utc("2026-01-09T10:40"))

    ((_, published_to),) = provider.forecast_calls
    ((first_day, last_day),) = provider.actual_calls
    assert published_to == utc("2026-01-09T10:40")
    assert (first_day, last_day) == (date(2025, 12, 10), date(2026, 1, 8))
