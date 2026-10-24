import asyncio
from collections import defaultdict
from collections.abc import Awaitable, Callable, Iterable
from datetime import UTC, date, datetime, time, timedelta

from app.core.uk_time import ONE_DAY, uk_date
from app.services.energy.data.wind.models import ActualRecord, ForecastRecord
from app.services.energy.data.wind.provider import WindDataProvider

ONE_SECOND = timedelta(seconds=1)


def _group[T](rows: Iterable[T], key: Callable[[T], date]) -> dict[date, list[T]]:
    grouped: dict[date, list[T]] = defaultdict(list)
    for row in rows:
        grouped[key(row)].append(row)
    return grouped


class CachedWindDataProvider(WindDataProvider):
    """In-memory cache of finished days."""

    def __init__(
        self,
        inner: WindDataProvider,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self._inner = inner
        self._clock = clock
        self._forecasts: dict[date, list[ForecastRecord]] = {}  # by UTC publish day
        self._actuals: dict[date, list[ActualRecord]] = {}  # by UK day
        self._forecasts_lock = asyncio.Lock()
        self._actuals_lock = asyncio.Lock()

    async def get_forecasts(
        self, published_from: datetime, published_to: datetime
    ) -> list[ForecastRecord]:
        days = await self._load(
            self._forecasts,
            self._forecasts_lock,
            published_from.astimezone(UTC).date(),
            published_to.astimezone(UTC).date(),
            self._fetch_forecasts,
        )
        return [
            r for rows in days for r in rows if published_from <= r.publish_time <= published_to
        ]

    async def get_actuals(self, first_day: date, last_day: date) -> list[ActualRecord]:
        days = await self._load(
            self._actuals, self._actuals_lock, first_day, last_day, self._fetch_actuals
        )
        return [r for rows in days for r in rows]

    async def aclose(self) -> None:
        await self._inner.aclose()

    async def _fetch_forecasts(self, first: date, last: date) -> dict[date, list[ForecastRecord]]:
        start = datetime.combine(first, time(), UTC)
        end = datetime.combine(last + ONE_DAY, time(), UTC) - ONE_SECOND
        rows = await self._inner.get_forecasts(start, end)
        return _group(rows, lambda r: r.publish_time.date())

    async def _fetch_actuals(self, first: date, last: date) -> dict[date, list[ActualRecord]]:
        rows = await self._inner.get_actuals(first, last)
        return _group(rows, lambda r: uk_date(r.start_time))

    async def _load[T](
        self,
        store: dict[date, list[T]],
        lock: asyncio.Lock,
        first: date,
        last: date,
        fetch: Callable[[date, date], Awaitable[dict[date, list[T]]]],
    ) -> list[list[T]]:
        days = [first + timedelta(days=n) for n in range((last - first).days + 1)]
        async with lock:
            missing = [day for day in days if day not in store]
            fresh = await fetch(missing[0], missing[-1]) if missing else {}
            today = self._clock().date()
            for day in missing:
                if day < today:
                    store[day] = fresh.get(day, [])
        return [store[day] if day in store else fresh.get(day, []) for day in days]
