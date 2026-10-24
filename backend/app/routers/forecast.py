import re
from datetime import datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query

from app.core.config import Settings, get_settings
from app.core.exceptions import InvalidRequestError
from app.core.schemas import ErrorResponse
from app.core.uk_time import to_utc, uk_date
from app.dependencies import get_forecast_service
from app.services.forecast.schemas import ForecastResponse
from app.services.forecast.service import ForecastService

router = APIRouter(tags=["forecast"])

ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    status: {"model": ErrorResponse} for status in (404, 422, 500, 503)
}

# fromisoformat alone would also accept a bare date
AT_FORMAT = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(:\d{2})?(Z|[+-]\d{2}:\d{2})?")


def _parse_at(at: str) -> datetime:
    if AT_FORMAT.fullmatch(at):
        try:
            return to_utc(datetime.fromisoformat(at))
        except ValueError:
            pass
    raise InvalidRequestError("at must be a date and time like 2026-01-12T10:40.")


def simulated_now(
    at: Annotated[
        str,
        Query(
            description="Simulated current time, YYYY-MM-DDTHH:MM in UK local time",
            examples=["2026-01-12T10:40"],
        ),
    ],
    settings: Annotated[Settings, Depends(get_settings)],
) -> datetime:
    now = _parse_at(at)
    if not settings.first_day <= uk_date(now) <= settings.last_day:
        raise InvalidRequestError(
            f"at must fall between {settings.first_day} and {settings.last_day}."
        )
    return now


@router.get(
    "/forecast",
    responses=ERROR_RESPONSES,
    summary="Tomorrow's latest wind forecast and how past forecasts performed",
)
async def get_forecast(
    now: Annotated[datetime, Depends(simulated_now)],
    service: Annotated[ForecastService, Depends(get_forecast_service)],
) -> ForecastResponse:
    return await service.get_forecast(now)
