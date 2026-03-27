"""DataUpdateCoordinator for Speedtest RT.RU."""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .const import (
    DOMAIN,
    CONF_AUTO_UPDATE,
    CONF_SCAN_INTERVAL,
    CONF_SERVER_ID,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SERVER_ID,
    ATTR_DOWNLOAD,
    ATTR_UPLOAD,
    ATTR_PING,
    ATTR_JITTER,
    ATTR_ISP,
    ATTR_SERVER,
    ATTR_RESULT_URL,
    ATTR_DATE_LAST_TEST,
    ATTR_IP,
    ATTR_DOWNLOAD_LATENCY_IQM,
    ATTR_DOWNLOAD_LATENCY_LOW,
    ATTR_DOWNLOAD_LATENCY_HIGH,
    ATTR_DOWNLOAD_LATENCY_JITTER,
    ATTR_UPLOAD_LATENCY_IQM,
    ATTR_UPLOAD_LATENCY_LOW,
    ATTR_UPLOAD_LATENCY_HIGH,
    ATTR_UPLOAD_LATENCY_JITTER,
)

_LOGGER = logging.getLogger(__name__)


class SpeedtestCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for Speedtest RT.RU."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, binary_path: str
    ) -> None:
        """Initialize the coordinator."""
        self._binary_path = binary_path
        self.entry = entry

        # Get server_id from options or data
        options = entry.options
        self._server_id = options.get(
            CONF_SERVER_ID,
            entry.data.get(CONF_SERVER_ID, DEFAULT_SERVER_ID)
        )

        # Set update interval based on options (no polling if auto_update=False)
        auto_update = options.get(CONF_AUTO_UPDATE, True)
        interval = timedelta(
            seconds=options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        ) if auto_update else None

        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=interval,
        )

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from QMS binary."""
        try:
            # Build command arguments
            cmd_args = [self._binary_path]

            # Add server selection if not "auto"
            if self._server_id and self._server_id != "auto":
                cmd_args.extend(["-S", self._server_id])

            proc = await asyncio.create_subprocess_exec(
                *cmd_args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=120
                )
            except asyncio.TimeoutError:
                proc.kill()
                await proc.wait()
                raise UpdateFailed("Speedtest timed out after 120 seconds")

            output = stdout.decode("utf-8", errors="ignore").strip()

            _LOGGER.debug("QMS Raw Output: %s", output)
            if stderr:
                _LOGGER.debug("QMS Stderr: %s", stderr.decode("utf-8", errors="ignore"))

            # Parse with regex (English labels from QMS binary)
            data = self._parse_output(output)
            data[ATTR_DATE_LAST_TEST] = datetime.now(timezone.utc)
            return data

        except UpdateFailed:
            raise
        except Exception as err:
            _LOGGER.error("Error running QMS binary: %s", err)
            raise UpdateFailed(f"Failed to update: {err}") from err

    def _parse_output(self, output: str) -> dict[str, str]:
        """Parse QMS binary output."""
        data = {
            ATTR_DOWNLOAD: "unknown",
            ATTR_UPLOAD: "unknown",
            ATTR_PING: "unknown",
            ATTR_JITTER: "unknown",
            ATTR_ISP: "unknown",
            ATTR_SERVER: "unknown",
            ATTR_RESULT_URL: "unknown",
            ATTR_IP: "unknown",
            ATTR_DOWNLOAD_LATENCY_IQM: "unknown",
            ATTR_DOWNLOAD_LATENCY_LOW: "unknown",
            ATTR_DOWNLOAD_LATENCY_HIGH: "unknown",
            ATTR_DOWNLOAD_LATENCY_JITTER: "unknown",
            ATTR_UPLOAD_LATENCY_IQM: "unknown",
            ATTR_UPLOAD_LATENCY_LOW: "unknown",
            ATTR_UPLOAD_LATENCY_HIGH: "unknown",
            ATTR_UPLOAD_LATENCY_JITTER: "unknown",
        }

        # Regex patterns matching actual QMS binary output format
        patterns = {
            ATTR_PING: r"^Ping:\s*(\d+(?:\.\d+)?)",
            ATTR_JITTER: r"Jitter:\s*(\d+(?:\.\d+)?)",
            ATTR_DOWNLOAD: r"Download:\s*(\d+(?:\.\d+)?)\s*Mbit/s",
            ATTR_UPLOAD: r"Upload:\s*(\d+(?:\.\d+)?)\s*Mbit/s",
            ATTR_ISP: r"ISP:\s*([^\n]+)",
            ATTR_SERVER: r"Server:\s*([^\n]+)",
            ATTR_IP: r"IP:\s*([\d\.]+)",
            ATTR_RESULT_URL: r"Result:\s*(https?://\S+)",
            # Download latency stats from "Ping download: count: N, min X, max Y, mean Z, median M, iqr I, iqm Q"
            ATTR_DOWNLOAD_LATENCY_IQM: r"Ping download:.*?\biqm\s+(\d+(?:\.\d+)?)",
            ATTR_DOWNLOAD_LATENCY_LOW: r"Ping download:.*?\bmin\s+(\d+(?:\.\d+)?)",
            ATTR_DOWNLOAD_LATENCY_HIGH: r"Ping download:.*?\bmax\s+(\d+(?:\.\d+)?)",
            ATTR_DOWNLOAD_LATENCY_JITTER: r"Ping download:.*?\biqr\s+(\d+(?:\.\d+)?)",
            # Upload latency stats from "Ping upload: count: N, min X, max Y, mean Z, median M, iqr I, iqm Q"
            ATTR_UPLOAD_LATENCY_IQM: r"Ping upload:.*?\biqm\s+(\d+(?:\.\d+)?)",
            ATTR_UPLOAD_LATENCY_LOW: r"Ping upload:.*?\bmin\s+(\d+(?:\.\d+)?)",
            ATTR_UPLOAD_LATENCY_HIGH: r"Ping upload:.*?\bmax\s+(\d+(?:\.\d+)?)",
            ATTR_UPLOAD_LATENCY_JITTER: r"Ping upload:.*?\biqr\s+(\d+(?:\.\d+)?)",
        }

        for attr, pattern in patterns.items():
            match = re.search(pattern, output, re.IGNORECASE | re.MULTILINE)
            if match:
                data[attr] = match.group(1).strip()

        return data
