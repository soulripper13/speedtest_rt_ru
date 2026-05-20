"""The Speedtest RT.RU integration."""
import asyncio
import logging
import os
import platform
import shutil
import zipfile
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import (
    DOMAIN,
    BINARY_NAME,
    BINARY_URL_X86,
    BINARY_URL_ARM64,
    BINARY_DIR,
    BINARY_BUNDLED_DIR,
    BINARY_PLATFORM_X86,
    BINARY_PLATFORM_ARM64,
)
from .coordinator import SpeedtestCoordinator
from .www_manager import async_setup_cards, async_register_cards, async_remove_cards_and_resources

PLATFORMS = [Platform.SENSOR, Platform.BUTTON]

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Speedtest RT.RU from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # Use bundled binary when available; download only as a setup fallback.
    binary_path = await _ensure_binary(hass)
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

    # Listen for options changes
    entry.async_on_unload(entry.add_update_listener(async_options_updated))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
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


def _get_binary_platform() -> str:
    """Return the bundled binary platform directory for the current architecture."""
    machine = platform.machine()
    if machine in ("aarch64", "arm64"):
        return BINARY_PLATFORM_ARM64
    return BINARY_PLATFORM_X86


def _get_binary_url() -> str:
    """Return the download URL for the current architecture."""
    if _get_binary_platform() == BINARY_PLATFORM_ARM64:
        return BINARY_URL_ARM64
    return BINARY_URL_X86


def _get_binary_path(hass: HomeAssistant) -> Path:
    """Return the legacy downloaded binary path."""
    return Path(hass.config.path(BINARY_DIR)) / BINARY_NAME


def _get_bundled_binary_path(hass: HomeAssistant) -> Path:
    """Return the bundled binary path for the current architecture."""
    return (
        Path(hass.config.path(BINARY_DIR))
        / BINARY_BUNDLED_DIR
        / _get_binary_platform()
        / BINARY_NAME
    )


def _is_binary_ready(binary_path: Path) -> bool:
    """Return true when the binary exists and can be executed."""
    return (
        binary_path.is_file()
        and os.access(str(binary_path), os.X_OK)
    )


async def _ensure_binary(hass: HomeAssistant) -> str | None:
    """Return a usable QMS binary path.

    GitHub Actions keeps bundled binaries updated in the repository. The
    download fallback is only for old/manual installs that do not include one.
    """
    bundled_binary_path = _get_bundled_binary_path(hass)
    if bundled_binary_path.is_file():
        await hass.async_add_executor_job(os.chmod, bundled_binary_path, 0o755)
        _LOGGER.debug("Using bundled QMS binary at %s", bundled_binary_path)
        return str(bundled_binary_path)

    legacy_binary_path = _get_binary_path(hass)
    if _is_binary_ready(legacy_binary_path):
        _LOGGER.debug("Using legacy QMS binary at %s", legacy_binary_path)
        return str(legacy_binary_path)

    _LOGGER.warning(
        "Bundled QMS binary is missing for %s; downloading setup fallback",
        _get_binary_platform(),
    )
    return await _download_binary(hass)


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


async def _download_binary(hass: HomeAssistant) -> str | None:
    """Download and extract the QMS binary ZIP as a setup fallback."""
    binary_url = _get_binary_url()

    binary_path = _get_binary_path(hass)
    binary_dir = binary_path.parent

    if _is_binary_ready(binary_path):
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

        return installed_binary

    except Exception as err:
        _LOGGER.error("Error downloading/extracting binary: %s", err)
        if zip_path.exists():
            await hass.async_add_executor_job(zip_path.unlink)
        if temp_binary_path.exists():
            await hass.async_add_executor_job(temp_binary_path.unlink)
        return None
