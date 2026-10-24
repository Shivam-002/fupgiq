from datetime import date, datetime

from pydantic import Field

from app.core.schemas import CamelModel


class ForecastPoint(CamelModel):
    time: datetime
    forecast: float = Field(description="Forecast wind generation in MW")


class TrackRecord(CamelModel):
    days: int = Field(description="Past days the figures are based on")
    accuracy: float = Field(description="1 - typical miss / average actual energy")
    typical_miss_mwh: float
    daily_errors_mwh: list[float] = Field(
        description="Forecast minus actual energy for each past day, oldest first"
    )


class ForecastResponse(CamelModel):
    forecast_day: date
    forecast_published_at: datetime
    forecast_energy_mwh: float
    points: list[ForecastPoint]
    track_record: TrackRecord | None
