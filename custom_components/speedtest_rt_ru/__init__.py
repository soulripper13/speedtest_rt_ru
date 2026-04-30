"""The Speedtest RT.RU integration."""
import asyncio
from dataclasses import dataclass
import logging
import os
import platform
import shutil
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store

from .const import (
    DOMAIN,
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

BINARY_STORAGE_VERSION = 1
BINARY_STORAGE_KEY = f"{DOMAIN}.binary"
DATA_BINARY_UPDATE_LOCK = "binary_update_lock"

UPDATE_STATUS_UPDATED = "updated"
UPDATE_STATUS_CURRENT = "current"
UPDATE_STATUS_FAILED = "failed"
UPDATE_STATUS_UNKNOWN = "unknown"


@dataclass(frozen=True)
class BinaryUpdateResult:
    """Result of a binary update check."""

    status: str
    last_modified: str | None = None
    remote_etag: str | None = None
    message: str | None = None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Speedtest RT.RU from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Download binary if not present
    binary_path = await _download_binary(hass)
    if not binary_path:
        _LOGGER.error("Failed to download/extract QMS binary")
        return False

    # Create coordinator
    coordinator = SpeedtestCoordinator(hass, entry, binary_path)

    # Set initial data to avoid blocking setup with a speedtest
    coordinator.async_set_updated_data({
        "download": 0,
        "upload": 0,
        "ping": 0,
        "jitter": 0,
        "isp": "—",
        "server": "—",
        "result_url": None,
        "last_test": None,
        "ip": None,
        "ping_during_download": None,
        "ping_during_upload": None,
    })

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

    @callback
    def _schedule_binary_update_check(_now) -> None:
        """Schedule a binary update check from the event loop."""
        hass.async_create_task(_check_binary_update(hass, entry))

    # Schedule periodic binary update checks
    cancel_updater = async_track_time_interval(
        hass,
        _schedule_binary_update_check,
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
        has_entries = any(
            isinstance(data, dict) and "coordinator" in data
            for data in hass.data[DOMAIN].values()
        )
        if not has_entries:
            await async_remove_cards_and_resources(hass)
            hass.data.pop(DOMAIN, None)
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


def _get_binary_update_lock(hass: HomeAssistant) -> asyncio.Lock:
    """Return the shared binary update lock."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    lock = domain_data.get(DATA_BINARY_UPDATE_LOCK)
    if lock is None:
        lock = asyncio.Lock()
        domain_data[DATA_BINARY_UPDATE_LOCK] = lock
    return lock


def _get_binary_path(hass: HomeAssistant) -> Path:
    """Return the installed binary path."""
    return Path(hass.config.path(BINARY_DIR)) / BINARY_NAME


def _is_binary_ready(binary_path: Path) -> bool:
    """Return true when the binary exists and can be executed."""
    return (
        binary_path.is_file()
        and os.access(str(binary_path), os.X_OK)
    )


async def _async_load_binary_storage(
    hass: HomeAssistant,
) -> tuple[Store, dict[str, Any]]:
    """Load binary update metadata from Home Assistant storage."""
    store = Store(hass, BINARY_STORAGE_VERSION, BINARY_STORAGE_KEY)
    data = await store.async_load()
    if not isinstance(data, dict):
        data = {}

    binaries = data.get("binaries")
    if not isinstance(binaries, dict):
        data["binaries"] = {}

    return store, data


async def _async_get_binary_metadata(
    hass: HomeAssistant, etag_key: str
) -> dict[str, Any]:
    """Return persisted metadata for the current architecture."""
    _, data = await _async_load_binary_storage(hass)
    metadata = data["binaries"].get(etag_key)
    return metadata if isinstance(metadata, dict) else {}


async def _async_store_binary_metadata(
    hass: HomeAssistant, etag_key: str, metadata: dict[str, Any]
) -> None:
    """Persist metadata for the installed binary."""
    store, data = await _async_load_binary_storage(hass)
    data["binaries"][etag_key] = metadata
    await store.async_save(data)


async def _async_fetch_remote_binary_metadata(
    hass: HomeAssistant, binary_url: str
) -> BinaryUpdateResult:
    """Fetch remote binary version metadata."""
    session = async_get_clientsession(hass)

    try:
        async with session.head(binary_url, allow_redirects=True) as resp:
            if resp.status != 200:
                message = f"Binary update check returned HTTP {resp.status}"
                _LOGGER.warning(message)
                return BinaryUpdateResult(
                    status=UPDATE_STATUS_FAILED,
                    message=message,
                )

            last_modified = resp.headers.get("Last-Modified")
            remote_etag = resp.headers.get("ETag") or last_modified
            if not remote_etag:
                message = "No ETag or Last-Modified header returned by binary host"
                _LOGGER.warning(message)
                return BinaryUpdateResult(
                    status=UPDATE_STATUS_UNKNOWN,
                    message=message,
                )

            return BinaryUpdateResult(
                status=UPDATE_STATUS_CURRENT,
                last_modified=last_modified,
                remote_etag=remote_etag,
            )

    except Exception as err:
        message = f"Error checking binary version: {err}"
        _LOGGER.error(message)
        return BinaryUpdateResult(
            status=UPDATE_STATUS_FAILED,
            message=message,
        )


async def _check_and_update_binary(
    hass: HomeAssistant, _entry: ConfigEntry
) -> BinaryUpdateResult:
    """Check for a newer binary and download it if available.

    Returns a BinaryUpdateResult describing whether the binary was updated,
    already current, failed, or could not be checked.
    """
    async with _get_binary_update_lock(hass):
        try:
            return await _async_check_and_update_binary_locked(hass)
        except Exception as err:
            message = f"Error during binary update check: {err}"
            _LOGGER.error(message)
            return BinaryUpdateResult(
                status=UPDATE_STATUS_FAILED,
                message=message,
            )


async def _async_check_and_update_binary_locked(
    hass: HomeAssistant,
) -> BinaryUpdateResult:
    """Check and update the binary while the shared update lock is held."""
    binary_url, etag_key = _get_binary_url()
    binary_path = _get_binary_path(hass)

    remote_metadata = await _async_fetch_remote_binary_metadata(hass, binary_url)
    if remote_metadata.status in (UPDATE_STATUS_FAILED, UPDATE_STATUS_UNKNOWN):
        return remote_metadata

    stored_metadata = await _async_get_binary_metadata(hass, etag_key)
    stored_etag = stored_metadata.get("etag")

    if (
        stored_etag
        and stored_etag == remote_metadata.remote_etag
        and _is_binary_ready(binary_path)
    ):
        _LOGGER.debug("Binary is up to date (ETag: %s)", stored_etag)
        return BinaryUpdateResult(
            status=UPDATE_STATUS_CURRENT,
            last_modified=remote_metadata.last_modified,
            remote_etag=remote_metadata.remote_etag,
        )

    _LOGGER.info(
        "Binary update required (stored ETag: %s, remote ETag: %s)",
        stored_etag,
        remote_metadata.remote_etag,
    )

    new_binary_path = await _download_binary(
        hass,
        force=True,
        expected_metadata={
            "etag": remote_metadata.remote_etag,
            "last_modified": remote_metadata.last_modified,
        },
    )
    if not new_binary_path:
        message = "Binary update download failed"
        _LOGGER.error(message)
        return BinaryUpdateResult(
            status=UPDATE_STATUS_FAILED,
            last_modified=remote_metadata.last_modified,
            remote_etag=remote_metadata.remote_etag,
            message=message,
        )

    for entry_id, data in hass.data.get(DOMAIN, {}).items():
        if not isinstance(data, dict):
            continue
        coordinator = data.get("coordinator")
        if coordinator and hasattr(coordinator, "_binary_path"):
            coordinator._binary_path = new_binary_path
            data["binary_path"] = new_binary_path

    _LOGGER.info("Binary updated successfully to %s", new_binary_path)
    return BinaryUpdateResult(
        status=UPDATE_STATUS_UPDATED,
        last_modified=remote_metadata.last_modified,
        remote_etag=remote_metadata.remote_etag,
    )


async def _check_binary_update(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Periodic 24h check — delegates to _check_and_update_binary."""
    try:
        await _check_and_update_binary(hass, entry)
    except Exception as err:
        _LOGGER.error("Error during scheduled binary update check: %s", err)


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
    hass: HomeAssistant,
    force: bool = False,
    expected_metadata: dict[str, Any] | None = None,
) -> str | None:
    """Download and extract the QMS binary ZIP.

    If force=False, skips download when the binary already exists and is executable.
    If force=True, always re-downloads (used for updates).
    Stores remote version metadata after a successful download.
    """
    binary_url, etag_key = _get_binary_url()

    binary_path = _get_binary_path(hass)
    binary_dir = binary_path.parent

    if not force and _is_binary_ready(binary_path):
        _LOGGER.debug("QMS binary already exists at %s", binary_path)
        return str(binary_path)

    session = async_get_clientsession(hass)
    zip_path = binary_dir / f"{BINARY_NAME}.zip"
    temp_binary_path = binary_dir / f".{BINARY_NAME}.tmp"

    try:
        async with session.get(binary_url) as resp:
            if resp.status != 200:
                _LOGGER.error("Failed to download ZIP from %s: %s", binary_url, resp.status)
                return None
            content = await resp.read()
            remote_etag = resp.headers.get("ETag") or resp.headers.get("Last-Modified")
            last_modified = resp.headers.get("Last-Modified")
            content_length = resp.headers.get("Content-Length")

        await hass.async_add_executor_job(zip_path.write_bytes, content)
        _LOGGER.debug("Downloaded QMS ZIP to %s", zip_path)

        def install_binary_from_zip() -> str:
            selected_member: zipfile.ZipInfo | None = None
            with zipfile.ZipFile(zip_path, "r") as zf:
                file_members = [member for member in zf.infolist() if not member.is_dir()]
                for member in file_members:
                    if Path(member.filename).name == BINARY_NAME:
                        selected_member = member
                        break

                if selected_member is None and len(file_members) == 1:
                    selected_member = file_members[0]

                if selected_member is None:
                    raise FileNotFoundError(f"No {BINARY_NAME} executable found in ZIP")

                if temp_binary_path.exists():
                    temp_binary_path.unlink()

                with zf.open(selected_member) as source, temp_binary_path.open("wb") as target:
                    shutil.copyfileobj(source, target)

            os.chmod(temp_binary_path, 0o755)
            os.replace(temp_binary_path, binary_path)
            return str(binary_path)

        installed_binary = await hass.async_add_executor_job(install_binary_from_zip)
        try:
            await hass.async_add_executor_job(zip_path.unlink)
        except FileNotFoundError:
            pass
        except Exception as err:
            _LOGGER.debug("Could not remove temporary ZIP %s: %s", zip_path, err)
        _LOGGER.info("QMS binary ready at %s", installed_binary)

        expected_metadata = expected_metadata or {}
        metadata_etag = remote_etag or expected_metadata.get("etag")
        metadata_last_modified = (
            last_modified or expected_metadata.get("last_modified")
        )
        if metadata_etag:
            try:
                await _async_store_binary_metadata(
                    hass,
                    etag_key,
                    {
                        "etag": metadata_etag,
                        "last_modified": metadata_last_modified,
                        "content_length": content_length,
                        "url": binary_url,
                        "path": installed_binary,
                        "updated_at": datetime.now(timezone.utc).isoformat(),
                    },
                )
            except Exception as err:
                _LOGGER.warning("Could not persist binary metadata: %s", err)

        return installed_binary

    except Exception as err:
        _LOGGER.error("Error downloading/extracting binary: %s", err)
        if zip_path.exists():
            await hass.async_add_executor_job(zip_path.unlink)
        if temp_binary_path.exists():
            await hass.async_add_executor_job(temp_binary_path.unlink)
        return None
