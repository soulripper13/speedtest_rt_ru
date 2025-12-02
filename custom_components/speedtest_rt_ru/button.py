"""Button platform for Speedtest RT.RU integration."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Speedtest RT.RU button."""
    hass_data = hass.data[DOMAIN][entry.entry_id]
    coordinator = hass_data.get("coordinator")

    if coordinator:
        async_add_entities([SpeedtestButton(coordinator, entry)])


class SpeedtestButton(CoordinatorEntity, ButtonEntity):
    """Button to manually trigger a speedtest."""

    _attr_has_entity_name = True
    _attr_name = "Run Speedtest"
    _attr_icon = "mdi:speedometer"

    def __init__(self, coordinator, entry: ConfigEntry) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_run_speedtest"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Speedtest RT.RU",
            manufacturer="Rostelecom",
            model="QMS Speedtest",
        )

    async def async_press(self) -> None:
        """Handle the button press."""
        _LOGGER.info("Manually triggering speedtest via button")
        await self.coordinator.async_request_refresh()
