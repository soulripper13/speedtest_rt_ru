# Check for Update Button — Design Spec

**Date:** 2026-04-29

## Summary

Add a "Check for Update" button entity to the Speedtest RT.RU integration. When pressed, it checks whether a newer `qms_lib` binary is available, downloads it if so, and fires a persistent HA notification with the result.

## Architecture

### New: `CheckUpdateButton` in `button.py`

A new `ButtonEntity` class added alongside the existing `SpeedtestButton`. Registered via `async_setup_entry` in the same file.

**`async_press` flow:**
1. Calls the shared helper `_check_and_update_binary(hass, entry)`
2. Displays a persistent notification based on the result:
   - No update: *"No new update available"*
   - Update found and applied: *"New update available — last modified: 2026-04-20"*

The notification uses a fixed `notification_id` (`speedtest_rt_ru_update`) so repeated presses replace the previous notification instead of stacking.

### Refactor: `_check_and_update_binary` helper in `__init__.py`

Extract the core update logic from `_check_binary_update` into a reusable function:

```python
async def _check_and_update_binary(
    hass: HomeAssistant, entry: ConfigEntry
) -> tuple[bool, str | None]:
    """Check for and apply binary update.

    Returns (was_updated, last_modified_str).
    was_updated=True means a new binary was downloaded and applied.
    last_modified_str is the Last-Modified header value from the server, or None.
    """
```

Both callers use this helper:
- **24h scheduled check** (`_check_binary_update`): calls helper, logs result, no notification
- **Button press** (`CheckUpdateButton.async_press`): calls helper, fires persistent notification

### Entity details

| Property | Value |
|---|---|
| `_attr_name` | `"Check for Update"` |
| `_attr_icon` | `"mdi:update"` |
| `_attr_unique_id` | `"{entry_id}_check_update"` |
| Device | Same `DeviceInfo` as `SpeedtestButton` |

## Data Flow

```
Button pressed
  → _check_and_update_binary(hass, entry)
      → HEAD request to binary URL
      → Compare Last-Modified with hass.data[DOMAIN][etag_key]
      → If changed: _download_binary(force=True)
                    update coordinator._binary_path
                    store new Last-Modified
      → Return (was_updated, last_modified_str)
  → persistent_notification.async_create(...)
```

## Error Handling

- If the HEAD request fails or returns non-200: notification → *"Update check failed"*
- If download fails after a detected update: notification → *"Update download failed"*
- All errors also logged at `ERROR` level

## Out of Scope

- No new sensor or state tracking for update availability
- No version pinning or rollback
- No changes to the existing 24h auto-update scheduler behavior
