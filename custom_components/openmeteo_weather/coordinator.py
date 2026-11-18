"""Data update coordinators for Open-Meteo Weather."""

from __future__ import annotations

from dataclasses import dataclass
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.util import dt as dt_util

from aioopenmeteo import (
    AirQuality,
    Forecast,
    OpenMeteoClient,
    OpenMeteoError,
    OpenMeteoRateLimitError,
)

from .const import (
    AIR_QUALITY_UPDATE_INTERVAL,
    CONF_FORECAST_DAYS,
    CONF_MINUTELY_15,
    CONF_MODEL,
    DEFAULT_FORECAST_DAYS,
    DEFAULT_MINUTELY_15,
    DEFAULT_MODEL,
    DOMAIN,
    FORECAST_MAX_STALE,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


@dataclass
class OpenMeteoData:
    """Runtime data for one config entry."""

    forecast: OpenMeteoForecastCoordinator
    air_quality: OpenMeteoAirQualityCoordinator | None = None


type OpenMeteoConfigEntry = ConfigEntry[OpenMeteoData]


def create_client(hass: HomeAssistant, entry: ConfigEntry) -> OpenMeteoClient:
    """A client for the entry's location and options."""
    return OpenMeteoClient(
        entry.data[CONF_LATITUDE],
        entry.data[CONF_LONGITUDE],
        session=async_get_clientsession(hass),
        model=entry.options.get(CONF_MODEL, DEFAULT_MODEL),
        forecast_days=int(entry.options.get(CONF_FORECAST_DAYS, DEFAULT_FORECAST_DAYS)),
    )


class OpenMeteoForecastCoordinator(DataUpdateCoordinator[Forecast]):
    """Current conditions and forecast, every 15 minutes."""

    config_entry: OpenMeteoConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: OpenMeteoClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.client = client
        self.minutely_15 = bool(entry.options.get(CONF_MINUTELY_15, DEFAULT_MINUTELY_15))

    def _stale(self, err: OpenMeteoError) -> Forecast | None:
        """Keep showing the last forecast for a while if one update fails."""
        if self.data is None or dt_util.utcnow() - self.data.fetched_at > FORECAST_MAX_STALE:
            return None
        _LOGGER.warning(
            "Open-Meteo update failed, keeping the forecast from %s: %s",
            dt_util.as_local(self.data.fetched_at).strftime("%H:%M"),
            err,
        )
        return self.data

    async def _async_update_data(self) -> Forecast:
        try:
            return await self.client.get_forecast(minutely_15=self.minutely_15)
        except OpenMeteoRateLimitError as err:
            if (stale := self._stale(err)) is not None:
                return stale
            raise UpdateFailed(
                f"Open-Meteo rate limit reached: {err}", retry_after=err.retry_after
            ) from err
        except OpenMeteoError as err:
            if (stale := self._stale(err)) is not None:
                return stale
            raise UpdateFailed(f"Error fetching Open-Meteo forecast: {err}") from err


class OpenMeteoAirQualityCoordinator(DataUpdateCoordinator[AirQuality]):
    """Air quality and pollen, every hour. Optional: failures never affect the forecast."""

    config_entry: OpenMeteoConfigEntry

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry, client: OpenMeteoClient) -> None:
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=f"{DOMAIN}_air_quality",
            update_interval=AIR_QUALITY_UPDATE_INTERVAL,
        )
        self.client = client

    async def _async_update_data(self) -> AirQuality:
        try:
            return await self.client.get_air_quality()
        except OpenMeteoRateLimitError as err:
            raise UpdateFailed(
                f"Open-Meteo rate limit reached: {err}", retry_after=err.retry_after
            ) from err
        except OpenMeteoError as err:
            raise UpdateFailed(f"Error fetching Open-Meteo air quality: {err}") from err
