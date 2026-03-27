"""The Speedtest RT.RU integration."""
import asyncio
import logging
import os
import platform
import zipfile
from datetime import timedelta
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval

from .const import (
    DOMAIN,
    CONF_AUTO_UPDATE,
    CONF_SCAN_INTERVAL,
    DEFAULT_AUTO_UPDATE,
    DEFAULT_SCAN_INTERVAL,
    BINARY_NAME,
    BINARY_URL_X86,
    BINARY_URL_ARM64,
    BINARY_DIR,
    BINARY_UPDATE_INTERVAL_HOURS,
    STORAGE_KEY_ETAG_X86,
    STORAGE_KEY_ETAG_ARM64,
)
from .coordinator import SpeedtestCoordinator
from .www_manager import async_setup_cards, async_register_cards, async_remove_cards_and_resources

PLATFORMS = [Platform.SENSOR, Platform.BUTTON]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Speedtest RT.RU from a config entry."""
    # Download binary if not present
    binary_path = await _download_binary(hass, entry)
    if not binary_path:
        _LOGGER.error("Failed to download/extract QMS binary")
        return False

    # Create coordinator
    coordinator = SpeedtestCoordinator(hass, entry, binary_path)

    # Set initial data to avoid blocking setup with a speedtest
    coordinator.async_set_updated_data({
        "download": None,
        "upload": None,
        "ping": None,
        "jitter": None,
        "isp": None,
        "server": None,
        "result_url": None,
        "last_test": None,
        "ip": None,
        "ping_during_download": None,
        "ping_low_during_download": None,
        "ping_high_during_download": None,
        "jitter_during_download": None,
        "ping_during_upload": None,
        "ping_low_during_upload": None,
        "ping_high_during_upload": None,
        "jitter_during_upload": None,
    })

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "binary_path": binary_path,
        "coordinator": coordinator,
    }

    # Forward to platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register service for manual trigger
    _register_services(hass)

    # Install and register Lovelace cards
    await async_setup_cards(hass)
    hass.async_create_task(async_register_cards(hass))

    # Schedule periodic binary update checks
    cancel_updater = async_track_time_interval(
        hass,
        lambda now: hass.async_create_task(_check_binary_update(hass, entry)),
        timedelta(hours=BINARY_UPDATE_INTERVAL_HOURS),
    )
    hass.data[DOMAIN][entry.entry_id]["cancel_updater"] = cancel_updater

    # Listen for options changes
    entry.async_on_unload(entry.add_update_listener(async_options_updated))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Cancel the binary update checker
    entry_data = hass.data[DOMAIN].get(entry.entry_id, {})
    cancel_updater = entry_data.get("cancel_updater")
    if cancel_updater:
        cancel_updater()

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
        # Remove Lovelace cards and resources when integration is removed
        if not hass.data[DOMAIN]:
            await async_remove_cards_and_resources(hass)
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
            if not isinstance(data, dict):
                continue
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


def _get_binary_url() -> tuple[str, str]:
    """Return (binary_url, etag_storage_key) for the current architecture."""
    machine = platform.machine()
    if machine in ("aarch64", "arm64"):
        return BINARY_URL_ARM64, STORAGE_KEY_ETAG_ARM64
    return BINARY_URL_X86, STORAGE_KEY_ETAG_X86


async def _check_binary_update(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Check if a newer binary is available via HEAD request and update if so."""
    binary_url, etag_key = _get_binary_url()
    session = async_get_clientsession(hass)

    try:
        async with session.head(binary_url, allow_redirects=True) as resp:
            if resp.status != 200:
                _LOGGER.debug("Binary update check returned status %s", resp.status)
                return

            remote_etag = resp.headers.get("ETag") or resp.headers.get("Last-Modified")
            if not remote_etag:
                _LOGGER.debug("No ETag/Last-Modified header, skipping update check")
                return

        # Compare with stored ETag
        stored_etag = hass.data[DOMAIN].get(etag_key)
        if stored_etag and stored_etag == remote_etag:
            _LOGGER.debug("Binary is up to date (ETag: %s)", remote_etag)
            return

        _LOGGER.info(
            "New binary version detected (ETag: %s -> %s), downloading update",
            stored_etag,
            remote_etag,
        )

        new_binary_path = await _download_binary(hass, entry, force=True)
        if not new_binary_path:
            _LOGGER.error("Binary update download failed")
            return

        # Store new ETag
        hass.data[DOMAIN][etag_key] = remote_etag

        # Update binary path in all active entry data and coordinators
        for entry_id, data in hass.data[DOMAIN].items():
            if not isinstance(data, dict):
                continue
            coordinator = data.get("coordinator")
            if coordinator and hasattr(coordinator, "_binary_path"):
                coordinator._binary_path = new_binary_path
                data["binary_path"] = new_binary_path

        _LOGGER.info("Binary updated successfully to %s", new_binary_path)

    except Exception as err:
        _LOGGER.error("Error during binary update check: %s", err)


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

        in_server_list = False
        for line in output.splitlines():
            if "===============" in line:
                in_server_list = True
                continue

            if in_server_list and line.strip():
                parts = line.split(maxsplit=3)
                if len(parts) >= 3 and parts[0].isdigit():
                    server_id = parts[0]
                    server_name = parts[1] if len(parts) > 1 else ""
                    server_city = parts[2] if len(parts) > 2 else ""
                    display_name = f"{server_city} - {server_name}" if server_city else server_name
                    servers[server_id] = display_name

        _LOGGER.debug("Found %d servers", len(servers) - 1)
        return servers

    except Exception as err:
        _LOGGER.error("Error fetching server list: %s", err)
        return {"auto": "Auto (Best Server)"}


