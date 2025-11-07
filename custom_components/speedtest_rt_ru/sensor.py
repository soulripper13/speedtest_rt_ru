from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfDataRate, UnitOfTime
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

SENSOR_KEYS = {
    "Download": {"unit": UnitOfDataRate.MEGABITS_PER_SECOND},
    "Upload": {"unit": UnitOfDataRate.MEGABITS_PER_SECOND},
    "Ping": {"unit": UnitOfTime.MILLISECONDS},
    "Jitter": {"unit": UnitOfTime.MILLISECONDS},
    "ISP": {"unit": None},
    "Server": {"unit": None},
}


async def async_setup_entry(hass, entry, async_add_entities):
    """Set up the Speedtest RT.RU sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [SpeedtestRtSensor(coordinator, key, cfg["unit"]) for key, cfg in SENSOR_KEYS.items()]
    async_add_entities(entities)


class SpeedtestRtSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Speedtest RT.RU sensor."""

    def __init__(self, coordinator, key, unit):
        super().__init__(coordinator)
        self._key = key
        self._attr_unit_of_measurement = unit

    @property
    def name(self):
        return f"Speedtest RT.RU {self._key}"

    @property
    def unique_id(self):
        return f"speedtest_rt_ru_{self._key.lower()}"

    @property
    def native_value(self):
        """Return the current value of the sensor."""
        value = self.coordinator.data.get(self._key)
        if value is None:
            return None
        try:
            return float(value.replace(",", "."))
        except (ValueError, AttributeError):
            return value

    @property
    def icon(self):
        icons = {
            "Download": "mdi:download-network",
            "Upload": "mdi:upload-network",
            "Ping": "mdi:speedometer",
            "Jitter": "mdi:waves",
            "ISP": "mdi:account",
            "Server": "mdi:server-network",
        }
        return icons.get(self._key, "mdi:gauge")
