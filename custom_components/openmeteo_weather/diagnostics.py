"""Diagnostics for Open-Meteo Weather."""

from __future__ import annotations

from typing import Any

from homeassistant.components.diagnostics import async_redact_data
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE
from homeassistant.core import HomeAssistant

from .coordinator import OpenMeteoConfigEntry

TO_REDACT = {CONF_LATITUDE, CONF_LONGITUDE, "latitude", "longitude"}


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: OpenMeteoConfigEntry
) -> dict[str, Any]:
    """What the integration received, without the location."""
    runtime = entry.runtime_data
    forecast = runtime.forecast.data
    air = runtime.air_quality.data if runtime.air_quality else None
    return {
        "entry": {
            "data": async_redact_data(dict(entry.data), TO_REDACT),
            "options": dict(entry.options),
        },
        "forecast": None
        if forecast is None
        else {
            "model": forecast.model,
            "timezone": forecast.timezone,
            "elevation": forecast.elevation,
            "fetched_at": forecast.fetched_at.isoformat(),
            "current": dict(forecast.current.values) if forecast.current else None,
            "available_current": sorted(forecast.available("current")),
            "available_daily": sorted(forecast.available("daily")),
            "available_minutely_15": sorted(forecast.available("minutely_15")),
            "hours": len(forecast.hourly),
            "days": len(forecast.daily),
            "quarters": len(forecast.minutely_15),
        },
        "air_quality": None
        if air is None
        else {
            "fetched_at": air.fetched_at.isoformat(),
            "current": dict(air.current.values) if air.current else None,
        },
    }