async def _download_binary(
    hass: HomeAssistant, entry: ConfigEntry, force: bool = False
) -> str | None:
    """Download and extract the QMS binary ZIP.

    If force=False, skips download when the binary already exists and is executable.
    If force=True, always re-downloads (used for updates).
    Stores the remote ETag in hass.data after a successful download.
    """
    binary_url, etag_key = _get_binary_url()

    binary_dir = Path(hass.config.path(BINARY_DIR))
    binary_path = binary_dir / BINARY_NAME

    if not force and binary_path.exists() and os.access(str(binary_path), os.X_OK):
        _LOGGER.debug("QMS binary already exists at %s", binary_path)
        # Seed ETag on first boot so the next check has something to compare
        if etag_key not in hass.data.get(DOMAIN, {}):
            await _store_remote_etag(hass, binary_url, etag_key)
        return str(binary_path)

    session = async_get_clientsession(hass)
    zip_path = binary_dir / "qms_lib.zip"

    try:
        async with session.get(binary_url) as resp:
            if resp.status != 200:
                _LOGGER.error("Failed to download ZIP from %s: %s", binary_url, resp.status)
                return None
            content = await resp.read()
            remote_etag = resp.headers.get("ETag") or resp.headers.get("Last-Modified")

        await hass.async_add_executor_job(zip_path.write_bytes, content)
        _LOGGER.debug("Downloaded QMS ZIP to %s", zip_path)

        def extract_zip():
            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(binary_dir)

        await hass.async_add_executor_job(extract_zip)

        extracted_binary = binary_dir / BINARY_NAME
        if not extracted_binary.exists():
            for file_path in binary_dir.iterdir():
                if file_path.is_file() and file_path.name != "qms_lib.zip":
                    extracted_binary = file_path
                    _LOGGER.info("Using extracted binary: %s", extracted_binary.name)
                    break
            else:
                _LOGGER.error("No executable found in ZIP")
                return None

        await hass.async_add_executor_job(os.chmod, str(extracted_binary), 0o755)
        await hass.async_add_executor_job(zip_path.unlink)
        _LOGGER.info("QMS binary ready at %s", extracted_binary)

        # Store ETag so future checks can detect updates
        if remote_etag:
            hass.data.setdefault(DOMAIN, {})[etag_key] = remote_etag

        return str(extracted_binary)

    except Exception as err:
        _LOGGER.error("Error downloading/extracting binary: %s", err)
        if zip_path.exists():
            await hass.async_add_executor_job(zip_path.unlink)
        return None


async def _store_remote_etag(hass: HomeAssistant, binary_url: str, etag_key: str) -> None:
    """Do a HEAD request to seed the stored ETag without downloading the binary."""
    session = async_get_clientsession(hass)
    try:
        async with session.head(binary_url, allow_redirects=True) as resp:
            etag = resp.headers.get("ETag") or resp.headers.get("Last-Modified")
            if etag:
                hass.data.setdefault(DOMAIN, {})[etag_key] = etag
                _LOGGER.debug("Seeded binary ETag: %s", etag)
    except Exception as err:
        _LOGGER.debug("Could not seed binary ETag: %s", err)
