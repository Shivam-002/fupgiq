from functools import lru_cache
from typing import Annotated

from fastapi import Depends

from app.core.config import Settings, get_settings
from app.services.energy.data.wind.cache import CachedWindDataProvider
from app.services.energy.data.wind.elexon import ElexonWindProvider
from app.services.energy.data.wind.provider import WindDataProvider
from app.services.forecast.service import ForecastService


@lru_cache
def get_wind_provider() -> WindDataProvider:
    settings = get_settings()
    elexon = ElexonWindProvider(
        base_url=settings.elexon_base_url,
        timeout_seconds=settings.elexon_timeout_seconds,
        retries=settings.elexon_retries,
    )
    return CachedWindDataProvider(elexon)


def get_forecast_service(
    provider: Annotated[WindDataProvider, Depends(get_wind_provider)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> ForecastService:
    return ForecastService(
        provider,
        track_record_days=settings.track_record_days,
        fetch_timeout_seconds=settings.request_timeout_seconds,
    )
