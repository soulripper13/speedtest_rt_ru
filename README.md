# Speedtest RT.RU Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom%20integration-yellow.svg)](https://github.com/hacs/integration)
[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

Home Assistant integration for measuring internet speed using RT.RU's QMS binary.

![Logo](icon.png)

---

## English

**Speedtest RT.RU** is a Home Assistant integration that automatically downloads and runs the QMS binary from [RT.RU](https://speedtest.rt.ru) to measure your internet speed.  
It provides six sensors:
- **Download** – download speed in Mbps  
- **Upload** – upload speed in Mbps  
- **Ping** – network latency in milliseconds  
- **Jitter** – network jitter in milliseconds  
- **ISP** – your Internet Service Provider name  
- **Server** – the speedtest server used  

### Features
- Automatic download of the QMS speedtest binary on setup  
- Configurable update interval through the Home Assistant UI or manual update  
- Fully compatible with Home Assistant and HACS  
- Works only on **x86_64** systems  
- Requires **Home Assistant 2025.11+**

---

### Installation

#### Manual installation
1. Copy the `custom_components/speedtest_rt_ru` folder to your Home Assistant `config/custom_components` directory.  
2. Restart Home Assistant.  
3. Go to **Settings → Devices & Services → Add Integration → Speedtest RT.RU**.  
4. Configure update interval or leave the default.

#### HACS installation (preferred)
1. Add this repository to HACS as a **Custom Repository** (type: integration).  
2. Download and install **Speedtest RT.RU** via HACS.  
3. Restart Home Assistant.  
4. Add the integration via the UI:  
   **Settings → Devices & Services → Add Integration → Speedtest RT.RU**.

Or simply click:

[![Open HACS Repository][hacs-repo-badge]][hacs-repo]  
[![Add Integration][config-flow-badge]][config-flow]

---

### Usage

After setup, you will see six sensors (entity IDs may include the domain prefix, e.g. `sensor.speedtest_rt_ru_download`):

- `sensor.download`  
- `sensor.upload`  
- `sensor.ping`  
- `sensor.jitter`  
- `sensor.isp`  
- `sensor.server`

You can use them in automations, Lovelace dashboards, or for monitoring your internet connection.

The integration also exposes a service:  
`speedtest_rt_ru.perform_test`  
You can call it manually to trigger a speed test and update all sensors.

To call the service:
1. Go to **Developer Tools → Services**.  
2. Select `speedtest_rt_ru.perform_test` from the dropdown.  
3. Call the service (no parameters required).

If you prefer to disable automatic polling:
- Go to **Settings → Devices & Services**.  
- Find your Speedtest RT.RU integration.  
- Click ⚙️ **Configure**.  
- Disable “Enable polling” or set a high scan interval (e.g., never).  
- Save changes.  
Now sensors update only when the service is manually triggered.

---

### Troubleshooting

- **`Exec format error`** → Ensure your system architecture is **x86_64**.  
- **Binary download fails** → Verify [speedtest.rt.ru](https://speedtest.rt.ru) is reachable.  
- Logs are available under **Settings → System → Logs**.

---

## Русский

**Speedtest RT.RU** — интеграция для Home Assistant, автоматически загружающая и запускающая бинарник QMS с [RT.RU](https://speedtest.rt.ru) для измерения скорости интернета.  
Интеграция предоставляет шесть сенсоров:
- **Скорость загрузки** – в Мбит/с  
- **Скорость отдачи** – в Мбит/с  
- **Ping** – задержка сети в миллисекундах  
- **Jitter** – джиттер сети в миллисекундах  
- **ISP** – название вашего интернет-провайдера  
- **Server** – используемый сервер Speedtest  

### Возможности
- Автоматическая загрузка бинарника QMS при установке  
- Настраиваемый интервал обновления через UI Home Assistant  
- Полная совместимость с Home Assistant и HACS  
- Работает только на **x86_64** системах  
- Требует **Home Assistant 2025.11+**

---

### Установка

#### Ручная установка
1. Скопируйте папку `custom_components/speedtest_rt_ru` в `config/custom_components` вашего Home Assistant.  
2. Перезапустите Home Assistant.  
3. Перейдите в **Настройки → Устройства и Сервисы → Добавить интеграцию → Speedtest RT.RU**.  
4. Настройте интервал обновления.

#### Установка через HACS
1. Добавьте репозиторий в HACS как **пользовательскую интеграцию**.  
2. Установите через HACS.  
3. Добавьте интеграцию через UI.  

---

### Использование

После установки будут доступны шесть сенсоров (ID сущностей могут включать префикс домена, напр. `sensor.speedtest_rt_ru_download`):

- `sensor.download`  
- `sensor.upload`  
- `sensor.ping`  
- `sensor.jitter`  
- `sensor.isp`  
- `sensor.server`

Можно использовать в автоматизациях, Lovelace-дэшбордах и для мониторинга соединения.

Для ручного запуска теста скорости используйте сервис  
`speedtest_rt_ru.perform_test`  
(через **Инструменты разработчика → Сервисы**).

---

### Устранение неполадок
- Ошибка **`Exec format error`** → убедитесь, что используется архитектура **x86_64**.  
- Проблемы со скачиванием → проверьте доступность [speedtest.rt.ru](https://speedtest.rt.ru).  
- Логи доступны в **Настройки → Система → Журналы**.

---

## Links and Credits

- [RT.RU Speedtest](https://speedtest.rt.ru)  
- [Home Assistant](https://www.home-assistant.io)  
- [HACS Integration Guide](https://hacs.xyz/docs/faq/custom_repositories/)  
- Developed by [soulripper13](https://github.com/soulripper13)

---

[releases-shield]: https://img.shields.io/github/v/release/soulripper13/speedtest_rt_ru?style=for-the-badge
[releases]: https://github.com/soulripper13/speedtest_rt_ru/releases
[commits-shield]: https://img.shields.io/github/commit-activity/m/soulripper13/speedtest_rt_ru?style=for-the-badge
[commits]: https://github.com/soulripper13/speedtest_rt_ru/commits/main
[license-shield]: https://img.shields.io/github/license/soulripper13/speedtest_rt_ru?style=for-the-badge

[hacs-repo-badge]: https://img.shields.io/badge/Open%20in-HACS-41BDF5?style=for-the-badge&logo=home-assistant
[hacs-repo]: https://github.com/soulripper13/speedtest_rt_ru
[config-flow-badge]: https://img.shields.io/badge/Add%20Integration-Speedtest%20RT.RU-blue?style=for-the-badge&logo=home-assistant
[config-flow]: https://my.home-assistant.io/redirect/config_flow_start?domain=speedtest_rt_ru
