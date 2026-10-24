import asyncio
from datetime import date, datetime, timedelta

from app.core.exceptions import ForecastNotFoundError, ProviderUnavailableError
from app.core.uk_time import ONE_DAY, same_clock_on, uk_date, uk_day_bounds
from app.services.energy.data.wind.models import ActualRecord, ForecastRecord
from app.services.energy.data.wind.provider import WindDataProvider
from app.services.forecast.calculations import (
    ForecastIndex,
    SelectedForecast,
    TrackRecordStats,
    compare_energy,
    energy_mwh,
    track_record,
)
from app.services.forecast.schemas import ForecastPoint, ForecastResponse, TrackRecord


class ForecastService:
    def __init__(
        self,
        provider: WindDataProvider,
        track_record_days: int,
        fetch_timeout_seconds: float,
    ) -> None:
        self._provider = provider
        self._track_record_days = track_record_days
        self._fetch_timeout = fetch_timeout_seconds

    async def get_forecast(self, now: datetime) -> ForecastResponse:
        """Tomorrow's forecast as of `now`, with the track record."""
        today = uk_date(now)
        forecast_day = today + ONE_DAY
        history = [today - timedelta(days=n) for n in range(self._track_record_days, 0, -1)]

        forecasts, actuals = await self._fetch(history[0], history[-1], now)
        index = ForecastIndex(forecasts)

        points = index.latest_by(*uk_day_bounds(forecast_day), published_by=now)
        if not points:
            raise ForecastNotFoundError()

        actual_mw = {a.start_time: a.generation_mw for a in actuals}
        daily = [
            pair
            for day in history
            if (pair := compare_energy(_seen_day_before(index, day, now), actual_mw))
        ]

        return ForecastResponse(
            forecast_day=forecast_day,
            forecast_published_at=max(p.published_at for p in points),
            forecast_energy_mwh=round(energy_mwh(points), 1),
            points=[ForecastPoint(time=p.time, forecast=p.generation_mw) for p in points],
            track_record=_to_schema(track_record(daily)),
        )

    async def _fetch(
        self, first_day: date, last_day: date, now: datetime
    ) -> tuple[list[ForecastRecord], list[ActualRecord]]:
        # include runs from two days before
        earliest_publish, _ = uk_day_bounds(first_day - 2 * ONE_DAY)
        try:
            async with asyncio.timeout(self._fetch_timeout):
                return await asyncio.gather(
                    self._provider.get_forecasts(earliest_publish, now),
                    self._provider.get_actuals(first_day, last_day),
                )
        except TimeoutError:
            raise ProviderUnavailableError() from None


def _seen_day_before(index: ForecastIndex, day: date, now: datetime) -> list[SelectedForecast]:
    return index.latest_by(*uk_day_bounds(day), published_by=same_clock_on(day - ONE_DAY, now))


def _to_schema(stats: TrackRecordStats | None) -> TrackRecord | None:
    if stats is None:
        return None
    return TrackRecord(
        days=stats.days,
        accuracy=round(stats.accuracy, 4),
        typical_miss_mwh=round(stats.typical_miss_mwh, 1),
        daily_errors_mwh=[round(error, 1) for error in stats.daily_errors_mwh],
    )
