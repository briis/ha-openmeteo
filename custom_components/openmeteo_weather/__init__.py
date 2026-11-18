"""The Open-Meteo Weather integration."""

from __future__ import annotations

from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from .const import CONF_AIR_QUALITY, DEFAULT_AIR_QUALITY
from .coordinator import (
    OpenMeteoAirQualityCoordinator,
    OpenMeteoConfigEntry,
    OpenMeteoData,
    OpenMeteoForecastCoordinator,
    create_client,
)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.WEATHER]


async def async_setup_entry(hass: HomeAssistant, entry: OpenMeteoConfigEntry) -> bool:
    """Set up Open-Meteo Weather from a config entry."""
    client = create_client(hass, entry)
    forecast = OpenMeteoForecastCoordinator(hass, entry, client)
    await forecast.async_config_entry_first_refresh()
    data = OpenMeteoData(forecast=forecast)
    # Air quality is optional (default on). A failure there must not stop the
    # forecast, so it gets a plain refresh instead of first_refresh.
    if entry.options.get(CONF_AIR_QUALITY, DEFAULT_AIR_QUALITY):
        data.air_quality = OpenMeteoAirQualityCoordinator(hass, entry, client)
        await data.air_quality.async_refresh()
    entry.runtime_data = data
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: OpenMeteoConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
