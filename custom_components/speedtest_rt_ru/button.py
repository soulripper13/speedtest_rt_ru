"""Button platform for Speedtest RT.RU integration."""
from __future__ import annotations

import logging
from email.utils import parsedate_to_datetime

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import SpeedtestCoordinator
from . import _check_and_update_binary

_LOGGER = logging.getLogger(__name__)


def _format_last_modified(last_modified: str | None) -> str:
    """Parse HTTP Last-Modified header into YYYY-MM-DD string."""
    if not last_modified:
        return "unknown"
    try:
        dt = parsedate_to_datetime(last_modified)
        return dt.strftime("%Y-%m-%d")
    except Exception:
        return last_modified


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Speedtest RT.RU buttons."""
    coordinator: SpeedtestCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]
    async_add_entities([
        SpeedtestButton(coordinator, entry),
        CheckUpdateButton(coordinator, entry),
    ])


class SpeedtestButton(CoordinatorEntity[SpeedtestCoordinator], ButtonEntity):
    """Button to manually trigger a speedtest."""

    _attr_has_entity_name = True
    _attr_name = "Run Speedtest"
    _attr_icon = "mdi:speedometer"

    def __init__(self, coordinator: SpeedtestCoordinator, entry: ConfigEntry) -> None:
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


class CheckUpdateButton(CoordinatorEntity[SpeedtestCoordinator], ButtonEntity):
    """Button to check for and apply qms_lib binary updates."""

    _attr_has_entity_name = True
    _attr_name = "Check for Update"
    _attr_icon = "mdi:update"

    def __init__(self, coordinator: SpeedtestCoordinator, entry: ConfigEntry) -> None:
        """Initialize the button."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_check_update"

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
        """Check for a binary update and notify the user of the result."""
        _LOGGER.info("Manual binary update check triggered")

        try:
            was_updated, last_modified = await _check_and_update_binary(
                self.hass, self._entry
            )
        except Exception as err:
            _LOGGER.error("Update check failed: %s", err)
            self.hass.components.persistent_notification.async_create(
                "Update check failed. See logs for details.",
                title="Speedtest RT.RU",
                notification_id="speedtest_rt_ru_update",
            )
            return

        if was_updated:
            date_str = _format_last_modified(last_modified)
            message = f"New update available — last modified: {date_str}"
        else:
            message = "No new update available"

        self.hass.components.persistent_notification.async_create(
            message,
            title="Speedtest RT.RU",
            notification_id="speedtest_rt_ru_update",
        )
