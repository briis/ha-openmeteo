"""Constants for the Open-Meteo Weather integration."""

from __future__ import annotations

from datetime import timedelta
from typing import Final

DOMAIN: Final = "openmeteo_weather"
DEFAULT_NAME: Final = "Open-Meteo"
MANUFACTURER: Final = "Open-Meteo"

CONF_MODEL: Final = "model"
CONF_FORECAST_DAYS: Final = "forecast_days"
CONF_MINUTELY_15: Final = "minutely_15"
CONF_AIR_QUALITY: Final = "air_quality"

DEFAULT_MODEL: Final = "best_match"
DEFAULT_FORECAST_DAYS: Final = 7
DEFAULT_MINUTELY_15: Final = True
DEFAULT_AIR_QUALITY: Final = True

# Current values are 15-minute values, so polling faster gives nothing new.
UPDATE_INTERVAL: Final = timedelta(minutes=15)
# Air quality (CAMS) is hourly.
AIR_QUALITY_UPDATE_INTERVAL: Final = timedelta(hours=1)
# How long the last good forecast is shown when updates fail.
FORECAST_MAX_STALE: Final = timedelta(hours=3)
