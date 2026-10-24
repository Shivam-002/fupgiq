from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class ForecastRecord:
    start_time: datetime
    publish_time: datetime
    generation_mw: float


@dataclass(frozen=True, slots=True)
class ActualRecord:
    start_time: datetime
    generation_mw: float
