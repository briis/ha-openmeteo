"""Sensors for Open-Meteo Weather.

Sensors are only created for values the selected model actually provides, e.g. the
DMI models have no UV index and the ECMWF models no visibility.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Literal

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    DEGREE,
    PERCENTAGE,
    UV_INDEX,
    Platform,
    UnitOfIrradiance,
    UnitOfLength,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from aioopenmeteo import WMO_KEYS, AirQuality, Forecast

try:  # Home Assistant 2026.x moved these into unit enums (old names removed in 2027.8)
    from homeassistant.const import UnitOfDensity, UnitOfRatio

    MICROGRAMS_PER_CUBIC_METER: str = UnitOfDensity.MICROGRAMS_PER_CUBIC_METER
    PARTS_PER_MILLION: str = UnitOfRatio.PARTS_PER_MILLION
except ImportError:  # older Home Assistant
    from homeassistant.const import (
        CONCENTRATION_MICROGRAMS_PER_CUBIC_METER as MICROGRAMS_PER_CUBIC_METER,
        CONCENTRATION_PARTS_PER_MILLION as PARTS_PER_MILLION,
    )

from .const import CONF_MINUTELY_15, DEFAULT_MINUTELY_15
from .coordinator import (
    OpenMeteoAirQualityCoordinator,
    OpenMeteoConfigEntry,
    OpenMeteoForecastCoordinator,
)
from .entity import OpenMeteoEntity, device_info

Source = Literal["current", "today", "minutely_15", "air_quality"]

MOON_PHASES = [
    "new_moon",
    "waxing_crescent",
    "first_quarter",
    "waxing_gibbous",
    "full_moon",
    "waning_gibbous",
    "last_quarter",
    "waning_crescent",
]
POLLEN_UNIT = "grains/m³"


@dataclass(frozen=True, kw_only=True)
class OpenMeteoSensorDescription(SensorEntityDescription):
    """A sensor fed by one Open-Meteo variable.

    `variable` is the API variable the sensor needs (to decide whether to create it);
    `value_fn` gets the data and "now" and returns the state.
    """

    source: Source
    variable: str
    value_fn: Callable[[Any, datetime], Any] | None = None


def _num(value: Any) -> float | None:
    return value if isinstance(value, int | float) else None


def _current(
    key: str,
    *,
    enabled: bool = False,
    scale: float = 1.0,
    **kwargs: Any,
) -> OpenMeteoSensorDescription:
    def value(fc: Forecast, _now: datetime) -> float | None:
        if fc.current is None or (v := _num(fc.current.get(key))) is None:
            return None
        return v * scale if scale != 1.0 else v

    kwargs.setdefault("translation_key", key)
    kwargs.setdefault("state_class", SensorStateClass.MEASUREMENT)
    return OpenMeteoSensorDescription(
        key=key,
        source="current",
        variable=key,
        value_fn=value,
        entity_registry_enabled_default=enabled,
        **kwargs,
    )


def _today(key: str, *, enabled: bool = False, **kwargs: Any) -> OpenMeteoSensorDescription:
    def value(fc: Forecast, now: datetime) -> Any:
        day = fc.today(now)
        return None if day is None else day.get(key)

    kwargs.setdefault("translation_key", f"today_{key}")
    return OpenMeteoSensorDescription(
        key=f"today_{key}",
        source="today",
        variable=key,
        value_fn=value,
        entity_registry_enabled_default=enabled,
        **kwargs,
    )


def _air(key: str, *, enabled: bool = False, **kwargs: Any) -> OpenMeteoSensorDescription:
    def value(aq: AirQuality, _now: datetime) -> float | None:
        return None if aq.current is None else _num(aq.current.get(key))

    kwargs.setdefault("translation_key", key)
    kwargs.setdefault("state_class", SensorStateClass.MEASUREMENT)
    return OpenMeteoSensorDescription(
        key=f"aq_{key}",
        source="air_quality",
        variable=key,
        value_fn=value,
        entity_registry_enabled_default=enabled,
        **kwargs,
    )


def _next_hour(fc: Forecast, now: datetime, key: str) -> list[float]:
    """Values for the next hour. A 15-minute value covers the 15 minutes before its
    time stamp, so the next hour is the four values stamped after now."""
    end = now + timedelta(hours=1)
    return [
        v for q in fc.minutely_15 if now < q.time <= end and (v := _num(q.get(key))) is not None
    ]


def _sum_next_hour(fc: Forecast, now: datetime) -> float | None:
    values = _next_hour(fc, now, "precipitation")
    return round(sum(values), 2) if values else None


def _max_next_hour(key: str) -> Callable[[Forecast, datetime], float | None]:
    def value(fc: Forecast, now: datetime) -> float | None:
        values = _next_hour(fc, now, key)
        return max(values) if values else None

    return value


TEMP = {
    "device_class": SensorDeviceClass.TEMPERATURE,
    "native_unit_of_measurement": UnitOfTemperature.CELSIUS,
    "suggested_display_precision": 1,
}
RAIN_MM = {
    "device_class": SensorDeviceClass.PRECIPITATION,
    "native_unit_of_measurement": UnitOfPrecipitationDepth.MILLIMETERS,
    "suggested_display_precision": 1,
}
SNOW_CM = {
    "device_class": SensorDeviceClass.PRECIPITATION,
    "native_unit_of_measurement": UnitOfPrecipitationDepth.CENTIMETERS,
    "suggested_display_precision": 1,
}
WIND = {
    "device_class": SensorDeviceClass.WIND_SPEED,
    "native_unit_of_measurement": UnitOfSpeed.KILOMETERS_PER_HOUR,
    "suggested_display_precision": 1,
}
BEARING = {
    "device_class": SensorDeviceClass.WIND_DIRECTION,
    "native_unit_of_measurement": DEGREE,
    "state_class": SensorStateClass.MEASUREMENT_ANGLE,
    "suggested_display_precision": 0,
}
HPA = {
    "device_class": SensorDeviceClass.ATMOSPHERIC_PRESSURE,
    "native_unit_of_measurement": UnitOfPressure.HPA,
    "suggested_display_precision": 1,
}
PCT = {"native_unit_of_measurement": PERCENTAGE, "suggested_display_precision": 0}
HEIGHT = {
    "device_class": SensorDeviceClass.DISTANCE,
    "native_unit_of_measurement": UnitOfLength.METERS,
    "suggested_display_precision": 0,
}
IRRADIANCE = {
    "device_class": SensorDeviceClass.IRRADIANCE,
    "native_unit_of_measurement": UnitOfIrradiance.WATTS_PER_SQUARE_METER,
    "suggested_display_precision": 0,
}
SOIL_MOISTURE = {
    "device_class": SensorDeviceClass.MOISTURE,
    "native_unit_of_measurement": PERCENTAGE,
    "suggested_display_precision": 1,
    "scale": 100.0,  # m³/m³ -> volumetric %
}
UGM3 = {
    "native_unit_of_measurement": MICROGRAMS_PER_CUBIC_METER,
    "suggested_display_precision": 1,
}
POLLEN = {"native_unit_of_measurement": POLLEN_UNIT, "suggested_display_precision": 0}
TIMESTAMP = {"device_class": SensorDeviceClass.TIMESTAMP}
HOURS_FROM_SECONDS = {
    "device_class": SensorDeviceClass.DURATION,
    "native_unit_of_measurement": UnitOfTime.SECONDS,
    "suggested_unit_of_measurement": UnitOfTime.HOURS,
    "suggested_display_precision": 1,
}


def _weather_key(fc: Forecast, _now: datetime) -> str | None:
    return fc.current.weather_key if fc.current else None


def _today_weather_key(fc: Forecast, now: datetime) -> str | None:
    day = fc.today(now)
    return day.weather_key if day else None


def _today_moon(fc: Forecast, now: datetime) -> str | None:
    day = fc.today(now)
    return day.moon_phase if day else None


SENSORS: tuple[OpenMeteoSensorDescription, ...] = (
    # --- current conditions -------------------------------------------------
    _current("temperature_2m", enabled=True, translation_key="temperature", **TEMP),
    _current("apparent_temperature", enabled=True, **TEMP),
    _current("dew_point_2m", enabled=True, translation_key="dew_point", **TEMP),
    _current("wet_bulb_temperature_2m", translation_key="wet_bulb_temperature", **TEMP),
    _current(
        "relative_humidity_2m",
        enabled=True,
        translation_key="humidity",
        device_class=SensorDeviceClass.HUMIDITY,
        **PCT,
    ),
    OpenMeteoSensorDescription(
        key="weather_code",
        translation_key="weather",
        source="current",
        variable="weather_code",
        device_class=SensorDeviceClass.ENUM,
        options=list(WMO_KEYS),
        value_fn=_weather_key,
    ),
    _current("precipitation", enabled=True, **RAIN_MM),
    _current("precipitation_probability", enabled=True, **PCT),
    _current("rain", **RAIN_MM),
    _current("showers", **RAIN_MM),
    _current("snowfall", **SNOW_CM),
    _current("snow_depth", **HEIGHT | {"suggested_display_precision": 2}),
    _current("cloud_cover", enabled=True, **PCT),
    _current("cloud_cover_low", **PCT),
    _current("cloud_cover_mid", **PCT),
    _current("cloud_cover_high", **PCT),
    _current("pressure_msl", enabled=True, translation_key="pressure", **HPA),
    _current("surface_pressure", **HPA),
    _current("wind_speed_10m", enabled=True, translation_key="wind_speed", **WIND),
    _current("wind_direction_10m", enabled=True, translation_key="wind_direction", **BEARING),
    _current("wind_gusts_10m", enabled=True, translation_key="wind_gusts", **WIND),
    _current("wind_speed_80m", **WIND),
    _current("wind_direction_80m", **BEARING),
    _current(
        "visibility",
        enabled=True,
        device_class=SensorDeviceClass.DISTANCE,
        native_unit_of_measurement=UnitOfLength.METERS,
        suggested_unit_of_measurement=UnitOfLength.KILOMETERS,
        suggested_display_precision=1,
    ),
    _current(
        "uv_index",
        enabled=True,
        native_unit_of_measurement=UV_INDEX,
        suggested_display_precision=1,
    ),
    _current("uv_index_clear_sky", native_unit_of_measurement=UV_INDEX),
    _current("shortwave_radiation", enabled=True, translation_key="solar_radiation", **IRRADIANCE),
    _current("direct_radiation", **IRRADIANCE),
    _current("diffuse_radiation", **IRRADIANCE),
    _current("direct_normal_irradiance", **IRRADIANCE),
    _current("terrestrial_radiation", **IRRADIANCE),
    _current(
        "sunshine_duration",
        translation_key="sunshine_duration",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.SECONDS,
        suggested_display_precision=0,
    ),
    _current("cape", native_unit_of_measurement="J/kg", suggested_display_precision=0),
    _current("lifted_index", native_unit_of_measurement="K", suggested_display_precision=1),
    _current(
        "convective_inhibition", native_unit_of_measurement="J/kg", suggested_display_precision=0
    ),
    _current("freezing_level_height", **HEIGHT),
    _current("boundary_layer_height", **HEIGHT),
    _current(
        "vapour_pressure_deficit",
        device_class=SensorDeviceClass.PRESSURE,
        native_unit_of_measurement=UnitOfPressure.KPA,
        suggested_display_precision=2,
    ),
    _current(
        "evapotranspiration",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        suggested_display_precision=2,
    ),
    _current(
        "et0_fao_evapotranspiration",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        suggested_display_precision=2,
    ),
    _current(
        "total_column_integrated_water_vapour",
        native_unit_of_measurement="kg/m²",
        suggested_display_precision=1,
    ),
    _current("soil_temperature_0cm", **TEMP),
    _current("soil_temperature_6cm", **TEMP),
    _current("soil_temperature_18cm", **TEMP),
    _current("soil_temperature_54cm", **TEMP),
    _current("soil_moisture_0_to_1cm", **SOIL_MOISTURE),
    _current("soil_moisture_1_to_3cm", **SOIL_MOISTURE),
    _current("soil_moisture_3_to_9cm", **SOIL_MOISTURE),
    _current("soil_moisture_9_to_27cm", **SOIL_MOISTURE),
    _current("soil_moisture_27_to_81cm", **SOIL_MOISTURE),
    # --- today --------------------------------------------------------------
    OpenMeteoSensorDescription(
        key="today_weather_code",
        translation_key="today_weather",
        source="today",
        variable="weather_code",
        device_class=SensorDeviceClass.ENUM,
        options=list(WMO_KEYS),
        value_fn=_today_weather_key,
    ),
    _today("temperature_2m_max", enabled=True, translation_key="today_temperature_max", **TEMP),
    _today("temperature_2m_min", enabled=True, translation_key="today_temperature_min", **TEMP),
    _today("apparent_temperature_max", **TEMP),
    _today("apparent_temperature_min", **TEMP),
    _today("precipitation_sum", enabled=True, **RAIN_MM),
    _today("rain_sum", **RAIN_MM),
    _today("showers_sum", **RAIN_MM),
    _today("snowfall_sum", **SNOW_CM),
    _today(
        "precipitation_hours",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        suggested_display_precision=0,
    ),
    _today("precipitation_probability_max", enabled=True, **PCT),
    _today("wind_speed_10m_max", **WIND),
    _today("wind_gusts_10m_max", **WIND),
    _today("wind_direction_10m_dominant", **BEARING),
    _today("uv_index_max", enabled=True, native_unit_of_measurement=UV_INDEX),
    _today("sunshine_duration", enabled=True, **HOURS_FROM_SECONDS),
    _today("daylight_duration", **HOURS_FROM_SECONDS),
    _today(
        "shortwave_radiation_sum",
        native_unit_of_measurement="MJ/m²",
        suggested_display_precision=1,
    ),
    _today(
        "et0_fao_evapotranspiration",
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        suggested_display_precision=1,
    ),
    _today("sunrise", enabled=True, translation_key="sunrise", **TIMESTAMP),
    _today("sunset", enabled=True, translation_key="sunset", **TIMESTAMP),
    _today("moonrise", translation_key="moonrise", **TIMESTAMP),
    _today("moonset", translation_key="moonset", **TIMESTAMP),
    OpenMeteoSensorDescription(
        key="today_moon_phase",
        translation_key="moon_phase",
        source="today",
        variable="moon_phase",
        device_class=SensorDeviceClass.ENUM,
        options=MOON_PHASES,
        value_fn=_today_moon,
        entity_registry_enabled_default=False,
    ),
    # --- 15-minute data -----------------------------------------------------
    OpenMeteoSensorDescription(
        key="precipitation_next_hour",
        translation_key="precipitation_next_hour",
        source="minutely_15",
        variable="precipitation",
        value_fn=_sum_next_hour,
        **RAIN_MM,
    ),
    OpenMeteoSensorDescription(
        key="wind_gusts_next_hour",
        translation_key="wind_gusts_next_hour",
        source="minutely_15",
        variable="wind_gusts_10m",
        value_fn=_max_next_hour("wind_gusts_10m"),
        entity_registry_enabled_default=False,
        **WIND,
    ),
    OpenMeteoSensorDescription(
        key="lightning_potential_next_hour",
        translation_key="lightning_potential_next_hour",
        source="minutely_15",
        variable="lightning_potential",
        value_fn=_max_next_hour("lightning_potential"),
        native_unit_of_measurement="J/kg",
        suggested_display_precision=0,
    ),
    # --- air quality --------------------------------------------------------
    _air("european_aqi", enabled=True, device_class=SensorDeviceClass.AQI),
    _air("european_aqi_pm2_5", device_class=SensorDeviceClass.AQI),
    _air("european_aqi_pm10", device_class=SensorDeviceClass.AQI),
    _air("european_aqi_nitrogen_dioxide", device_class=SensorDeviceClass.AQI),
    _air("european_aqi_ozone", device_class=SensorDeviceClass.AQI),
    _air("european_aqi_sulphur_dioxide", device_class=SensorDeviceClass.AQI),
    _air("us_aqi", device_class=SensorDeviceClass.AQI),
    _air("pm2_5", enabled=True, device_class=SensorDeviceClass.PM25, **UGM3),
    _air("pm10", enabled=True, device_class=SensorDeviceClass.PM10, **UGM3),
    _air("nitrogen_dioxide", device_class=SensorDeviceClass.NITROGEN_DIOXIDE, **UGM3),
    _air("ozone", device_class=SensorDeviceClass.OZONE, **UGM3),
    _air("sulphur_dioxide", device_class=SensorDeviceClass.SULPHUR_DIOXIDE, **UGM3),
    _air("carbon_monoxide", device_class=SensorDeviceClass.CO, **UGM3),
    _air(
        "carbon_dioxide",
        device_class=SensorDeviceClass.CO2,
        native_unit_of_measurement=PARTS_PER_MILLION,
        suggested_display_precision=0,
    ),
    _air("dust", **UGM3),
    _air("ammonia", **UGM3),
    _air("methane", **UGM3 | {"suggested_display_precision": 0}),
    _air("aerosol_optical_depth", suggested_display_precision=2),
    _air("alder_pollen", enabled=True, **POLLEN),
    _air("birch_pollen", enabled=True, **POLLEN),
    _air("grass_pollen", enabled=True, **POLLEN),
    _air("mugwort_pollen", enabled=True, **POLLEN),
    _air("olive_pollen", **POLLEN),
    _air("ragweed_pollen", **POLLEN),
)


def _available(description: OpenMeteoSensorDescription, data: Any) -> bool:
    """Does the data have this sensor's variable (for the chosen model and place)?"""
    if data is None:
        return False
    match description.source:
        case "current":
            return description.variable in data.available("current")
        case "today":
            # Any day: e.g. "moonset" is null on a day the moon does not set.
            return description.variable in data.available("daily")
        case "minutely_15":
            return description.variable in data.available("minutely_15")
        case _:
            return description.variable in data.available()


