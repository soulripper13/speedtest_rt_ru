# Speedtest RT.RU Integration for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom%20integration-yellow.svg)](https://github.com/hacs/integration)
[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)


Home Assistant integration for measuring internet speed using RT.RU's QMS binary.

![Logo](icon.png)

## English

**Speedtest RT.RU** is a Home Assistant integration that automatically downloads and runs the QMS binary from [RT.RU](https://speedtest.rt.ru) to measure your internet speed. It provides six sensors:
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
- Works only on x86_64 systems
- Requires Home Assistant 2025.11+

### Installation
#### Manual installation
1. Copy the `custom_components/speedtest_rt_ru` folder to your Home Assistant `config/custom_components` directory
2. Restart Home Assistant
3. Go to **Settings → Devices & Services → Add Integration → Speedtest RT.RU**
4. Configure update interval or leave default

#### HACS installation
The preferred way is to use HACS:

1. Search and download this integration to your HA installation via HACS, or click:

   [![Open HACS Repository][hacs-repo-badge]][hacs-repo]

1. Restart home assistant

1. Add this integration to Home Assistant, or click:

   [![Add Integration][config-flow-badge]][config-flow]

### Usage
After setup, you will see six sensors (entity IDs may include domain prefix, e.g., `sensor.speedtest_rt_ru_download`):
- `sensor.download`
- `sensor.upload`
- `sensor.ping`
- `sensor.jitter`
- `sensor.isp`
- `sensor.server`

These can be used in automations, Lovelace dashboards, or for monitoring your internet connection.

The integration also exposes a service `speedtest_rt_ru.perform_test` that can be called to manually trigger a speed test and update the sensors. To use it:
- Go to **Developer Tools → Services**.
- Select `speedtest_rt_ru.perform_test` from the service dropdown.
- Call the service (no parameters required).

If you want to disable automatic polling (updates at the configured interval) and rely only on manual updates via the service:
- Go to **Settings → Devices & Services**.
- Find your Speedtest RT.RU integration.
- Click the gear icon (Configure) and toggle off "Enable polling" or adjust the scan interval to a very high value (e.g., never).
- Save changes. Sensors will now only update when you call the service.

### Troubleshooting
- If you see **`Exec format error`**, ensure that the QMS binary matches your system architecture (x86_64 only)
- Logs are available in **Settings → System → Logs**

---

## Русский

**Speedtest RT.RU** — интеграция для Home Assistant, которая автоматически скачивает и запускает бинарник QMS с [RT.RU](https://speedtest.rt.ru) для измерения скорости интернета. Интеграция предоставляет шесть сенсоров:
- **Скорость загрузки** – в Мбит/с
- **Скорость отдачи** – в Мбит/с
- **Ping** – задержка сети в миллисекундах
- **Jitter** – джиттер сети в миллисекундах
- **ISP** – название вашего интернет-провайдера
- **Server** – используемый сервер Speedtest

### Возможности
- Автоматическая загрузка бинарника QMS при установке
- Настраиваемый интервал обновления через UI Home Assistant или ручное обновление
- Полная совместимость с Home Assistant и HACS
- Работает только на системах x86_64
- Требует Home Assistant 2025.11+

### Установка
#### Ручная установка
1. Скопируйте папку `custom_components/speedtest_rt_ru` в директорию `config/custom_components` Home Assistant
2. Перезапустите Home Assistant
3. Перейдите в **Настройки → Устройства и Сервисы → Добавить интеграцию → Speedtest RT.RU**
4. Настройте интервал обновления или оставьте значение по умолчанию

#### Установка через HACS
1. Добавьте репозиторий в HACS как **пользовательскую интеграцию**
2. Установите через HACS
3. Добавьте интеграцию через UI, как указано выше

### Использование
После установки будут доступны шесть сенсоров (ID сущностей могут включать префикс домена, напр., `sensor.speedtest_rt_ru_download`):
- `sensor.download`
- `sensor.upload`
- `sensor.ping`
- `sensor.jitter`
- `sensor.isp`
- `sensor.server`

Их можно использовать в автоматизациях, Lovelace дашбордах или для мониторинга интернет-соединения.

Интеграция также предоставляет сервис `speedtest_rt_ru.perform_test`, который можно вызвать для ручного запуска теста скорости и обновления сенсоров. Чтобы использовать его:
- Перейдите в **Инструменты разработчика → Сервисы**.
- Выберите `speedtest_rt_ru.perform_test` из выпадающего списка сервисов.
- Вызовите сервис (параметры не требуются).

Если вы хотите отключить автоматическое опрос (обновления по настроенному интервалу) и полагаться только на ручные обновления через сервис:
- Перейдите в **Настройки → Устройства и Сервисы**.
- Найдите вашу интеграцию Speedtest RT.RU.
- Нажмите на значок шестерёнки (Настроить) и отключите "Включить опрос" или установите интервал сканирования на очень высокое значение (например, никогда).
- Сохраните изменения. Сенсоры теперь будут обновляться только при вызове сервиса.

### Устранение неполадок
- Если появляется ошибка **`Exec format error`**, убедитесь, что бинарник QMS соответствует архитектуре вашей системы (только x86_64)
- Логи доступны в **Настройки → Система → Журналы**
