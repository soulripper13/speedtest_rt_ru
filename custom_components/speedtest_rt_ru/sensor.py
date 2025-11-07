"""Support for Speedtest RT.RU sensors."""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfDataRate, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_AUTO_UPDATE,
    CONF_SCAN_INTERVAL,
    DEFAULT_SCAN_INTERVAL,
    ATTR_DOWNLOAD,
    ATTR_UPLOAD,
    ATTR_PING,
    ATTR_JITTER,
    ATTR_ISP,
    ATTR_SERVER,
)

_LOGGER = logging.getLogger(__name__)

SENSORS = (
    SensorEntityDescription(
        key=ATTR_DOWNLOAD,
        name="Download",
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_UPLOAD,
        name="Upload",
        native_unit_of_measurement=UnitOfDataRate.MEGABITS_PER_SECOND,
        device_class=SensorDeviceClass.DATA_RATE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_PING,
        name="Ping",
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
        device_class=SensorDeviceClass.DURATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key=ATTR_JITTER,
        name="Jitter",
        native_unit_of_measurement=UnitOfTime.MILLISECONDS,
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


class SpeedtestSensorData:
    """Data for Speedtest RT.RU sensors."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, binary_path: str
    ) -> None:
        """Initialize the sensor data."""
        self.hass = hass
        self.entry = entry
        self.binary_path = binary_path
        self.data: dict[str, Any] = {}
        self._unsub_options = None

    async def async_refresh(self) -> None:
        """Refresh data from QMS binary."""
        try:
            proc = await asyncio.create_subprocess_exec(
                self.binary_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            output = stdout.decode("utf-8", errors="ignore").strip()

            _LOGGER.debug("QMS Raw Output: %s", output)
            if stderr:
                _LOGGER.debug("QMS Stderr: %s", stderr.decode("utf-8", errors="ignore"))

            # Parse with regex (Russian labels first, fallback to English)
            self.data = _parse_output(output)
        except Exception as err:
            _LOGGER.error("Error running QMS binary: %s", err)
            self.data = {key: "unknown" for key in [desc.key for desc in SENSORS]}

    @property
    def scan_interval(self) -> timedelta | None:
        """Return the scan interval."""
        if not self.entry.options.get(CONF_AUTO_UPDATE, DEFAULT_AUTO_UPDATE):
            return None
        return timedelta(seconds=self.entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL))


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Speedtest RT.RU sensors."""
    # Get shared data (binary_path) from hass.data
    hass_data = hass.data[DOMAIN][entry.entry_id]
    binary_path = hass_data["binary_path"]

    # Create coordinator async here (non-blocking)
    coordinator = SpeedtestSensorData(hass, entry, binary_path)

    # Add sensors
    sensors = [
        SpeedtestSensor(coordinator, description)
        for description in SENSORS
    ]
    async_add_entities(sensors, True)  # Update immediately after add


class SpeedtestSensor(CoordinatorEntity[SpeedtestSensorData], SensorEntity):
    """Representation of a Speedtest RT.RU sensor."""

    _attr_has_entity_name = True
    _attr_unique_id_suffix = None

    def __init__(
        self,
        coordinator: SpeedtestSensorData,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}.{description.key}"

    @property
    def native_value(self) -> StateType | str | None:
        """Return the state."""
        if (value := self.coordinator.data.get(self.entity_description.key)) != "unknown":
            try:
                return round(float(value), 2) if "." in str(value) else int(value)
            except ValueError:
                pass
        return value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            key: self.coordinator.data.get(key, "unknown")
            for key in self.coordinator.data
            if key != self.entity_description.key
        }

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return all(
            val != "error" for val in self.coordinator.data.values()
        )


def _parse_output(output: str) -> dict[str, str]:
    """Parse QMS binary output."""
    data = {key: "unknown" for key in [desc.key for desc in SENSORS]}

    # Regex patterns (Russian first, case-insensitive)
    patterns = {
        ATTR_PING: r"пинг\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*мс",
        ATTR_JITTER: r"джиттер\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*мс",
        ATTR_DOWNLOAD: r"загрузка\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(мбит|mbps)",
        ATTR_UPLOAD: r"отдача\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*(мбит|mbps)",
        ATTR_ISP: r"(провайдер|isp)\s*[:\-]?\s*([^\n,]+)",
        ATTR_SERVER: r"(сервер|server)\s*[:\-]?\s*([^\n,]+)",
    }

    for attr, pattern in patterns.items():
        match = re.search(pattern, output, re.IGNORECASE | re.MULTILINE)
        if match:
            data[attr] = match.group(1).strip()
        else:
            # Fallback English patterns
            eng_pattern = (
                pattern.replace("пинг", "ping")
                .replace("джиттер", "jitter")
                .replace("загрузка", "download")
                .replace("отдача", "upload")
            )
            eng_match = re.search(eng_pattern, output, re.IGNORECASE | re.MULTILINE)
            if eng_match:
                data[attr] = eng_match.group(1).strip()

    return data
