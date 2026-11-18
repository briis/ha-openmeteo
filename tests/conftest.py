"""Fixtures for Open-Meteo Weather tests."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from aioopenmeteo import (
    AIR_QUALITY_CURRENT_VARIABLES,
    CURRENT_VARIABLES,
    DAILY_VARIABLES,
    HOURLY_VARIABLES,
    MINUTELY_15_VARIABLES,
    parse_air_quality,
    parse_forecast,
)

# Variables the test "model" does not have (like DMI: no UV index).
MISSING = {
    "uv_index",
    "uv_index_clear_sky",
    "uv_index_max",
    "uv_index_clear_sky_max",
    "lifted_index",
    "evapotranspiration",
    "lightning_potential",
}
SAMPLE = {
    "temperature_2m": 6.9,
    "relative_humidity_2m": 94,
    "dew_point_2m": 6.0,
    "apparent_temperature": 4.4,
    "is_day": 1,
    "weather_code": 63,
    "pressure_msl": 974.3,
    "wind_speed_10m": 10.8,
    "wind_direction_10m": 135,
    "wind_gusts_10m": 40.0,
    "visibility": 3200,
    "cloud_cover": 100,
    "soil_moisture_0_to_1cm": 0.437,
}


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Allow loading custom_components/ in tests."""
    yield


def _value(name: str, i: int = 0) -> Any:
    if name in MISSING:
        return None
    return SAMPLE.get(name, 1.0 + i % 3)


def forecast_payload() -> dict[str, Any]:
    now = datetime.now(UTC).replace(second=0, microsecond=0)
    now = now - timedelta(minutes=now.minute % 15)
    day0 = int(now.replace(hour=0, minute=0).timestamp()) - 3600  # local midnight, UTC+1
    if day0 + 86400 <= now.timestamp():
        day0 += 86400
    elif day0 > now.timestamp():
        day0 -= 86400
    days, hours = 7, 7 * 24
    hourly = {"time": [day0 + 3600 * i for i in range(hours)]}
    hourly |= {n: [_value(n, i) for i in range(hours)] for n in HOURLY_VARIABLES}
    daily: dict[str, list] = {"time": [day0 + 86400 * d for d in range(days)]}
    for n in DAILY_VARIABLES:
        if n in ("sunrise", "sunset", "moonrise", "moonset"):
            offset = {"sunrise": 28000, "sunset": 57000, "moonrise": 49000, "moonset": 70000}
            daily[n] = [day0 + 86400 * d + offset[n] for d in range(days)]
        elif n == "moon_phase":
            daily[n] = [0.5] * days
        else:
            daily[n] = [_value(n, d) for d in range(days)]
    quarters = {"time": [int(now.timestamp()) + 900 * i for i in range(8)]}
    quarters |= {n: [None if n in MISSING else 0.5] * 8 for n in MINUTELY_15_VARIABLES}
    return {
        "latitude": 55.64,
        "longitude": 12.08,
        "utc_offset_seconds": 3600,
        "timezone": "Europe/Copenhagen",
        "elevation": 45.0,
        "current": {"time": int(now.timestamp()), "interval": 900}
        | {n: _value(n) for n in CURRENT_VARIABLES},
        "hourly": hourly,
        "daily": daily,
        "minutely_15": quarters,
    }


def air_quality_payload() -> dict[str, Any]:
    now = int(datetime.now(UTC).replace(minute=0, second=0, microsecond=0).timestamp())
    current = {"time": now, "interval": 3600}
    current |= {n: 5.0 for n in AIR_QUALITY_CURRENT_VARIABLES}
    current["olive_pollen"] = None  # e.g. outside the European pollen domain
    current["european_aqi"] = 22
    return {"latitude": 55.6, "longitude": 12.1, "utc_offset_seconds": 3600, "current": current}


@pytest.fixture
def forecast():
    return parse_forecast(forecast_payload(), "dmi_seamless")


@pytest.fixture
def air_quality():
    return parse_air_quality(air_quality_payload())


@pytest.fixture
def mock_client(forecast, air_quality) -> Generator[AsyncMock]:
    """Patch the aioopenmeteo client everywhere the integration uses it."""
    with (
        patch("custom_components.openmeteo_weather.coordinator.OpenMeteoClient") as coord_cls,
        patch("custom_components.openmeteo_weather.config_flow.OpenMeteoClient") as flow_cls,
    ):
        for cls in (coord_cls, flow_cls):
            cls.return_value.get_forecast = AsyncMock(return_value=forecast)
            cls.return_value.get_air_quality = AsyncMock(return_value=air_quality)
        yield coord_cls.return_value
