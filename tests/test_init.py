"""Tests for Open-Meteo Weather setup, config flow, entities and options."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_LATITUDE, CONF_LOCATION, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from aioopenmeteo import OpenMeteoConnectionError, OpenMeteoInvalidLocationError
from custom_components.openmeteo_weather.const import (
    CONF_AIR_QUALITY,
    CONF_FORECAST_DAYS,
    CONF_MINUTELY_15,
    CONF_MODEL,
    DOMAIN,
)

OPTIONS = {
    CONF_MODEL: "dmi_seamless",
    CONF_AIR_QUALITY: True,
    CONF_FORECAST_DAYS: 7,
    CONF_MINUTELY_15: True,
}


def make_entry(**options) -> MockConfigEntry:
    return MockConfigEntry(
        domain=DOMAIN,
        title="Home",
        data={CONF_LATITUDE: 55.64, CONF_LONGITUDE: 12.08},
        options=OPTIONS | options,
        unique_id="55.64_12.08_dmi_seamless",
    )


async def setup(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()


def sensor_keys(hass: HomeAssistant, entry: MockConfigEntry) -> set[str]:
    registry = er.async_get(hass)
    prefix = f"{entry.entry_id}_"
    return {
        e.unique_id.removeprefix(prefix)
        for e in er.async_entries_for_config_entry(registry, entry.entry_id)
        if e.domain == "sensor"
    }


async def test_config_flow_defaults(hass: HomeAssistant, mock_client) -> None:
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] is FlowResultType.FORM
    schema = result["data_schema"].schema
    defaults = {str(k): k.default() for k in schema if callable(getattr(k, "default", None))}
    assert defaults[CONF_MODEL] == "best_match"
    assert defaults[CONF_AIR_QUALITY] is True

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: "Home",
            CONF_LOCATION: {CONF_LATITUDE: 55.6402, CONF_LONGITUDE: 12.0824},
            CONF_MODEL: "best_match",
            CONF_AIR_QUALITY: True,
            CONF_FORECAST_DAYS: 7,
            CONF_MINUTELY_15: True,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {CONF_LATITUDE: 55.6402, CONF_LONGITUDE: 12.0824}
    assert result["options"][CONF_MODEL] == "best_match"
    assert result["result"].unique_id == "55.6402_12.0824_best_match"


async def test_config_flow_model_not_available(hass: HomeAssistant, mock_client) -> None:
    with patch("custom_components.openmeteo_weather.config_flow.OpenMeteoClient") as cls:
        cls.return_value.get_forecast = AsyncMock(
            side_effect=OpenMeteoInvalidLocationError(400, "No data is available")
        )
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_NAME: "Home",
                CONF_LOCATION: {CONF_LATITUDE: 55.64, CONF_LONGITUDE: 12.08},
                CONF_MODEL: "jma_msm",
                CONF_AIR_QUALITY: True,
                CONF_FORECAST_DAYS: 7,
                CONF_MINUTELY_15: True,
            },
        )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {CONF_MODEL: "model_not_available"}


async def test_setup_creates_entities(hass: HomeAssistant, mock_client) -> None:
    entry = make_entry()
    await setup(hass, entry)
    assert entry.state is ConfigEntryState.LOADED

    weather = hass.states.get("weather.home")
    assert weather is not None
    assert weather.state == "rainy"
    assert weather.attributes["temperature"] == 6.9
    assert weather.attributes["attribution"] == "Weather data by Open-Meteo.com"

    keys = sensor_keys(hass, entry)
    # model has no UV index -> no UV sensors
    assert "uv_index" not in keys
    assert "today_uv_index_max" not in keys
    assert "lightning_potential_next_hour" not in keys
    assert {"temperature_2m", "precipitation_next_hour", "today_sunrise", "aq_birch_pollen"} <= keys
    assert "aq_olive_pollen" not in keys

    assert hass.states.get("sensor.home_temperature").state == "6.9"
    assert hass.states.get("sensor.home_weather").state == "rain_moderate"
    assert hass.states.get("sensor.home_precipitation_next_hour").state == "2.0"
    assert hass.states.get("sensor.home_european_aqi").state == "22"
    # disabled by default, but registered
    registry = er.async_get(hass)
    soil = registry.async_get_entity_id(
        "sensor", DOMAIN, f"{entry.entry_id}_soil_moisture_0_to_1cm"
    )
    assert registry.async_get(soil).disabled_by is not None


async def test_forecasts(hass: HomeAssistant, mock_client) -> None:
    await setup(hass, make_entry())
    for kind, minimum in (("daily", 6), ("hourly", 100)):
        result = await hass.services.async_call(
            "weather",
            "get_forecasts",
            {"entity_id": "weather.home", "type": kind},
            blocking=True,
            return_response=True,
        )
        items = result["weather.home"]["forecast"]
        assert len(items) >= minimum
        assert items[0]["temperature"] is not None
        assert items[0]["condition"] is not None


async def test_air_quality_off(hass: HomeAssistant, mock_client) -> None:
    entry = make_entry()
    await setup(hass, entry)
    assert "aq_european_aqi" in sensor_keys(hass, entry)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], OPTIONS | {CONF_AIR_QUALITY: False}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.runtime_data.air_quality is None
    assert not any(k.startswith("aq_") for k in sensor_keys(hass, entry))


async def test_air_quality_failure_does_not_block(hass: HomeAssistant, mock_client) -> None:
    mock_client.get_air_quality.side_effect = OpenMeteoConnectionError("offline")
    entry = make_entry()
    await setup(hass, entry)
    assert entry.state is ConfigEntryState.LOADED
    assert hass.states.get("weather.home") is not None
    assert not any(k.startswith("aq_") for k in sensor_keys(hass, entry))

    # It comes back: the sensors are added then.
    mock_client.get_air_quality.side_effect = None
    await entry.runtime_data.air_quality.async_refresh()
    await hass.async_block_till_done()
    assert "aq_european_aqi" in sensor_keys(hass, entry)


async def test_change_model_updates_unique_id(hass: HomeAssistant, mock_client) -> None:
    entry = make_entry()
    await setup(hass, entry)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], OPTIONS | {CONF_MODEL: "ecmwf_ifs025"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert entry.unique_id == "55.64_12.08_ecmwf_ifs025"
    assert entry.options[CONF_MODEL] == "ecmwf_ifs025"


async def test_forecast_failure_retries_setup(hass: HomeAssistant, mock_client) -> None:
    mock_client.get_forecast.side_effect = OpenMeteoConnectionError("offline")
    entry = make_entry()
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    assert entry.state is ConfigEntryState.SETUP_RETRY
