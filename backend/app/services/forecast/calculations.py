from bisect import bisect_left, bisect_right
from collections import defaultdict
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import fmean

from app.services.energy.data.wind.models import ForecastRecord

HOUR = timedelta(hours=1)
FORECAST_STEP = timedelta(hours=1)
ACTUAL_STEP = timedelta(minutes=30)


@dataclass(frozen=True, slots=True)
class SelectedForecast:
    time: datetime
    published_at: datetime
    generation_mw: float


@dataclass(frozen=True, slots=True)
class TrackRecordStats:
    days: int
    accuracy: float
    typical_miss_mwh: float
    daily_errors_mwh: list[float]


class ForecastIndex:
    """Published runs per target time, oldest first."""

    def __init__(self, records: Iterable[ForecastRecord]) -> None:
        runs: dict[datetime, list[ForecastRecord]] = defaultdict(list)
        for record in records:
            runs[record.start_time].append(record)
        for target_runs in runs.values():
            target_runs.sort(key=lambda r: r.publish_time)
        self._runs = runs
        self._targets = sorted(runs)

    def latest_by(
        self, start: datetime, end: datetime, published_by: datetime
    ) -> list[SelectedForecast]:
        """Newest value per target time in [start, end) published by `published_by`."""
        selected = []
        first, last = bisect_left(self._targets, start), bisect_left(self._targets, end)
        for target in self._targets[first:last]:
            runs = self._runs[target]
            count = bisect_right(runs, published_by, key=lambda r: r.publish_time)
            if count:
                run = runs[count - 1]
                selected.append(SelectedForecast(target, run.publish_time, run.generation_mw))
        return selected


def energy_mwh(points: Sequence[SelectedForecast]) -> float:
    return sum(p.generation_mw for p in points) * (FORECAST_STEP / HOUR)


def compare_energy(
    points: Sequence[SelectedForecast], actual_mw: Mapping[datetime, float]
) -> tuple[float, float] | None:
    """(forecast MWh, actual MWh) over the hours where both are known."""
    slots = FORECAST_STEP // ACTUAL_STEP
    forecast = actual = 0.0
    matched = False
    for point in points:
        halves = [actual_mw.get(point.time + n * ACTUAL_STEP) for n in range(slots)]
        if None in halves:
            continue
        forecast += point.generation_mw * (FORECAST_STEP / HOUR)
        actual += sum(v for v in halves if v is not None) * (ACTUAL_STEP / HOUR)
        matched = True
    return (forecast, actual) if matched else None


def track_record(daily: Sequence[tuple[float, float]]) -> TrackRecordStats | None:
    if not daily:
        return None
    errors = [forecast - actual for forecast, actual in daily]
    typical_miss = fmean(abs(error) for error in errors)
    average_actual = fmean(actual for _, actual in daily)
    accuracy = 1 - typical_miss / average_actual if average_actual > 0 else 0.0
    return TrackRecordStats(
        days=len(daily),
        accuracy=min(1.0, max(0.0, accuracy)),
        typical_miss_mwh=typical_miss,
        daily_errors_mwh=errors,
    )
