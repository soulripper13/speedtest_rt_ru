"""Diagnostics support for Speedtest RT.RU."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import SpeedtestCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    hass_data = hass.data.get(DOMAIN, {}).get(entry.entry_id, {})
    coordinator: SpeedtestCoordinator | None = hass_data.get("coordinator")

    diagnostics_data: dict[str, Any] = {
        "entry": {
            "entry_id": entry.entry_id,
            "version": entry.version,
            "domain": entry.domain,
            "title": entry.title,
            "data": dict(entry.data),
            "options": dict(entry.options),
        },
    }

    if coordinator:
        diagnostics_data["coordinator"] = {
            "last_update_success": coordinator.last_update_success,
            "data": coordinator.data,
        }
        if coordinator.last_exception:
            diagnostics_data["coordinator"]["last_exception"] = str(
                coordinator.last_exception
            )

    return diagnostics_data
