import asyncio
import logging
from datetime import UTC, date, datetime
from typing import Any

import httpx
from pydantic import AwareDatetime, BaseModel, Field, TypeAdapter, ValidationError

from app.core.exceptions import ProviderUnavailableError
from app.services.energy.data.wind.models import ActualRecord, ForecastRecord
from app.services.energy.data.wind.provider import WindDataProvider

logger = logging.getLogger(__name__)

FORECASTS_PATH = "/datasets/WINDFOR/stream"
ACTUALS_PATH = "/datasets/FUELHH/stream"


class _ForecastRow(BaseModel):
    publish_time: AwareDatetime = Field(alias="publishTime")
    start_time: AwareDatetime = Field(alias="startTime")
    generation: float


class _ActualRow(BaseModel):
    publish_time: AwareDatetime = Field(alias="publishTime")
    start_time: AwareDatetime = Field(alias="startTime")
    fuel_type: str = Field(alias="fuelType")
    generation: float


_FORECAST_ROWS = TypeAdapter(list[_ForecastRow])
_ACTUAL_ROWS = TypeAdapter(list[_ActualRow])


class _RetryableError(Exception):
    pass


def _iso(moment: datetime) -> str:
    return moment.astimezone(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class ElexonWindProvider(WindDataProvider):
    """Elexon BMRS: WINDFOR forecasts and FUELHH actuals."""

    def __init__(
        self,
        base_url: str,
        timeout_seconds: float,
        retries: int,
        backoff_seconds: float = 0.5,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout_seconds
        self._retries = retries
        self._backoff = backoff_seconds
        self._client = client

    async def get_forecasts(
        self, published_from: datetime, published_to: datetime
    ) -> list[ForecastRecord]:
        payload = await self._get(
            FORECASTS_PATH,
            {"publishDateTimeFrom": _iso(published_from), "publishDateTimeTo": _iso(published_to)},
        )
        return [
            ForecastRecord(
                start_time=row.start_time.astimezone(UTC),
                publish_time=row.publish_time.astimezone(UTC),
                generation_mw=row.generation,
            )
            for row in self._parse(_FORECAST_ROWS, payload)
        ]

    async def get_actuals(self, first_day: date, last_day: date) -> list[ActualRecord]:
        payload = await self._get(
            ACTUALS_PATH,
            {
                "settlementDateFrom": first_day.isoformat(),
                "settlementDateTo": last_day.isoformat(),
                "fuelType": "WIND",
            },
        )
        newest: dict[datetime, _ActualRow] = {}
        for row in self._parse(_ACTUAL_ROWS, payload):
            if row.fuel_type != "WIND":
                continue
            # keep the latest revision
            seen = newest.get(row.start_time)
            if seen is None or row.publish_time > seen.publish_time:
                newest[row.start_time] = row
        return [
            ActualRecord(start_time=row.start_time.astimezone(UTC), generation_mw=row.generation)
            for row in sorted(newest.values(), key=lambda r: r.start_time)
        ]

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    def _http(self) -> httpx.AsyncClient:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    async def _get(self, path: str, params: dict[str, str]) -> Any:
        url = f"{self._base_url}{path}"
        last_error: Exception | None = None
        for attempt in range(self._retries + 1):
            if attempt:
                await asyncio.sleep(self._backoff * attempt)
            try:
                response = await self._http().get(url, params=params)
                if response.status_code == 429 or response.status_code >= 500:
                    raise _RetryableError(f"HTTP {response.status_code}")
                response.raise_for_status()
                return response.json()
            except (httpx.TransportError, _RetryableError) as exc:
                last_error = exc
                logger.warning("Elexon %s failed (attempt %d): %r", path, attempt + 1, exc)
            except (httpx.HTTPError, ValueError) as exc:
                logger.error("Elexon %s rejected the request: %r", path, exc)
                raise ProviderUnavailableError() from exc
        raise ProviderUnavailableError() from last_error

    @staticmethod
    def _parse[T](rows: TypeAdapter[T], payload: object) -> T:
        try:
            return rows.validate_python(payload)
        except ValidationError as exc:
            logger.error("Elexon returned data in an unexpected shape: %s", exc)
            raise ProviderUnavailableError(
                "The wind data provider returned unexpected data."
            ) from exc
