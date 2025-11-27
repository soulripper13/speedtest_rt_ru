# Speedtest RT.RU Integration for Home Assistant
[![HACS Badge][hacsbadge]][hacs]
[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![Community Forum][forum-shield]][forum]
---
## English
**Speedtest RT.RU** is a Home Assistant integration that automatically downloads and runs the QMS binary from [RT.RU](https://speedtest.rt.ru) to measure your internet speed.

![Logo](icon.png)

It provides six sensors:
- **Download** – download speed in Mbps
- **Upload** – upload speed in Mbps
- **Ping** – network latency in milliseconds
- **Jitter** – network jitter in milliseconds
- **ISP** – your Internet Service Provider name
- **Server** – the speedtest server used
### Features
- Automatic download of the QMS speedtest binary on setup
- **Server selection** – choose from available Russian speedtest servers or use automatic selection
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
The preferred way is to use HACS:
1. Search and download this integration to your HA installation via HACS, or click:  
   [![Open HACS Repository][hacs-repo-badge]][hacs-repo]
2. Restart Home Assistant
3. Add this integration to Home Assistant, or click:  
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

#### Server Selection
You can choose which speedtest server to use:
1. Go to **Settings → Devices & Services**.
2. Find your Speedtest RT.RU integration.
3. Click ⚙️ **Configure**.
4. Select your preferred server from the **Test Server** dropdown:
   - **Auto (Best Server)** – automatically selects the best server
   - Or choose a specific server by city (e.g., "Хабаровск - khabarovsk1.qms.ru")
5. Save changes. The integration will reload automatically.

#### Manual Speed Test
The integration also exposes a service:
`speedtest_rt_ru.perform_test`
You can call it manually to trigger a speed test and update all sensors.
To call the service:
1. Go to **Developer Tools → Services**.
2. Select `speedtest_rt_ru.perform_test` from the dropdown.
3. Call the service (no parameters required).

#### Disable Automatic Updates
If you prefer to disable automatic polling:
- Go to **Settings → Devices & Services**.
- Find your Speedtest RT.RU integration.
- Click ⚙️ **Configure**.
- Disable "Enable Automatic Updates" or set a high scan interval.
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

![Logo](icon.png)

Интеграция предоставляет шесть сенсоров:
- **Скорость загрузки** – в Мбит/с
- **Скорость отдачи** – в Мбит/с
- **Ping** – задержка сети в миллисекундах
- **Jitter** – джиттер сети в миллисекундах
- **ISP** – название вашего интернет-провайдера
- **Server** – используемый сервер Speedtest
### Возможности
- Автоматическая загрузка бинарника QMS при установке
- **Выбор сервера** – возможность выбора сервера из доступных серверов Speedtest или автоматический выбор
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
#### Установка через HACS (предпочтительно)
Предпочтительный способ — использовать HACS:
1. Найдите и загрузите эту интеграцию в вашу установку HA через HACS, или нажмите:  
   [![Открыть репозиторий HACS][hacs-repo-badge]][hacs-repo]
2. Перезапустите Home Assistant
3. Добавьте эту интеграцию в Home Assistant, или нажмите:  
   [![Добавить интеграцию][config-flow-badge]][config-flow]

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

#### Выбор сервера
Вы можете выбрать, какой сервер использовать для тестирования скорости:
1. Перейдите в **Настройки → Устройства и Сервисы**.
2. Найдите интеграцию Speedtest RT.RU.
3. Нажмите ⚙️ **Настроить**.
4. Выберите предпочитаемый сервер из выпадающего списка **Тестовый сервер**:
   - **Auto (Best Server)** – автоматический выбор лучшего сервера
   - Или выберите конкретный сервер по городу (например, "Хабаровск - khabarovsk1.qms.ru")
5. Сохраните изменения. Интеграция перезагрузится автоматически.

#### Ручной запуск теста
Для ручного запуска теста скорости используйте сервис
`speedtest_rt_ru.perform_test`
1. Перейдите в **Инструменты разработчика → Сервисы**.
2. Выберите `speedtest_rt_ru.perform_test` из выпадающего списка.
3. Вызовите сервис (параметры не требуются).

#### Отключение автоматических обновлений
Если вы хотите отключить автоматический опрос:
1. Перейдите в **Настройки → Устройства и Сервисы**.
2. Найдите интеграцию Speedtest RT.RU.
3. Нажмите ⚙️ **Настроить**.
4. Отключите "Включить автоматические обновления" или установите большой интервал сканирования.
5. Сохраните изменения.
Теперь сенсоры будут обновляться только при ручном вызове сервиса.
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
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Custom-41BDF5?style=for-the-badge
[hacs-repo-badge]: https://my.home-assistant.io/badges/hacs_repository.svg
[hacs-repo]: https://my.home-assistant.io/redirect/hacs_repository/?owner=soulripper13&repository=speedtest_rt_ru&category=integration
[config-flow-badge]: https://my.home-assistant.io/badges/config_flow_start.svg
[config-flow]: https://my.home-assistant.io/redirect/config_flow_start?domain=speedtest_rt_ru
[commits-shield]: https://img.shields.io/github/commit-activity/m/soulripper13/speedtest_rt_ru?style=for-the-badge
[commits]: https://github.com/soulripper13/speedtest_rt_ru/commits/main
[forum-shield]: https://img.shields.io/badge/Community-Forum-blue?style=for-the-badge&logo=home-assistant
[forum]: https://community.home-assistant.io/
[license-shield]: https://img.shields.io/github/license/soulripper13/speedtest_rt_ru?style=for-the-badge
[releases-shield]: https://img.shields.io/github/v/release/soulripper13/speedtest_rt_ru?style=for-the-badge
[releases]: https://github.com/soulripper13/speedtest_rt_ru/releases
