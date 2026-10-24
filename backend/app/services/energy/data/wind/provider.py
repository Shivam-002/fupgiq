from abc import ABC, abstractmethod
from datetime import date, datetime

from app.services.energy.data.wind.models import ActualRecord, ForecastRecord


class WindDataProvider(ABC):
    """Wind data source interface. Datetimes are UTC."""

    @abstractmethod
    async def get_forecasts(
        self, published_from: datetime, published_to: datetime
    ) -> list[ForecastRecord]:
        """Forecasts published within [published_from, published_to]."""

    @abstractmethod
    async def get_actuals(self, first_day: date, last_day: date) -> list[ActualRecord]:
        """Half-hourly actuals for UK days first_day..last_day."""

    async def aclose(self) -> None:
        return None
