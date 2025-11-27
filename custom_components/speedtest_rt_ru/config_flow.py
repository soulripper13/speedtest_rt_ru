"""Config flow for Speedtest RT.RU integration."""
import logging
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
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_AUTO_UPDATE,
    DEFAULT_SERVER_ID,
)

_LOGGER = logging.getLogger(__name__)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Speedtest RT.RU."""

    VERSION = 1

    @staticmethod
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return OptionsFlowHandler(config_entry)

    async def async_step_user(
        self, user_input: dict[str, any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            return self.async_create_entry(title="Speedtest RT.RU", data=user_input)

        # Get available servers (binary might not exist yet, so fallback to auto only)
        from . import get_available_servers
        from pathlib import Path

        binary_path = Path(self.hass.config.path("custom_components/speedtest_rt_ru/qms_lib"))
        servers = {"auto": "Auto (Best Server)"}

        if binary_path.exists():
            try:
                servers = await get_available_servers(str(binary_path))
            except Exception:
                _LOGGER.debug("Could not fetch servers, using auto only")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_SERVER_ID,
                        default=DEFAULT_SERVER_ID,
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=[{"value": k, "label": v} for k, v in servers.items()],
                            mode=SelectSelectorMode.DROPDOWN,
                        )
                    ),
                    vol.Optional(
                        CONF_SCAN_INTERVAL,
                        description={"suggested_value": DEFAULT_SCAN_INTERVAL},
                    ): int,
                    vol.Optional(
                        CONF_AUTO_UPDATE, default=DEFAULT_AUTO_UPDATE
                    ): bool,
                }
            ),
        )

class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Speedtest RT.RU options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, any] | None = None
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

        # Get available servers
        from . import get_available_servers
        from pathlib import Path

        binary_path = Path(self.hass.config.path("custom_components/speedtest_rt_ru/qms_lib"))
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
                }
            ),
            description_placeholders={
                "auto_update_desc": "Enable automatic updates at the interval below, or disable for manual-only (use service to trigger)."
            },
        )
