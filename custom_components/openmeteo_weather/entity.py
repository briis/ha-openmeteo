"""Base entity for Open-Meteo Weather."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from aioopenmeteo import ATTRIBUTION, get_model

from .const import CONF_MODEL, DEFAULT_MODEL, DOMAIN, MANUFACTURER
from .coordinator import OpenMeteoAirQualityCoordinator, OpenMeteoForecastCoordinator


def device_info(coordinator: OpenMeteoForecastCoordinator | OpenMeteoAirQualityCoordinator):
    """One device per config entry; the model name shows which model is used."""
    entry = coordinator.config_entry
    model = get_model(entry.options.get(CONF_MODEL, DEFAULT_MODEL))
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=entry.title,
        manufacturer=MANUFACTURER,
        model=model.name,
        entry_type=DeviceEntryType.SERVICE,
        configuration_url="https://open-meteo.com/",
    )


class OpenMeteoEntity(CoordinatorEntity[OpenMeteoForecastCoordinator]):
    """Common device info and attribution (Open-Meteo data is CC BY 4.0)."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True

    def __init__(self, coordinator: OpenMeteoForecastCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_device_info = device_info(coordinator)
