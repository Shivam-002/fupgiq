from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

UK = ZoneInfo("Europe/London")
ONE_DAY = timedelta(days=1)


def to_utc(moment: datetime) -> datetime:
    """Naive datetimes are read as UK local time."""
    if moment.tzinfo is None:
        moment = moment.replace(tzinfo=UK)
    return moment.astimezone(UTC)


def uk_date(moment: datetime) -> date:
    return moment.astimezone(UK).date()


def uk_day_bounds(day: date) -> tuple[datetime, datetime]:
    start = datetime.combine(day, time(), UK)
    end = datetime.combine(day + ONE_DAY, time(), UK)
    return start.astimezone(UTC), end.astimezone(UTC)


def same_clock_on(day: date, moment: datetime) -> datetime:
    """`moment`'s UK wall-clock time, placed on `day`."""
    clock = moment.astimezone(UK).time()
    return datetime.combine(day, clock, UK).astimezone(UTC)
