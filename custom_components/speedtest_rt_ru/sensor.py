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
    ATTR_RESULT_URL,
    ATTR_DATE_LAST_TEST,
    ATTR_IP,
    ATTR_DOWNLOAD_LATENCY_IQM,
    ATTR_DOWNLOAD_LATENCY_LOW,
    ATTR_DOWNLOAD_LATENCY_HIGH,
    ATTR_DOWNLOAD_LATENCY_JITTER,
    ATTR_UPLOAD_LATENCY_IQM,
    ATTR_UPLOAD_LATENCY_LOW,
    ATTR_UPLOAD_LATENCY_HIGH,
    ATTR_UPLOAD_LATENCY_JITTER,
)
from .coordinator import SpeedtestCoordinator

_LOGGER = logging.getLogger(__name__)

# Latency sensor keys — disabled by default, user can enable
_LATENCY_KEYS = {
    ATTR_DOWNLOAD_LATENCY_IQM,
    ATTR_DOWNLOAD_LATENCY_LOW,
    ATTR_DOWNLOAD_LATENCY_HIGH,
    ATTR_DOWNLOAD_LATENCY_JITTER,
    ATTR_UPLOAD_LATENCY_IQM,
    ATTR_UPLOAD_LATENCY_LOW,
    ATTR_UPLOAD_LATENCY_HIGH,
    ATTR_UPLOAD_LATENCY_JITTER,
}

SENSORS = (
    SensorEntityDescription(
        key=ATTR_DOWNLOAD,
        name="Download",
        native_unit_of_measurement="Mbit/s",
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:download",
    ),
    SensorEntityDescription(
        key=ATTR_UPLOAD,
        name="Upload",
        native_unit_of_measurement="Mbit/s",
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:upload",
    ),
    SensorEntityDescription(
        key=ATTR_PING,
        name="Ping",
        native_unit_of_measurement="ms",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:speedometer",
    ),
    SensorEntityDescription(
        key=ATTR_JITTER,
        name="Jitter",
        native_unit_of_measurement="ms",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:pulse",
    ),
    SensorEntityDescription(
        key=ATTR_ISP,
        name="ISP",
        icon="mdi:web",
    ),
    SensorEntityDescription(
        key=ATTR_SERVER,
        name="Server",
        icon="mdi:server",
    ),
    SensorEntityDescription(
        key=ATTR_IP,
        name="IP",
        icon="mdi:ip-network",
    ),
    SensorEntityDescription(
        key=ATTR_RESULT_URL,
        name="Result URL",
        icon="mdi:link",
    ),
    SensorEntityDescription(
        key=ATTR_DATE_LAST_TEST,
        name="Last Test",
        device_class=SensorDeviceClass.TIMESTAMP,
        icon="mdi:clock",
    ),
    # Latency detail sensors (disabled by default)
    SensorEntityDescription(
        key=ATTR_DOWNLOAD_LATENCY_IQM,
        name="Download Ping",
        native_unit_of_measurement="ms",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:speedometer",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key=ATTR_DOWNLOAD_LATENCY_LOW,
        name="Download Ping Min",
        native_unit_of_measurement="ms",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:speedometer",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key=ATTR_DOWNLOAD_LATENCY_HIGH,
        name="Download Ping Max",
        native_unit_of_measurement="ms",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:speedometer",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key=ATTR_DOWNLOAD_LATENCY_JITTER,
        name="Download Jitter",
        native_unit_of_measurement="ms",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:pulse",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key=ATTR_UPLOAD_LATENCY_IQM,
        name="Upload Ping",
        native_unit_of_measurement="ms",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:speedometer",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key=ATTR_UPLOAD_LATENCY_LOW,
        name="Upload Ping Min",
        native_unit_of_measurement="ms",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:speedometer",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key=ATTR_UPLOAD_LATENCY_HIGH,
        name="Upload Ping Max",
        native_unit_of_measurement="ms",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:speedometer",
        entity_registry_enabled_default=False,
    ),
    SensorEntityDescription(
        key=ATTR_UPLOAD_LATENCY_JITTER,
        name="Upload Jitter",
        native_unit_of_measurement="ms",
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:pulse",
        entity_registry_enabled_default=False,
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
            return None

        # Timestamp sensor returns ISO string directly
        if self.entity_description.device_class == SensorDeviceClass.TIMESTAMP:
            return raw_value

        # Numeric sensors
        if self.entity_description.native_unit_of_measurement:
            try:
                parsed = float(raw_value)
                return round(parsed, 2) if "." in str(raw_value) else int(parsed)
            except ValueError:
                return None

        return raw_value
