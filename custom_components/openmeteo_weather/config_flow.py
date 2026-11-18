"""Config flow for Open-Meteo Weather."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_LATITUDE, CONF_LOCATION, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import voluptuous as vol

from aioopenmeteo import (
    MAX_FORECAST_DAYS,
    MODELS,
    OpenMeteoClient,
    OpenMeteoConnectionError,
    OpenMeteoError,
    OpenMeteoInvalidLocationError,
    OpenMeteoRateLimitError,
)

from .const import (
    CONF_AIR_QUALITY,
    CONF_FORECAST_DAYS,
    CONF_MINUTELY_15,
    CONF_MODEL,
    DEFAULT_AIR_QUALITY,
    DEFAULT_FORECAST_DAYS,
    DEFAULT_MINUTELY_15,
    DEFAULT_MODEL,
    DEFAULT_NAME,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

MODEL_SELECTOR = selector.SelectSelector(
    selector.SelectSelectorConfig(
        options=[selector.SelectOptionDict(value=m.id, label=m.name) for m in MODELS],
        mode=selector.SelectSelectorMode.DROPDOWN,
        custom_value=True,  # lets a model Open-Meteo adds later be typed in
    )
)


def _settings_schema() -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_MODEL, default=DEFAULT_MODEL): MODEL_SELECTOR,
            vol.Required(CONF_AIR_QUALITY, default=DEFAULT_AIR_QUALITY): (
                selector.BooleanSelector()
            ),
            vol.Required(CONF_FORECAST_DAYS, default=DEFAULT_FORECAST_DAYS): (
                selector.NumberSelector(
                    selector.NumberSelectorConfig(
                        min=1,
                        max=MAX_FORECAST_DAYS,
                        step=1,
                        mode=selector.NumberSelectorMode.BOX,
                    )
                )
            ),
            vol.Required(CONF_MINUTELY_15, default=DEFAULT_MINUTELY_15): (
                selector.BooleanSelector()
            ),
        }
    )


def _options(user_input: dict[str, Any]) -> dict[str, Any]:
    return {
        CONF_MODEL: (user_input.get(CONF_MODEL) or DEFAULT_MODEL).strip(),
        CONF_AIR_QUALITY: bool(user_input.get(CONF_AIR_QUALITY, DEFAULT_AIR_QUALITY)),
        CONF_FORECAST_DAYS: int(user_input.get(CONF_FORECAST_DAYS, DEFAULT_FORECAST_DAYS)),
        CONF_MINUTELY_15: bool(user_input.get(CONF_MINUTELY_15, DEFAULT_MINUTELY_15)),
    }


async def _validate(
    hass: HomeAssistant, latitude: float, longitude: float, model: str
) -> dict[str, str]:
    """Fetch once to check the model covers the location; returns form errors."""
    client = OpenMeteoClient(
        latitude,
        longitude,
        session=async_get_clientsession(hass),
        model=model,
        forecast_days=1,
    )
    try:
        await client.get_forecast(minutely_15=False)
    except OpenMeteoInvalidLocationError:
        return {CONF_MODEL: "model_not_available"}
    except OpenMeteoRateLimitError:
        return {"base": "rate_limited"}
    except OpenMeteoConnectionError:
        return {"base": "cannot_connect"}
    except OpenMeteoError as err:
        _LOGGER.warning("Unexpected answer from Open-Meteo: %s", err)
        return {"base": "unknown"}
    return {}


def _unique_id(latitude: float, longitude: float, model: str) -> str:
    return f"{latitude}_{longitude}_{model}"


class OpenMeteoConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Open-Meteo Weather."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OpenMeteoOptionsFlow:
        return OpenMeteoOptionsFlow()

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        """Name, location, model and optional data in one step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            latitude = round(user_input[CONF_LOCATION][CONF_LATITUDE], 4)
            longitude = round(user_input[CONF_LOCATION][CONF_LONGITUDE], 4)
            options = _options(user_input)
            # One entry per location and model, so models can be compared side by side.
            await self.async_set_unique_id(_unique_id(latitude, longitude, options[CONF_MODEL]))
            self._abort_if_unique_id_configured()
            errors = await _validate(self.hass, latitude, longitude, options[CONF_MODEL])
            if not errors:
                return self.async_create_entry(
                    title=user_input[CONF_NAME],
                    data={CONF_LATITUDE: latitude, CONF_LONGITUDE: longitude},
                    options=options,
                )

        defaults = user_input or {
            CONF_NAME: DEFAULT_NAME,
            CONF_LOCATION: {
                CONF_LATITUDE: self.hass.config.latitude,
                CONF_LONGITUDE: self.hass.config.longitude,
            },
        }
        schema = vol.Schema(
            {
                vol.Required(CONF_NAME): str,
                vol.Required(CONF_LOCATION): selector.LocationSelector(
                    selector.LocationSelectorConfig(radius=False)
                ),
            }
        ).extend(_settings_schema().schema)
        return self.async_show_form(
            step_id="user",
            data_schema=self.add_suggested_values_to_schema(schema, defaults),
            errors=errors,
        )


class OpenMeteoOptionsFlow(OptionsFlowWithReload):
    """Change model, air quality, forecast length and 15-minute data."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self.config_entry
        if user_input is not None:
            options = _options(user_input)
            latitude = entry.data[CONF_LATITUDE]
            longitude = entry.data[CONF_LONGITUDE]
            if options[CONF_MODEL] != entry.options.get(CONF_MODEL, DEFAULT_MODEL):
                unique_id = _unique_id(latitude, longitude, options[CONF_MODEL])
                if any(
                    e.unique_id == unique_id and e.entry_id != entry.entry_id
                    for e in self.hass.config_entries.async_entries(DOMAIN)
                ):
                    errors[CONF_MODEL] = "model_already_configured"
                else:
                    errors = await _validate(self.hass, latitude, longitude, options[CONF_MODEL])
                if not errors:
                    self.hass.config_entries.async_update_entry(entry, unique_id=unique_id)
            if not errors:
                return self.async_create_entry(data=options)

        current = user_input or {
            CONF_MODEL: entry.options.get(CONF_MODEL, DEFAULT_MODEL),
            CONF_AIR_QUALITY: entry.options.get(CONF_AIR_QUALITY, DEFAULT_AIR_QUALITY),
            CONF_FORECAST_DAYS: entry.options.get(CONF_FORECAST_DAYS, DEFAULT_FORECAST_DAYS),
            CONF_MINUTELY_15: entry.options.get(CONF_MINUTELY_15, DEFAULT_MINUTELY_15),
        }
        return self.async_show_form(
            step_id="init",
            data_schema=self.add_suggested_values_to_schema(_settings_schema(), current),
            errors=errors,
        )
