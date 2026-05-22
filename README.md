# Speedtest RT.RU Integration for Home Assistant

[![HACS Default](https://img.shields.io/badge/HACS-Default-orange.svg?style=for-the-badge)](https://github.com/hacs/default)
[![GitHub Release](https://img.shields.io/github/release/soulripper13/speedtest_rt_ru.svg?style=for-the-badge)](https://github.com/soulripper13/speedtest_rt_ru/releases)
[![GitHub Issues](https://img.shields.io/github/issues/soulripper13/speedtest_rt_ru.svg?style=for-the-badge)](https://github.com/soulripper13/speedtest_rt_ru/issues)
![Downloads](https://img.shields.io/badge/dynamic/json?color=41BDF5&logo=home-assistant&label=Downloads&suffix=%20installs&cacheSeconds=15600&style=for-the-badge&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.speedtest_rt_ru.total)
[![Support Development](https://img.shields.io/badge/Support-Development-FF5E5B?style=for-the-badge&logo=ko-fi&logoColor=white)](https://ko-fi.com/soulripper13)
[![Support via PayPal](https://img.shields.io/badge/Support-PayPal-00457C?style=for-the-badge&logo=paypal&logoColor=white)](https://paypal.me/SKatoaroo)

<div align="center">
  <img src="icon.png" alt="Logo" width="120">
  <h3>Speedtest RT.RU for Home Assistant</h3>
  <p>A high-performance internet speed monitoring integration using the QMS binary from RT.RU.</p>
  
  <a href="https://my.home-assistant.io/redirect/hacs_repository/?owner=soulripper13&repository=speedtest_rt_ru&category=integration">
    <img src="https://my.home-assistant.io/badges/hacs_repository.svg" alt="Open in HACS">
  </a>
  <a href="https://my.home-assistant.io/redirect/config_flow_start/?domain=speedtest_rt_ru">
    <img src="https://my.home-assistant.io/badges/config_flow_start.svg" alt="Add Integration">
  </a>
</div>

---




## English

**Speedtest RT.RU** is a Home Assistant integration that automatically downloads and runs the QMS binary from [RT.RU](https://speedtest.rt.ru) to measure your internet speed.


It provides the following sensors and a button entity:
- **Download** – download speed in Mbps
- **Upload** – upload speed in Mbps
- **Ping** – idle network latency in milliseconds
- **Jitter** – network jitter in milliseconds
- **ISP** – your Internet Service Provider name
- **Server** – the speedtest server used
- **IP** – your public IP address
- **Result URL** – link to the full test result on qms.ru
- **Last Test** – timestamp of the last completed test
- **Run Speedtest** (button) – manually trigger a speed test
- 2 additional latency sensors: Download Ping and Upload Ping (disabled by default)

All entities are grouped under a single **Speedtest RT.RU** device for easy management.

### Features
- Bundled QMS speedtest binary with setup-time download fallback for manual installs
- **Bundled QMS binary updates** – repository workflow checks upstream QMS binaries and updates the packaged binaries by pull request
- **Server selection** – choose from available Russian speedtest servers or use automatic selection
- Configurable update interval through the Home Assistant UI or manual update
- **Button entity** – trigger speedtest directly from the UI
- **Lovelace cards** – two built-in cards (main + compact) auto-installed and registered on setup, removed on deletion
- **Bilingual cards** – cards support English and Russian (`language: "en"` or `"ru"`)
- **Diagnostics support** – troubleshoot issues via Settings > Integrations
- **Timeout protection** – tests automatically timeout after 300 seconds by default and can be adjusted in options
- Fully compatible with Home Assistant and HACS
- Works on **x86_64** and **ARM64 (aarch64)** systems
- Requires **Home Assistant 2024.1+**


### Installation

#### HACS installation (preferred)
1. Search and download this integration via **HACS**.
2. Restart Home Assistant.
3. Add the integration via **Settings → Devices & Services → Add Integration**.

#### Manual installation
1. Copy the `custom_components/speedtest_rt_ru` folder to your `config/custom_components` directory.
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration → Speedtest RT.RU**.
4. Configure the update interval or leave the default (30 minutes).


### Lovelace Cards

Two custom cards are automatically installed and registered when the integration is set up, and removed when the integration is deleted.

#### Main Card (`custom:speedtest-rt-ru-card`)
Full-featured card with dual radial gauges for download and upload, plus ping and jitter metrics, ISP name, server info, IP address, result link, and last test time.

```yaml
type: custom:speedtest-rt-ru-card
language: en   # or "ru" for Russian labels
entities:
  download: sensor.speedtest_rt_ru_download
  upload: sensor.speedtest_rt_ru_upload
  ping: sensor.speedtest_rt_ru_ping
  jitter: sensor.speedtest_rt_ru_jitter
  isp: sensor.speedtest_rt_ru_isp
  server: sensor.speedtest_rt_ru_server
  result_url: sensor.speedtest_rt_ru_result_url
  last_test: sensor.speedtest_rt_ru_last_test
  ip: sensor.speedtest_rt_ru_ip
max_download: 1000
max_upload: 500
```

#### Compact Card (`custom:speedtest-rt-ru-compact`)
Minimalist single-row pill card — great for side panels and compact dashboards.

```yaml
type: custom:speedtest-rt-ru-compact
language: en   # or "ru" for Russian labels
entities:
  download: sensor.speedtest_rt_ru_download
  upload: sensor.speedtest_rt_ru_upload
  ping: sensor.speedtest_rt_ru_ping
```

Both cards have a visual editor accessible from the Lovelace card picker.


### Usage

After setup, the following sensors and one button are grouped under a "Speedtest RT.RU" device:
- `sensor.speedtest_rt_ru_download`
- `sensor.speedtest_rt_ru_upload`
- `sensor.speedtest_rt_ru_ping`
- `sensor.speedtest_rt_ru_jitter`
- `sensor.speedtest_rt_ru_isp`
- `sensor.speedtest_rt_ru_server`
- `sensor.speedtest_rt_ru_ip`
- `sensor.speedtest_rt_ru_result_url`
- `sensor.speedtest_rt_ru_last_test`
- `button.speedtest_rt_ru_run_speedtest`

Additional latency sensors (disabled by default, enable in entity settings):
- `sensor.speedtest_rt_ru_ping_during_download` — latency measured during the download phase
- `sensor.speedtest_rt_ru_ping_during_upload` — latency measured during the upload phase

Use them in automations, Lovelace dashboards, or for monitoring your internet connection.

#### Server Selection
1. Go to **Settings → Devices & Services**.
2. Find your Speedtest RT.RU integration.
3. Click ⚙️ **Configure**.
4. Select a server from the **Test Server** dropdown:
   - **Auto (Best Server)** – automatically selects the best server
   - Or choose a specific server by city (e.g., "Хабаровск - khabarovsk1.qms.ru")
5. Save. The integration reloads automatically.

#### Manual Speed Test

**Option 1: Button Entity (recommended)**
Press the "Run Speedtest" button in your device dashboard or Lovelace card.

**Option 2: Service Call**
The integration exposes the service `speedtest_rt_ru.perform_test`:
1. Go to **Developer Tools → Services**.
2. Select `speedtest_rt_ru.perform_test`.
3. Call the service (no parameters required).

#### Binary Updates
QMS binary updates are handled by a GitHub Actions workflow in this repository. The workflow checks the upstream RT.RU binaries, updates the packaged `qms_lib` files when they change, and opens a pull request.

#### Disable Automatic Speedtest Updates
1. Go to **Settings → Devices & Services**.
2. Find your Speedtest RT.RU integration.
3. Click ⚙️ **Configure**.
4. Disable "Enable Automatic Updates" or set a high scan interval.
5. Save.

Sensors will then update only when the service is manually triggered or the button is pressed.

#### Diagnostics
1. Go to **Settings → Devices & Services**.
2. Find your Speedtest RT.RU integration.
3. Click ⋮ and select **Download diagnostics**.


### Troubleshooting
- **`Exec format error`** → Your system architecture is not supported. Only **x86_64** and **ARM64 (aarch64)** are supported.
- **Binary download fails** → Check that [speedtest.rt.ru](https://speedtest.rt.ru) and `lib.qms.ru` are reachable from your HA host.
- **Test hangs** → Tests automatically time out after 300 seconds by default. Increase "Speedtest Timeout" in integration options if your server needs longer.
- **Cards not appearing** → Go to **Settings → Devices & Services**, find the integration, and restart HA. Cards are registered automatically on setup.
- Logs are available under **Settings → System → Logs**.

---
## Support the Project

This project is developed and maintained in spare time and is provided free to the community.

If you find it useful and would like to support ongoing development, maintenance, and improvements, any contribution is appreciated — but never required ❤️

### Ways to Support

* **Ko-fi**
  [https://ko-fi.com/soulripper13](https://ko-fi.com/soulripper13)

* **PayPal**
  [https://paypal.me/SKatoaroo](https://paypal.me/SKatoaroo)

* **Bitcoin (BTC)**
  `bc1qvu8a9gdy3dcxa94jge7d3rd7claapsydjsjxn0`

* **Solana (SOL)**
  `4jvCR2YFQLqguoyz9qAMPzVbaEcDsG5nzRHFG8SeaeBK`

You can also help by:

* Reporting bugs
* Submitting pull requests
* Suggesting features
* Helping other users
* Starring the repository ⭐

Thank you for being part of the community.
