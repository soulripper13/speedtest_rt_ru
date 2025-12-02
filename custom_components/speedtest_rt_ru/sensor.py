"""Support for Speedtest RT.RU sensors."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    ATTR_DOWNLOAD,
    ATTR_UPLOAD,
    ATTR_PING,
    ATTR_JITTER,
    ATTR_ISP,
    ATTR_SERVER,
)
from .coordinator import SpeedtestCoordinator

_LOGGER = logging.getLogger(__name__)

SENSORS = (
    SensorEntityDescription(
        key=ATTR_DOWNLOAD,
        name="Download",
        native_unit_of_measurement="Mbit/s",
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_UPLOAD,
        name="Upload",
        native_unit_of_measurement="Mbit/s",
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_PING,
        name="Ping",
        native_unit_of_measurement="ms",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_JITTER,
        name="Jitter",
        native_unit_of_measurement="ms",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_ISP,
        name="ISP",
        icon="mdi:server-network",
    ),
    SensorEntityDescription(
        key=ATTR_SERVER,
        name="Server",
        icon="mdi:server",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Speedtest RT.RU sensors."""
    coordinator: SpeedtestCoordinator = hass.data[DOMAIN][entry.entry_id]["coordinator"]

    sensors = [
        SpeedtestSensor(coordinator, description)
        for description in SENSORS
    ]
    async_add_entities(sensors)


class SpeedtestSensor(CoordinatorEntity[SpeedtestCoordinator], SensorEntity):
    """Representation of a Speedtest RT.RU sensor."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: SpeedtestCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.entry.entry_id}_{description.key}"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.coordinator.entry.entry_id)},
            name="Speedtest RT.RU",
            manufacturer="Rostelecom",
            model="QMS Speedtest",
        )

    @property
    def native_value(self) -> StateType | str | None:
        """Return the state."""
        if self.coordinator.data is None:
            return None

        raw_value = self.coordinator.data.get(self.entity_description.key)
        if raw_value is None or raw_value == "unknown":
            if self.entity_description.native_unit_of_measurement:
                return None
            return "unknown"

        try:
            parsed = float(raw_value)
            return round(parsed, 2) if "." in str(raw_value) else int(parsed)
        except ValueError:
            return raw_value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        if self.coordinator.data is None:
            return {}
        return {
            key: self.coordinator.data.get(key, "unknown")
            for key in self.coordinator.data
            if key != self.entity_description.key
        }
