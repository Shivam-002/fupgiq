from datetime import date

import pytest

from app.services.energy.data.wind.cache import CachedWindDataProvider
from tests.conftest import FakeWindProvider, actual_day, forecast_run, utc

pytestmark = pytest.mark.anyio

REAL_NOW = utc("2026-10-24T12:00")


def cached(inner: FakeWindProvider, now=REAL_NOW) -> CachedWindDataProvider:
    return CachedWindDataProvider(inner, clock=lambda: now)


async def test_repeat_forecast_requests_hit_memory() -> None:
    inner = FakeWindProvider(
        forecasts=forecast_run("2026-01-09T09:30", "2026-01-10T00:00", 24, 200)
    )
    cache = cached(inner)

    first = await cache.get_forecasts(utc("2026-01-09T00:00"), utc("2026-01-09T10:40"))
    second = await cache.get_forecasts(utc("2026-01-09T00:00"), utc("2026-01-09T10:40"))

    assert first == second
    assert len(first) == 24
    assert len(inner.forecast_calls) == 1


async def test_cached_days_are_still_filtered_by_publish_time() -> None:
    inner = FakeWindProvider(
        forecasts=forecast_run("2026-01-09T09:30", "2026-01-10T00:00", 24, 200)
        + forecast_run("2026-01-09T11:30", "2026-01-10T00:00", 24, 999)
    )
    cache = cached(inner)
    await cache.get_forecasts(utc("2026-01-09T00:00"), utc("2026-01-09T23:00"))

    earlier = await cache.get_forecasts(utc("2026-01-09T00:00"), utc("2026-01-09T10:40"))
    assert {r.generation_mw for r in earlier} == {200}


async def test_only_missing_days_are_fetched() -> None:
    inner = FakeWindProvider(
        actuals=actual_day(date(2026, 1, 8), 1) + actual_day(date(2026, 1, 9), 2)
    )
    cache = cached(inner)

    await cache.get_actuals(date(2026, 1, 8), date(2026, 1, 8))
    rows = await cache.get_actuals(date(2026, 1, 8), date(2026, 1, 9))

    assert inner.actual_calls == [
        (date(2026, 1, 8), date(2026, 1, 8)),
        (date(2026, 1, 9), date(2026, 1, 9)),
    ]
    assert len(rows) == 96


async def test_days_that_are_not_finished_are_never_cached() -> None:
    inner = FakeWindProvider(actuals=actual_day(date(2026, 1, 9), 2))
    cache = cached(inner, now=utc("2026-01-09T12:00"))

    await cache.get_actuals(date(2026, 1, 9), date(2026, 1, 9))
    await cache.get_actuals(date(2026, 1, 9), date(2026, 1, 9))

    assert len(inner.actual_calls) == 2
