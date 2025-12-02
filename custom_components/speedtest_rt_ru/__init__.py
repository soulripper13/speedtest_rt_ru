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

PLATFORMS = [Platform.SENSOR, Platform.BUTTON]

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
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

async def async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    await hass.config_entries.async_reload(entry.entry_id)

@callback
def _register_services(hass: HomeAssistant) -> None:
    """Register the perform_test service."""

    async def async_perform_test(service_call) -> None:
        """Manually trigger speedtest via coordinator."""
        hass_data = hass.data.get(DOMAIN)
        if not hass_data:
            _LOGGER.warning("No Speedtest RT.RU data found")
            return

        coordinator = None
        for entry_id, data in hass_data.items():
            coordinator = data.get("coordinator")
            if coordinator:
                break

        if coordinator:
            try:
                await coordinator.async_request_refresh()
                _LOGGER.info("Manually triggered refresh on Speedtest RT.RU coordinator")
            except Exception as err:
                _LOGGER.error("Failed to refresh Speedtest RT.RU: %s", err)
        else:
            _LOGGER.warning("No Speedtest RT.RU coordinator found to update")

    if not hass.services.has_service(DOMAIN, "perform_test"):
        hass.services.async_register(DOMAIN, "perform_test", async_perform_test)

async def get_available_servers(binary_path: str) -> dict[str, str]:
    """Fetch available servers from QMS binary."""
    try:
        proc = await asyncio.create_subprocess_exec(
            binary_path,
            "-L",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        output = stdout.decode("utf-8", errors="ignore").strip()

        servers = {"auto": "Auto (Best Server)"}

        # Parse server list - skip header lines
        in_server_list = False
        for line in output.splitlines():
            if "===============" in line:
                in_server_list = True
                continue

            if in_server_list and line.strip():
                # Parse line format: ID  Name  City  Region
                parts = line.split(maxsplit=3)
                if len(parts) >= 3 and parts[0].isdigit():
                    server_id = parts[0]
                    server_name = parts[1] if len(parts) > 1 else ""
                    server_city = parts[2] if len(parts) > 2 else ""

                    # Create display name: "City - Name"
                    display_name = f"{server_city} - {server_name}" if server_city else server_name
                    servers[server_id] = display_name

        _LOGGER.debug("Found %d servers", len(servers) - 1)
        return servers

    except Exception as err:
        _LOGGER.error("Error fetching server list: %s", err)
        return {"auto": "Auto (Best Server)"}

async def _download_binary(hass: HomeAssistant, entry: ConfigEntry) -> str | None:
    """Download and extract the QMS binary ZIP if not present."""
    machine = platform.machine()
    if machine != "x86_64":
        _LOGGER.warning(
            "QMS binary is x86_64 only. Running on %s—consider manual binary or alternative.",
            machine,
        )

    binary_dir = Path(hass.config.path(BINARY_DIR))
    # No mkdir—component dir exists
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

        # Write file in executor to avoid blocking
        await hass.async_add_executor_job(zip_path.write_bytes, content)
        _LOGGER.debug("Downloaded QMS ZIP to %s", zip_path)

        # Extract ZIP in executor to avoid blocking
        def extract_zip():
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(binary_dir)

        await hass.async_add_executor_job(extract_zip)
        _LOGGER.debug("Extracted QMS ZIP contents to %s", binary_dir)

        # Find and chmod the binary (assume named 'qms_lib'; fallback to first executable)
        extracted_binary = binary_dir / BINARY_NAME
        if not extracted_binary.exists():
            # Fallback: chmod any non-dir file (adjust if multiple)
            for file_path in binary_dir.iterdir():
                if file_path.is_file() and file_path.name != "qms_lib.zip":  # Skip ZIP
                    extracted_binary = file_path
                    _LOGGER.info("Using extracted binary: %s", extracted_binary.name)
                    break
            else:
                _LOGGER.error("No executable found in ZIP")
                return None

        # Chmod in executor to avoid blocking
        await hass.async_add_executor_job(os.chmod, str(extracted_binary), 0o755)
        # Cleanup ZIP in executor
        await hass.async_add_executor_job(zip_path.unlink)
        _LOGGER.info("Extracted and made executable QMS binary at %s", extracted_binary)
        return str(extracted_binary)

    except Exception as err:
        _LOGGER.error("Error downloading/extracting binary: %s", err)
        if zip_path.exists():
            await hass.async_add_executor_job(zip_path.unlink)
        return None
