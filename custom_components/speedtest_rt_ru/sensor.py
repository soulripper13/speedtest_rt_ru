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
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    CONF_AUTO_UPDATE,
    CONF_SCAN_INTERVAL,
    CONF_SERVER_ID,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SERVER_ID,
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


class SpeedtestSensorData(DataUpdateCoordinator):
    """Data for Speedtest RT.RU sensors."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, binary_path: str
    ) -> None:
        """Initialize the coordinator."""
        self._binary_path = binary_path
        self.entry = entry

        # Get server_id from options or data
        options = entry.options
        self._server_id = options.get(
            CONF_SERVER_ID,
            entry.data.get(CONF_SERVER_ID, DEFAULT_SERVER_ID)
        )

        # Set update interval based on options (no polling if auto_update=False)
        auto_update = options.get(CONF_AUTO_UPDATE, True)
        interval = timedelta(
            seconds=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        ) if auto_update else None

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=interval,
            update_method=self._async_update_data,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from QMS binary."""
        try:
            # Build command arguments
            cmd_args = [self._binary_path]

            # Add server selection if not "auto"
            if self._server_id and self._server_id != "auto":
                cmd_args.extend(["-S", self._server_id])

            proc = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            stdout, stderr = await proc.communicate()
            output = stdout.decode("utf-8", errors="ignore").strip()

            _LOGGER.debug("QMS Raw Output: %s", output)
            if stderr:
                _LOGGER.debug("QMS Stderr: %s", stderr.decode("utf-8", errors="ignore"))

            # Parse with regex (English labels from QMS binary)
            data = _parse_output(output)
            return data  # Always return, even if partial "unknown"

        except Exception as err:
            _LOGGER.error("Error running QMS binary: %s", err)
            raise UpdateFailed(f"Failed to update: {err}")


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the Speedtest RT.RU sensors."""
    # Get shared data (binary_path) from hass.data
    hass_data = hass.data[DOMAIN][entry.entry_id]
    binary_path = hass_data["binary_path"]

    # Create coordinator
    coordinator = SpeedtestSensorData(hass, entry, binary_path)

    # Initial refresh—raise NotReady if fails
    try:
        await coordinator.async_config_entry_first_refresh()
    except UpdateFailed as err:
        _LOGGER.error("Initial update failed: %s", err)
        raise ConfigEntryNotReady("Speedtest initial run failed")

    # Store coordinator for service access
    hass_data["coordinator"] = coordinator

    # Add sensors
    sensors = [
        SpeedtestSensor(coordinator, description)
        for description in SENSORS
    ]
    async_add_entities(sensors)


class SpeedtestSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Speedtest RT.RU sensor."""

    _attr_has_entity_name = True
    _attr_should_poll = False  # Rely on coordinator

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
        raw_value = self.coordinator.data.get(self.entity_description.key)
        if raw_value is None or raw_value == "unknown":
            # For numeric sensors (has unit), return None (unavailable)
            if self.entity_description.native_unit_of_measurement:
                return None
            # For strings (no unit), return 'unknown'
            return "unknown"

        # Parse to number if possible
        try:
            parsed = float(raw_value)
            return round(parsed, 2) if "." in str(raw_value) else int(parsed)
        except ValueError:
            # Fallback to string (e.g., ISP name)
            return raw_value

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return extra state attributes."""
        return {
            key: self.coordinator.data.get(key, "unknown")
            for key in self.coordinator.data
            if key != self.entity_description.key
        }


def _parse_output(output: str) -> dict[str, str]:
    """Parse QMS binary output."""
    data = {desc.key: "unknown" for desc in SENSORS}

    # Regex patterns for English QMS output (case-insensitive, multi-line)
    patterns = {
        ATTR_PING: r"Idle Latency:\s*(\d+(?:\.\d+)?)\s*ms",
        ATTR_JITTER: r"Jitter:\s*(\d+(?:\.\d+)?)\s*ms",
        ATTR_DOWNLOAD: r"Download:\s*(\d+(?:\.\d+)?)\s*Mbit/s",
        ATTR_UPLOAD: r"Upload:\s*(\d+(?:\.\d+)?)\s*Mbit/s",
        ATTR_ISP: r"ISP:\s*([^\n]+)",
        ATTR_SERVER: r"Server:\s*([^\n]+)",
    }

    for attr, pattern in patterns.items():
        match = re.search(pattern, output, re.IGNORECASE | re.MULTILINE)
        if match:
            data[attr] = match.group(1).strip()

    return data
