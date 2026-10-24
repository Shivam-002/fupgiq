from app.services.energy.data.wind.models import ForecastRecord
from app.services.forecast.calculations import (
    ForecastIndex,
    SelectedForecast,
    compare_energy,
    energy_mwh,
    track_record,
)
from tests.conftest import forecast_run, utc

DAY_START, DAY_END = utc("2026-01-10T00:00"), utc("2026-01-11T00:00")


def test_picks_the_latest_run_published_by_the_cutoff() -> None:
    index = ForecastIndex(
        forecast_run("2026-01-09T07:30", "2026-01-10T00:00", 24, 100)
        + forecast_run("2026-01-09T09:30", "2026-01-10T00:00", 24, 200)
    )
    points = index.latest_by(DAY_START, DAY_END, published_by=utc("2026-01-09T10:40"))
    assert len(points) == 24
    assert {p.generation_mw for p in points} == {200}
    assert {p.published_at for p in points} == {utc("2026-01-09T09:30")}


def test_never_uses_a_run_published_after_the_cutoff() -> None:
    index = ForecastIndex(
        forecast_run("2026-01-09T09:30", "2026-01-10T00:00", 24, 200)
        + forecast_run("2026-01-09T11:30", "2026-01-10T00:00", 24, 999)
    )
    points = index.latest_by(DAY_START, DAY_END, published_by=utc("2026-01-09T10:40"))
    assert 999 not in {p.generation_mw for p in points}


def test_a_run_published_exactly_at_the_cutoff_counts() -> None:
    index = ForecastIndex(forecast_run("2026-01-09T10:40", "2026-01-10T00:00", 24, 300))
    points = index.latest_by(DAY_START, DAY_END, published_by=utc("2026-01-09T10:40"))
    assert len(points) == 24


def test_returns_nothing_when_no_run_exists_yet() -> None:
    index = ForecastIndex(forecast_run("2026-01-09T11:30", "2026-01-10T00:00", 24, 200))
    assert index.latest_by(DAY_START, DAY_END, published_by=utc("2026-01-09T10:40")) == []


def test_only_returns_hours_inside_the_window() -> None:
    index = ForecastIndex(forecast_run("2026-01-08T22:30", "2026-01-09T21:00", 72, 100))
    points = index.latest_by(DAY_START, DAY_END, published_by=utc("2026-01-09T10:40"))
    assert points[0].time == DAY_START
    assert points[-1].time == utc("2026-01-10T23:00")


def test_each_hour_uses_its_own_latest_value() -> None:
    late_run_covers_only_morning = [
        ForecastRecord(utc("2026-01-10T00:00"), utc("2026-01-09T09:30"), 50)
    ]
    index = ForecastIndex(
        forecast_run("2026-01-09T07:30", "2026-01-10T00:00", 2, 100) + late_run_covers_only_morning
    )
    points = index.latest_by(DAY_START, DAY_END, published_by=utc("2026-01-09T10:40"))
    assert [p.generation_mw for p in points] == [50, 100]


def test_energy_of_hourly_points() -> None:
    points = [SelectedForecast(utc("2026-01-10T00:00"), utc("2026-01-09T09:30"), 250.0)] * 4
    assert energy_mwh(points) == 1000


def test_compare_energy_skips_hours_without_both_half_hour_actuals() -> None:
    points = [
        SelectedForecast(utc("2026-01-10T00:00"), utc("2026-01-09T09:30"), 120),
        SelectedForecast(utc("2026-01-10T01:00"), utc("2026-01-09T09:30"), 120),
    ]
    actual_mw = {
        utc("2026-01-10T00:00"): 100,
        utc("2026-01-10T00:30"): 100,
        utc("2026-01-10T01:00"): 100,
    }
    assert compare_energy(points, actual_mw) == (120, 100)


def test_compare_energy_is_none_without_any_overlap() -> None:
    points = [SelectedForecast(utc("2026-01-10T00:00"), utc("2026-01-09T09:30"), 120)]
    assert compare_energy(points, {}) is None


def test_track_record_figures() -> None:
    stats = track_record([(110, 100), (90, 100), (130, 100)])
    assert stats is not None
    assert stats.days == 3
    assert stats.daily_errors_mwh == [10, -10, 30]
    assert round(stats.typical_miss_mwh, 6) == round(50 / 3, 6)
    assert round(stats.accuracy, 6) == round(1 - (50 / 3) / 100, 6)


def test_track_record_accuracy_never_goes_negative() -> None:
    stats = track_record([(500, 100)])
    assert stats is not None and stats.accuracy == 0


def test_track_record_is_none_without_history() -> None:
    assert track_record([]) is None
