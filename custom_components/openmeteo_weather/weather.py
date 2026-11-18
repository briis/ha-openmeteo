"""Weather entity for Open-Meteo Weather."""

from __future__ import annotations

from typing import Any

from homeassistant.components.weather import (
    ATTR_FORECAST_APPARENT_TEMP,
    ATTR_FORECAST_CLOUD_COVERAGE,
    ATTR_FORECAST_CONDITION,
    ATTR_FORECAST_HUMIDITY,
    ATTR_FORECAST_NATIVE_DEW_POINT,
    ATTR_FORECAST_NATIVE_PRECIPITATION,
    ATTR_FORECAST_NATIVE_PRESSURE,
    ATTR_FORECAST_NATIVE_TEMP,
    ATTR_FORECAST_NATIVE_TEMP_LOW,
    ATTR_FORECAST_NATIVE_WIND_GUST_SPEED,
    ATTR_FORECAST_NATIVE_WIND_SPEED,
    ATTR_FORECAST_PRECIPITATION_PROBABILITY,
    ATTR_FORECAST_TIME,
    ATTR_FORECAST_UV_INDEX,
    ATTR_FORECAST_WIND_BEARING,
    Forecast,
    SingleCoordinatorWeatherEntity,
    WeatherEntityFeature,
)
from homeassistant.const import (
    UnitOfLength,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.util import dt as dt_util

from aioopenmeteo import DataPoint

from .coordinator import OpenMeteoConfigEntry, OpenMeteoForecastCoordinator
from .entity import OpenMeteoEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OpenMeteoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    async_add_entities([OpenMeteoWeather(entry.runtime_data.forecast)])


def _num(value: Any) -> float | None:
    return value if isinstance(value, int | float) else None


class OpenMeteoWeather(
    OpenMeteoEntity, SingleCoordinatorWeatherEntity[OpenMeteoForecastCoordinator]
):
    """Current conditions and daily/hourly forecast."""

    _attr_name = None  # the device name
    _attr_native_temperature_unit = UnitOfTemperature.CELSIUS
    _attr_native_pressure_unit = UnitOfPressure.HPA
    _attr_native_wind_speed_unit = UnitOfSpeed.KILOMETERS_PER_HOUR
    _attr_native_precipitation_unit = UnitOfPrecipitationDepth.MILLIMETERS
    _attr_native_visibility_unit = UnitOfLength.KILOMETERS
    _attr_supported_features = (
        WeatherEntityFeature.FORECAST_DAILY | WeatherEntityFeature.FORECAST_HOURLY
    )

    def __init__(self, coordinator: OpenMeteoForecastCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = coordinator.config_entry.entry_id

    @property
    def _now(self) -> DataPoint | None:
        return self.coordinator.data.current if self.coordinator.data else None

    def _current(self, key: str) -> float | None:
        now = self._now
        return _num(now.get(key)) if now else None

    @property
    def condition(self) -> str | None:
        return self._now.condition if self._now else None

    @property
    def native_temperature(self) -> float | None:
        return self._current("temperature_2m")

    @property
    def native_apparent_temperature(self) -> float | None:
        return self._current("apparent_temperature")

    @property
    def native_dew_point(self) -> float | None:
        return self._current("dew_point_2m")

    @property
    def humidity(self) -> float | None:
        return self._current("relative_humidity_2m")

    @property
    def native_pressure(self) -> float | None:
        return self._current("pressure_msl")

    @property
    def native_wind_speed(self) -> float | None:
        return self._current("wind_speed_10m")

    @property
    def native_wind_gust_speed(self) -> float | None:
        return self._current("wind_gusts_10m")

    @property
    def wind_bearing(self) -> float | None:
        return self._current("wind_direction_10m")

    @property
    def cloud_coverage(self) -> float | None:
        return self._current("cloud_cover")

    @property
    def uv_index(self) -> float | None:
        return self._current("uv_index")

    @property
    def native_visibility(self) -> float | None:
        meters = self._current("visibility")
        return None if meters is None else round(meters / 1000, 1)

    @callback
    def _async_forecast_daily(self) -> list[Forecast] | None:
        data = self.coordinator.data
        if data is None:
            return None
        today = dt_util.now().date()
        forecast: list[Forecast] = []
        for day in data.daily:
            if day.date < today:
                continue
            v = day.values
            forecast.append(
                {
                    ATTR_FORECAST_TIME: day.start.isoformat(),
                    ATTR_FORECAST_CONDITION: day.condition,
                    ATTR_FORECAST_NATIVE_TEMP: _num(v.get("temperature_2m_max")),
                    ATTR_FORECAST_NATIVE_TEMP_LOW: _num(v.get("temperature_2m_min")),
                    ATTR_FORECAST_APPARENT_TEMP: _num(v.get("apparent_temperature_max")),
                    ATTR_FORECAST_NATIVE_DEW_POINT: _num(v.get("dew_point_2m_mean")),
                    ATTR_FORECAST_HUMIDITY: _num(v.get("relative_humidity_2m_mean")),
                    ATTR_FORECAST_NATIVE_PRESSURE: _num(v.get("pressure_msl_mean")),
                    ATTR_FORECAST_CLOUD_COVERAGE: _num(v.get("cloud_cover_mean")),
                    ATTR_FORECAST_NATIVE_PRECIPITATION: _num(v.get("precipitation_sum")),
                    ATTR_FORECAST_PRECIPITATION_PROBABILITY: _num(
                        v.get("precipitation_probability_max")
                    ),
                    ATTR_FORECAST_NATIVE_WIND_SPEED: _num(v.get("wind_speed_10m_max")),
                    ATTR_FORECAST_NATIVE_WIND_GUST_SPEED: _num(v.get("wind_gusts_10m_max")),
                    ATTR_FORECAST_WIND_BEARING: _num(v.get("wind_direction_10m_dominant")),
                    ATTR_FORECAST_UV_INDEX: _num(v.get("uv_index_max")),
                }
            )
        return forecast

    @callback
    def _async_forecast_hourly(self) -> list[Forecast] | None:
        data = self.coordinator.data
        if data is None:
            return None
        forecast: list[Forecast] = []
        for hour in data.hourly_from(dt_util.utcnow()):
            v = hour.values
            item: Forecast = {
                ATTR_FORECAST_TIME: hour.time.isoformat(),
                ATTR_FORECAST_CONDITION: hour.condition,
                ATTR_FORECAST_NATIVE_TEMP: _num(v.get("temperature_2m")),
                ATTR_FORECAST_APPARENT_TEMP: _num(v.get("apparent_temperature")),
                ATTR_FORECAST_NATIVE_DEW_POINT: _num(v.get("dew_point_2m")),
                ATTR_FORECAST_HUMIDITY: _num(v.get("relative_humidity_2m")),
                ATTR_FORECAST_NATIVE_PRESSURE: _num(v.get("pressure_msl")),
                ATTR_FORECAST_CLOUD_COVERAGE: _num(v.get("cloud_cover")),
                ATTR_FORECAST_NATIVE_PRECIPITATION: _num(v.get("precipitation")),
                ATTR_FORECAST_PRECIPITATION_PROBABILITY: _num(v.get("precipitation_probability")),
                ATTR_FORECAST_NATIVE_WIND_SPEED: _num(v.get("wind_speed_10m")),
                ATTR_FORECAST_NATIVE_WIND_GUST_SPEED: _num(v.get("wind_gusts_10m")),
                ATTR_FORECAST_WIND_BEARING: _num(v.get("wind_direction_10m")),
                ATTR_FORECAST_UV_INDEX: _num(v.get("uv_index")),
            }
            forecast.append(item)
        return forecast
