"""DataUpdateCoordinator for Speedtest RT.RU."""
from __future__ import annotations

import asyncio
import logging
import os
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
    CONF_TEST_TIMEOUT,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SERVER_ID,
    DEFAULT_TEST_TIMEOUT,
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
ANSI_ESCAPE_RE = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")
DEFAULT_SUBPROCESS_PATH = "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"


def _coerce_timeout(value: Any) -> int:
    """Return a usable speedtest timeout in seconds."""
    try:
        timeout = int(value)
    except (TypeError, ValueError):
        return DEFAULT_TEST_TIMEOUT

    return max(60, min(timeout, 900))


async def _terminate_process(proc: asyncio.subprocess.Process) -> None:
    """Terminate a subprocess and wait briefly for it to exit."""
    if proc.returncode is not None:
        return

    proc.kill()
    try:
        await asyncio.wait_for(proc.wait(), timeout=5)
    except asyncio.TimeoutError:
        _LOGGER.warning("Timed out waiting for QMS process to exit after kill")


def _decode_output(output: bytes) -> str:
    """Decode and normalize QMS terminal output."""
    text = output.decode("utf-8", errors="ignore")
    text = ANSI_ESCAPE_RE.sub("", text)
    text = text.replace("\r", "\n")
    return text.strip()


def _subprocess_env() -> dict[str, str]:
    """Return an environment suitable for running the QMS binary."""
    env = dict(os.environ)
    existing_path = env.get("PATH")
    if existing_path:
        env["PATH"] = f"{existing_path}:{DEFAULT_SUBPROCESS_PATH}"
    else:
        env["PATH"] = DEFAULT_SUBPROCESS_PATH

    return env


def _qms_error_message(returncode: int, output: str) -> str:
    """Return a concise UpdateFailed message for QMS failures."""
    qms_error = re.search(r"QMS Error:\s*\"?([^\"\n]+)\"?", output)
    detail = f'QMS Error: "{qms_error.group(1)}"' if qms_error else output[-500:]

    if "Ping error" in output:
        return (
            "QMS failed during latency check with \"Ping error\". "
            "This usually means the Home Assistant runtime cannot execute ping "
            "or cannot reach the selected QMS latency endpoint. "
            f"QMS exited with code {returncode}: {detail}"
        )

    return f"QMS exited with code {returncode}: {detail}"


class SpeedtestCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Coordinator for Speedtest RT.RU."""

    def __init__(
        self, hass: HomeAssistant, entry: ConfigEntry, binary_path: str
    ) -> None:
        """Initialize the coordinator."""
        self._binary_path = binary_path
        self.entry = entry

        # Get settings from options or initial config data.
        options = entry.options
        self._server_id = options.get(
            CONF_SERVER_ID,
            entry.data.get(CONF_SERVER_ID, DEFAULT_SERVER_ID)
        )
        self._test_timeout = _coerce_timeout(options.get(
            CONF_TEST_TIMEOUT,
            entry.data.get(CONF_TEST_TIMEOUT, DEFAULT_TEST_TIMEOUT)
        ))

        # Set update interval based on options (no polling if auto_update=False)
        auto_update = options.get(
            CONF_AUTO_UPDATE,
            entry.data.get(CONF_AUTO_UPDATE, True)
        )
        interval = timedelta(
            seconds=options.get(
                CONF_SCAN_INTERVAL,
                entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
            )
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
            cmd_args = self._build_speedtest_args(self._server_id)
            returncode, output = await self._async_run_qms_command(cmd_args)

            if returncode not in (0, None):
                if (
                    (not self._server_id or self._server_id == "auto")
                    and "Ping error" in output
                ):
                    fallback_server_id = await self._async_get_fallback_server_id()
                    if fallback_server_id:
                        _LOGGER.warning(
                            "QMS auto server latency check failed; retrying with "
                            "server ID %s",
                            fallback_server_id,
                        )
                        cmd_args = self._build_speedtest_args(fallback_server_id)
                        returncode, output = await self._async_run_qms_command(
                            cmd_args
                        )

                if returncode not in (0, None):
                    raise UpdateFailed(_qms_error_message(returncode, output))

            # Parse with regex (English labels from QMS binary)
            data = self._parse_output(output)
            if data[ATTR_DOWNLOAD] == "unknown" and data[ATTR_UPLOAD] == "unknown":
                _LOGGER.debug("Unable to parse QMS output: %r", output)
                raise UpdateFailed("Speedtest output did not contain speed results")

            data[ATTR_DATE_LAST_TEST] = datetime.now(timezone.utc)
            return data

        except UpdateFailed:
            raise
        except Exception as err:
            _LOGGER.error("Error running QMS binary: %s", err)
            raise UpdateFailed(f"Failed to update: {err}") from err

    def _build_speedtest_args(self, server_id: str | None) -> list[str]:
        """Build QMS speedtest command arguments."""
        cmd_args = [self._binary_path]
        if server_id and server_id != "auto":
            cmd_args.extend(["-S", server_id])
        else:
            cmd_args.append("-s")

        cmd_args.append("-P")
        return cmd_args

    async def _async_run_qms_command(
        self,
        cmd_args: list[str],
        timeout: int | None = None,
    ) -> tuple[int | None, str]:
        """Run QMS and return its return code and normalized output."""
        _LOGGER.debug("Running QMS command: %s", cmd_args)

        proc = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            stdin=asyncio.subprocess.DEVNULL,
            env=_subprocess_env(),
        )

        try:
            stdout, stderr = await asyncio.wait_for(
                proc.communicate(), timeout=timeout or self._test_timeout
            )
        except asyncio.TimeoutError:
            await _terminate_process(proc)
            raise UpdateFailed(
                f"Speedtest timed out after {timeout or self._test_timeout} seconds"
            )

        stdout_text = _decode_output(stdout)
        stderr_text = _decode_output(stderr)
        output = "\n".join(
            part for part in (stdout_text, stderr_text) if part
        ).strip()

        _LOGGER.debug("QMS Raw Output: %s", output)
        return proc.returncode, output

    async def _async_get_fallback_server_id(self) -> str | None:
        """Return the first server ID from QMS server list."""
        returncode, output = await self._async_run_qms_command(
            [self._binary_path, "-L", "-P"],
            timeout=min(self._test_timeout, 60),
        )
        if returncode not in (0, None):
            _LOGGER.warning(
                "Could not fetch QMS fallback server list: %s",
                _qms_error_message(returncode, output),
            )
            return None

        for line in output.splitlines():
            match = re.match(r"\s*(\d+)\s+\S+", line)
            if match:
                return match.group(1)

        _LOGGER.warning("QMS server list did not contain a fallback server ID")
        return None

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
            ATTR_UPLOAD_LATENCY_IQM: "unknown",
        }

        # Regex patterns matching actual QMS binary output format
        patterns = {
            ATTR_PING: r"Idle Latency:\s*(\d+(?:\.\d+)?)\s*ms\b",
            ATTR_JITTER: r"Idle Latency:.*?Jitter:\s*(\d+(?:\.\d+)?)\s*ms\b",
            ATTR_DOWNLOAD: r"Download:\s*(\d+(?:\.\d+)?)\s*Mbit\s*/\s*s",
            ATTR_UPLOAD: r"Upload:\s*(\d+(?:\.\d+)?)\s*Mbit\s*/\s*s",
            ATTR_ISP: r"ISP:\s*([^\n]+)",
            ATTR_SERVER: r"Server:\s*([^\n]+)",
            ATTR_IP: r"IP:\s*([^\n]+)",
            ATTR_RESULT_URL: r"Result:\s*(https?://\S+)",
            ATTR_DOWNLOAD_LATENCY_IQM: r"Download:.*?Latency:\s*(\d+(?:\.\d+)?)\s*ms\b",
            ATTR_UPLOAD_LATENCY_IQM: r"Upload:.*?Latency:\s*(\d+(?:\.\d+)?)\s*ms\b",
        }

        for attr, pattern in patterns.items():
            match = re.search(pattern, output, re.IGNORECASE | re.MULTILINE)
            if match:
                data[attr] = match.group(1).strip()

        return data