async def async_setup_entry(
    hass: HomeAssistant,
    entry: OpenMeteoConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    runtime = entry.runtime_data
    forecast = runtime.forecast
    minutely_15 = entry.options.get(CONF_MINUTELY_15, DEFAULT_MINUTELY_15)

    entities: list[SensorEntity] = [
        OpenMeteoForecastSensor(forecast, d)
        for d in SENSORS
        if d.source != "air_quality"
        and (d.source != "minutely_15" or minutely_15)
        and _available(d, forecast.data)
    ]
    keep = {e.unique_id for e in entities}

    air = runtime.air_quality
    air_added = False

    @callback
    def _add_air_quality() -> None:
        """Add air quality sensors once there is data to see which ones exist."""
        nonlocal air_added
        if air_added or air is None or air.data is None:
            return
        air_added = True
        async_add_entities(
            OpenMeteoAirQualitySensor(air, d)
            for d in SENSORS
            if d.source == "air_quality" and _available(d, air.data)
        )

    if air is not None:
        if air.data is not None:
            keep |= {
                f"{entry.entry_id}_{d.key}"
                for d in SENSORS
                if d.source == "air_quality" and _available(d, air.data)
            }
        else:
            # Air quality failed at startup: keep its old entities, add them later.
            keep |= _registered(hass, entry, prefix=f"{entry.entry_id}_aq_")
            entry.async_on_unload(air.async_add_listener(_add_air_quality))

    _remove_stale(hass, entry, keep)
    async_add_entities(entities)
    _add_air_quality()


def _registered(hass: HomeAssistant, entry: OpenMeteoConfigEntry, prefix: str) -> set[str]:
    registry = er.async_get(hass)
    return {
        e.unique_id
        for e in er.async_entries_for_config_entry(registry, entry.entry_id)
        if e.domain == Platform.SENSOR and e.unique_id.startswith(prefix)
    }


def _remove_stale(hass: HomeAssistant, entry: OpenMeteoConfigEntry, keep: set[str]) -> None:
    """Remove sensors the current model/options no longer provide.

    E.g. after switching to a model without UV index, or turning off air quality.
    """
    registry = er.async_get(hass)
    for entity in er.async_entries_for_config_entry(registry, entry.entry_id):
        if entity.domain == Platform.SENSOR and entity.unique_id not in keep:
            registry.async_remove(entity.entity_id)


class OpenMeteoForecastSensor(OpenMeteoEntity, SensorEntity):
    """A sensor from the forecast coordinator."""

    entity_description: OpenMeteoSensorDescription

    def __init__(
        self,
        coordinator: OpenMeteoForecastCoordinator,
        description: OpenMeteoSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data
        if data is None or self.entity_description.value_fn is None:
            return None
        return self.entity_description.value_fn(data, dt_util.utcnow())


class OpenMeteoAirQualitySensor(CoordinatorEntity[OpenMeteoAirQualityCoordinator], SensorEntity):
    """A sensor from the air quality coordinator."""

    _attr_has_entity_name = True
    entity_description: OpenMeteoSensorDescription

    def __init__(
        self,
        coordinator: OpenMeteoAirQualityCoordinator,
        description: OpenMeteoSensorDescription,
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{description.key}"
        self._attr_device_info = device_info(coordinator)
        self._attr_attribution = "Air quality data by Open-Meteo.com (CAMS)"

    @property
    def native_value(self) -> Any:
        data = self.coordinator.data
        if data is None or self.entity_description.value_fn is None:
            return None
        return self.entity_description.value_fn(data, dt_util.utcnow())
