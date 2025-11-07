"""The Speedtest RT.RU integration."""
import asyncio
import logging
import os
import platform
import zipfile
from pathlib import Path

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import entity_registry
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    CONF_AUTO_UPDATE,
    CONF_SCAN_INTERVAL,
    DEFAULT_AUTO_UPDATE,
    DEFAULT_SCAN_INTERVAL,
    BINARY_NAME,
    BINARY_URL,
    BINARY_DIR,
)

PLATFORMS = [Platform.SENSOR]

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Speedtest RT.RU from a config entry."""
    # Download binary if not present
    binary_path = await _download_binary(hass, entry)
    if not binary_path:
        _LOGGER.error("Failed to download/extract QMS binary")
        return False

    # Store binary path in hass.data (accessed async by platforms)
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {"binary_path": binary_path}

    # Forward to platforms (async loads sensor.py)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register service for manual trigger
    _register_services(hass)

    # Listen for options changes
    entry.add_update_listener(async_options_updated)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

async def async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)

@callback
def _register_services(hass: HomeAssistant) -> None:
    """Register the perform_test service."""

    async def async_perform_test(service_call) -> None:
        """Manually trigger speedtest on all sensors."""
        entity_reg = entity_registry.async_get(hass)
        updated_entities = []
        for entity_id, entity_entry in entity_reg.entities.items():
            if (
                entity_id.startswith("sensor.speedtest_rt_ru_")
                and entity_entry.domain == "sensor"
                and DOMAIN in entity_entry.unique_id
            ):
                hass.async_create_task(
                    hass.services.async_call(
                        "homeassistant",
                        "update_entity",
                        {"entity_id": entity_id},
                    )
                )
                updated_entities.append(entity_id)
        if updated_entities:
            _LOGGER.info("Manually triggered update for: %s", ", ".join(updated_entities))
        else:
            _LOGGER.warning("No Speedtest RT.RU sensors found to update")

    hass.services.async_register(DOMAIN, "perform_test", async_perform_test)

async def _download_binary(hass: HomeAssistant, entry: ConfigEntry) -> str | None:
    """Download and extract the QMS binary ZIP if not present."""
    machine = platform.machine()
    if machine != "x86_64":
        _LOGGER.warning(
            "QMS binary is x86_64 only. Running on %s—consider manual binary or alternative.",
            machine,
        )

    binary_dir = Path(hass.config.path(BINARY_DIR))
    binary_dir.mkdir(exist_ok=True)
    binary_path = binary_dir / BINARY_NAME

    if binary_path.exists() and os.access(str(binary_path), os.X_OK):
        _LOGGER.debug("QMS binary already exists and is executable at %s", binary_path)
        return str(binary_path)

    # Download ZIP
    session = async_get_clientsession(hass)
    zip_path = binary_dir / "qms_lib.zip"
    try:
        async with session.get(BINARY_URL) as resp:
            if resp.status != 200:
                _LOGGER.error("Failed to download ZIP from %s: %s", BINARY_URL, resp.status)
                return None
            content = await resp.read()
        zip_path.write_bytes(content)
        _LOGGER.debug("Downloaded QMS ZIP to %s", zip_path)

        # Extract ZIP
        with zipfile.ZipFile(zip_path, 'r') as zf:
            zf.extractall(binary_dir)
        _LOGGER.debug("Extracted QMS ZIP contents to %s", binary_dir)

        # Find and chmod the binary (assume named 'qms'; fallback to first executable)
        extracted_binary = binary_dir / BINARY_NAME
        if not extracted_binary.exists():
            # Fallback: chmod any non-dir file (adjust if multiple)
            for file_path in binary_dir.iterdir():
                if file_path.is_file():
                    extracted_binary = file_path
                    _LOGGER.info("Using extracted binary: %s", extracted_binary.name)
                    break
            else:
                _LOGGER.error("No executable found in ZIP")
                return None

        os.chmod(str(extracted_binary), 0o755)
        zip_path.unlink()  # Clean up ZIP
        _LOGGER.info("Extracted and made executable QMS binary at %s", extracted_binary)
        return str(extracted_binary)

    except Exception as err:
        _LOGGER.error("Error downloading/extracting binary: %s", err)
        if zip_path.exists():
            zip_path.unlink()
        return None
