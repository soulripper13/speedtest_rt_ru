"""Manager for Lovelace card resources."""

import logging
import os
import shutil
import stat
from pathlib import Path

from homeassistant.components.lovelace import DOMAIN as LOVELACE_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.event import async_call_later

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

VERSION = "1.1.0"

CARDS = [
    "speedtest-rt-ru-card.js",
    "speedtest-rt-ru-compact.js",
]

WWW_SOURCE_DIR = Path(__file__).parent / "www"


async def async_setup_cards(hass: HomeAssistant) -> bool:
    """Set up the custom cards by copying to www folder.

    This ensures cards are accessible at /local/speedtest_rt_ru/
    """
    try:
        www_dir = Path(hass.config.path("www"))
        target_dir = www_dir / "speedtest_rt_ru"

        if not www_dir.exists():
            _LOGGER.info("Creating www directory")
            await hass.async_add_executor_job(www_dir.mkdir)

        if not target_dir.exists():
            await hass.async_add_executor_job(target_dir.mkdir)

        copied_count = 0
        for card in CARDS:
            source = WWW_SOURCE_DIR / card
            target = target_dir / card

            if source.exists():
                await hass.async_add_executor_job(shutil.copy2, source, target)

                def set_permissions(t=target):
                    try:
                        os.chmod(t, stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IROTH)
                    except OSError as e:
                        _LOGGER.warning("Could not set permissions for %s: %s", t, e)

                await hass.async_add_executor_job(set_permissions)
                copied_count += 1

        _LOGGER.debug(
            "Speedtest RT.RU cards installed to www folder (%d files)",
            copied_count,
        )
        return True

    except Exception as e:
        _LOGGER.error("Failed to set up cards: %s", e)
        return False


async def async_remove_cards_and_resources(hass: HomeAssistant) -> None:
    """Remove cards from www folder and unregister resources."""
    try:
        www_dir = Path(hass.config.path("www"))
        target_dir = www_dir / "speedtest_rt_ru"

        if target_dir.exists():
            _LOGGER.info("Removing Speedtest RT.RU cards from www directory")
            await hass.async_add_executor_job(shutil.rmtree, target_dir)

        lovelace = hass.data.get(LOVELACE_DOMAIN)
        if lovelace and hasattr(lovelace, "resources") and lovelace.resources.loaded:
            resources = lovelace.resources

            for card in CARDS:
                base_url = f"/local/speedtest_rt_ru/{card}"

                found_resource = None
                for resource in resources.async_items():
                    if resource["url"].split("?")[0] == base_url:
                        found_resource = resource
                        break

                if found_resource:
                    _LOGGER.info("Unregistering Lovelace resource: %s", base_url)
                    await resources.async_delete_item(found_resource["id"])

    except Exception as e:
        _LOGGER.error("Failed to remove cards/resources: %s", e)


async def async_register_cards(hass: HomeAssistant) -> None:
    """Register Lovelace resources safely."""
    lovelace = hass.data.get(LOVELACE_DOMAIN)

    if not lovelace:
        _LOGGER.debug("Lovelace not loaded, skipping resource registration")
        return

    if not getattr(lovelace, "resources", None) or not lovelace.resources.loaded:
        _LOGGER.debug("Lovelace resources not loaded, retrying in 5 seconds")
        async_call_later(hass, 5, lambda _: hass.async_create_task(async_register_cards(hass)))
        return

    resources = lovelace.resources

    for card in CARDS:
        base_url = f"/local/speedtest_rt_ru/{card}"
        full_url = f"{base_url}?v={VERSION}"

        found_resource = None
        for resource in resources.async_items():
            if resource["url"].split("?")[0] == base_url:
                found_resource = resource
                break

        if found_resource:
            if found_resource["url"] != full_url:
                _LOGGER.info("Updating Lovelace resource %s to version %s", base_url, VERSION)
                try:
                    await resources.async_update_item(found_resource["id"], {
                        "res_type": "module",
                        "url": full_url
                    })
                except Exception as e:
                    _LOGGER.error("Failed to update resource %s: %s", base_url, e)
        else:
            _LOGGER.info("Auto-registering Lovelace resource: %s", full_url)
            try:
                await resources.async_create_item({
                    "res_type": "module",
                    "url": full_url
                })
            except Exception as e:
                _LOGGER.error("Failed to register %s: %s", full_url, e)
