"""Config flow for Speedtest RT.RU integration."""
from __future__ import annotations

import logging
import platform
from pathlib import Path
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    SelectSelector,
    SelectSelectorConfig,
    SelectSelectorMode,
)

from .const import (
    DOMAIN,
    CONF_SCAN_INTERVAL,
    CONF_AUTO_UPDATE,
    CONF_SERVER_ID,
    CONF_TEST_TIMEOUT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_AUTO_UPDATE,
    DEFAULT_SERVER_ID,
    DEFAULT_TEST_TIMEOUT,
    BINARY_DIR,
    BINARY_NAME,
    BINARY_BUNDLED_DIR,
    BINARY_PLATFORM_X86,
    BINARY_PLATFORM_ARM64,
)

_LOGGER = logging.getLogger(__name__)


def _get_binary_platform() -> str:
    """Return the bundled binary platform directory for the current architecture."""
    machine = platform.machine()
    if machine in ("aarch64", "arm64"):
        return BINARY_PLATFORM_ARM64
    return BINARY_PLATFORM_X86


def _get_options_binary_path(hass) -> Path:
    """Return the best available binary path for options server discovery."""
    integration_dir = Path(hass.config.path(BINARY_DIR))
    bundled_path = (
        integration_dir
        / BINARY_BUNDLED_DIR
        / _get_binary_platform()
        / BINARY_NAME
    )
    if bundled_path.exists():
        return bundled_path

    return integration_dir / BINARY_NAME


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Speedtest RT.RU."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return OptionsFlowHandler()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title="Speedtest RT.RU", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        description={"suggested_value": DEFAULT_SCAN_INTERVAL},
                    ): int,
                    vol.Optional(
                        CONF_AUTO_UPDATE, default=DEFAULT_AUTO_UPDATE
                    ): bool,
                    vol.Optional(
                        CONF_TEST_TIMEOUT,
                        description={"suggested_value": DEFAULT_TEST_TIMEOUT},
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=60,
                            max=900,
                            unit_of_measurement="seconds",
                        )
                    ),
                }
            ),
        )

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Speedtest RT.RU options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Get current values
        scan_interval = self.config_entry.options.get(
            CONF_SCAN_INTERVAL,
            self.config_entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        )
        auto_update = self.config_entry.options.get(
            CONF_AUTO_UPDATE,
            self.config_entry.data.get(CONF_AUTO_UPDATE, DEFAULT_AUTO_UPDATE)
        )
        server_id = self.config_entry.options.get(
            CONF_SERVER_ID,
            self.config_entry.data.get(CONF_SERVER_ID, DEFAULT_SERVER_ID)
        )
        test_timeout = self.config_entry.options.get(
            CONF_TEST_TIMEOUT,
            self.config_entry.data.get(CONF_TEST_TIMEOUT, DEFAULT_TEST_TIMEOUT)
        )

        # Get available servers
        from . import get_available_servers

        binary_path = _get_options_binary_path(self.hass)
        servers = {"auto": "Auto (Best Server)"}

        if binary_path.exists():
            try:
                servers = await get_available_servers(str(binary_path))
            except Exception:
                _LOGGER.debug("Could not fetch servers, using auto only")

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SERVER_ID,
                        description={"suggested_value": server_id},
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=[{"value": k, "label": v} for k, v in servers.items()],
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        description={"suggested_value": scan_interval},
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=60,
                            max=86400,
                            unit_of_measurement="seconds",
                        )
                    ),
                    vol.Optional(
                        CONF_AUTO_UPDATE, default=auto_update
                    ): bool,
                    vol.Optional(
                        CONF_TEST_TIMEOUT,
                        description={"suggested_value": test_timeout},
                    ): NumberSelector(
                        NumberSelectorConfig(
                            min=60,
                            max=900,
                            unit_of_measurement="seconds",
                        )
                    ),
                }
            ),
            description_placeholders={
                "auto_update_desc": "Enable automatic updates at the interval below, or disable for manual-only (use service to trigger)."
            },
        )
