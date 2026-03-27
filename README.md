# Speedtest RT.RU Integration for Home Assistant
[![HACS Badge][hacsbadge]][hacs]
[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)
[![Community Forum][forum-shield]][forum]
![Integration Usage](https://img.shields.io/badge/dynamic/json?color=orange&logo=home-assistant&label=Downloads&suffix=%20installs&cacheSeconds=15600&style=for-the-badge&url=https://analytics.home-assistant.io/custom_integrations.json&query=$.speedtest_rt_ru.total)
[![Support Development](https://img.shields.io/badge/Support-Development-FFDD00?style=for-the-badge&logo=paypal&logoColor=black)](#support-the-project)

---

## English

**Speedtest RT.RU** is a Home Assistant integration that automatically downloads and runs the QMS binary from [RT.RU](https://speedtest.rt.ru) to measure your internet speed.

![Logo](icon.png)

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
- Automatic download of the QMS speedtest binary on setup
- **Automatic binary updates** – checks for a new binary version every 24 hours via ETag comparison and updates in place without requiring a restart
- **Server selection** – choose from available Russian speedtest servers or use automatic selection
- Configurable update interval through the Home Assistant UI or manual update
- **Button entity** – trigger speedtest directly from the UI
- **Lovelace cards** – two built-in cards (main + compact) auto-installed and registered on setup, removed on deletion
- **Bilingual cards** – cards support English and Russian (`language: "en"` or `"ru"`)
- **Diagnostics support** – troubleshoot issues via Settings > Integrations
- **Timeout protection** – tests automatically timeout after 120 seconds
- Fully compatible with Home Assistant and HACS
- Works on **x86_64** and **ARM64 (aarch64)** systems
- Requires **Home Assistant 2024.1+**

---

### Installation

#### HACS installation (preferred)
1. Search and download this integration via HACS, or click:
   [![Open HACS Repository][hacs-repo-badge]][hacs-repo]
2. Restart Home Assistant.
3. Add the integration, or click:
   [![Add Integration][config-flow-badge]][config-flow]

#### Manual installation
1. Copy the `custom_components/speedtest_rt_ru` folder to your `config/custom_components` directory.
2. Restart Home Assistant.
3. Go to **Settings → Devices & Services → Add Integration → Speedtest RT.RU**.
4. Configure the update interval or leave the default (30 minutes).

---

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

---

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

#### Binary Auto-Update
The integration checks for a new QMS binary every **24 hours** by comparing the `ETag` header from `lib.qms.ru`. If a new version is found, it is downloaded and applied in place — no restart required. You will see a log message when an update is detected and applied.

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

---

### Troubleshooting
- **`Exec format error`** → Your system architecture is not supported. Only **x86_64** and **ARM64 (aarch64)** are supported.
- **Binary download fails** → Check that [speedtest.rt.ru](https://speedtest.rt.ru) and `lib.qms.ru` are reachable from your HA host.
- **Test hangs** → Tests automatically time out after 120 seconds.
- **Cards not appearing** → Go to **Settings → Devices & Services**, find the integration, and restart HA. Cards are registered automatically on setup.
- Logs are available under **Settings → System → Logs**.

---

## Support the Project

This integration is developed and maintained in spare time and provided free to the Home Assistant community.

If you find it useful, any contribution is appreciated — but never required ❤️

### Ways to Support

* **PayPal** – [https://paypal.me/SKatoaroo](https://paypal.me/SKatoaroo)
* **Bitcoin (BTC)** – `bc1qvu8a9gdy3dcxa94jge7d3rd7claapsydjsjxn0`
* **Solana (SOL)** – `4jvCR2YFQLqguoyz9qAMPzVbaEcDsG5nzRHFG8SeaeBK`

You can also help by:
* Reporting bugs
* Submitting pull requests
* Suggesting features
* Helping other users
* Starring the repository ⭐

Thank you for being part of the Home Assistant community.

---

## Русский

**Speedtest RT.RU** — интеграция для Home Assistant, автоматически загружающая и запускающая бинарник QMS с [RT.RU](https://speedtest.rt.ru) для измерения скорости интернета.

![Logo](icon.png)

Интеграция предоставляет сенсоры и кнопку:
- **Скорость загрузки** – в Мбит/с
- **Скорость отдачи** – в Мбит/с
- **Ping** – задержка сети в миллисекундах (в режиме ожидания)
- **Jitter** – джиттер сети в миллисекундах
- **ISP** – название вашего интернет-провайдера
- **Server** – используемый сервер Speedtest
- **IP** – ваш публичный IP-адрес
- **Result URL** – ссылка на полный результат теста на qms.ru
- **Last Test** – время последнего завершённого теста
- **Run Speedtest** (кнопка) – ручной запуск теста скорости
- 2 дополнительных сенсора задержки: пинг при загрузке и при отдаче (отключены по умолчанию)

Все сущности объединены в одно устройство **Speedtest RT.RU** для удобного управления.

### Возможности
- Автоматическая загрузка бинарника QMS при установке
- **Автоматическое обновление бинарника** – каждые 24 часа интеграция проверяет наличие новой версии по заголовку ETag и обновляет файл без перезапуска HA
- **Выбор сервера** – выбор из доступных серверов или автоматический подбор
- Настраиваемый интервал обновления через UI Home Assistant
- **Кнопка запуска** – запуск теста прямо из интерфейса
- **Карточки Lovelace** – две встроенные карточки (основная и компактная) автоматически устанавливаются при настройке интеграции и удаляются вместе с ней
- **Двуязычные карточки** – карточки поддерживают английский и русский язык (`language: "en"` или `"ru"`)
- **Поддержка диагностики** – устранение неполадок через Настройки > Интеграции
- **Защита от зависания** – тесты автоматически прерываются через 120 секунд
- Полная совместимость с Home Assistant и HACS
- Работает на **x86_64** и **ARM64 (aarch64)** системах
- Требует **Home Assistant 2024.1+**

---

### Установка

#### Установка через HACS (предпочтительно)
1. Найдите и загрузите интеграцию через HACS, или нажмите:
   [![Открыть репозиторий HACS][hacs-repo-badge]][hacs-repo]
2. Перезапустите Home Assistant.
3. Добавьте интеграцию, или нажмите:
   [![Добавить интеграцию][config-flow-badge]][config-flow]

#### Ручная установка
1. Скопируйте папку `custom_components/speedtest_rt_ru` в `config/custom_components` вашего Home Assistant.
2. Перезапустите Home Assistant.
3. Перейдите в **Настройки → Устройства и Сервисы → Добавить интеграцию → Speedtest RT.RU**.
4. Настройте интервал обновления или оставьте значение по умолчанию (30 минут).

---

### Карточки Lovelace

Две карточки автоматически устанавливаются и регистрируются при настройке интеграции, а при её удалении — удаляются.

#### Основная карточка (`custom:speedtest-rt-ru-card`)
Полнофункциональная карточка с двумя радиальными датчиками для загрузки и отдачи, показателями пинга и джиттера, именем провайдера, информацией о сервере, IP-адресом, ссылкой на результат и временем последнего теста.

```yaml
type: custom:speedtest-rt-ru-card
language: ru   # или "en" для английских подписей
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

#### Компактная карточка (`custom:speedtest-rt-ru-compact`)
Минималистичная однострочная карточка — идеальна для боковых панелей и компактных дэшбордов.

```yaml
type: custom:speedtest-rt-ru-compact
language: ru   # или "en" для английских подписей
entities:
  download: sensor.speedtest_rt_ru_download
  upload: sensor.speedtest_rt_ru_upload
  ping: sensor.speedtest_rt_ru_ping
```

Обе карточки имеют визуальный редактор, доступный из меню выбора карточек Lovelace.

---

### Использование

После установки будут доступны следующие сенсоры и одна кнопка, объединённые в устройство "Speedtest RT.RU":
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

Дополнительные сенсоры задержки (отключены по умолчанию, включить в настройках объектов):
- `sensor.speedtest_rt_ru_ping_during_download` — пинг IQM во время загрузки
- `sensor.speedtest_rt_ru_ping_low_during_download` / `ping_high_during_download`
- `sensor.speedtest_rt_ru_jitter_during_download`
- `sensor.speedtest_rt_ru_ping_during_upload` — пинг IQM во время отдачи
- `sensor.speedtest_rt_ru_ping_low_during_upload` / `ping_high_during_upload`
- `sensor.speedtest_rt_ru_jitter_during_upload`

Используйте их в автоматизациях, Lovelace-дэшбордах и для мониторинга соединения.

#### Выбор сервера
1. Перейдите в **Настройки → Устройства и Сервисы**.
2. Найдите интеграцию Speedtest RT.RU.
3. Нажмите ⚙️ **Настроить**.
4. Выберите сервер из выпадающего списка **Тестовый сервер**:
   - **Auto (Best Server)** – автоматический выбор лучшего сервера
   - Или выберите конкретный сервер по городу (например, "Хабаровск - khabarovsk1.qms.ru")
5. Сохраните изменения. Интеграция перезагрузится автоматически.

#### Ручной запуск теста

**Способ 1: Кнопка (рекомендуется)**
Нажмите кнопку "Run Speedtest" в панели устройства или на карточке Lovelace.

**Способ 2: Вызов сервиса**
Интеграция предоставляет сервис `speedtest_rt_ru.perform_test`:
1. Перейдите в **Инструменты разработчика → Сервисы**.
2. Выберите `speedtest_rt_ru.perform_test`.
3. Вызовите сервис (параметры не требуются).

#### Автоматическое обновление бинарника
Каждые **24 часа** интеграция выполняет HEAD-запрос к `lib.qms.ru` и сравнивает заголовок `ETag`. Если обнаружена новая версия — бинарник загружается и заменяется без перезапуска Home Assistant. Информация об обновлении появится в логах.

#### Отключение автоматических тестов скорости
1. Перейдите в **Настройки → Устройства и Сервисы**.
2. Найдите интеграцию Speedtest RT.RU.
3. Нажмите ⚙️ **Настроить**.
4. Отключите «Включить автоматические обновления» или установите большой интервал.
5. Сохраните изменения.

Сенсоры будут обновляться только при ручном вызове сервиса или нажатии кнопки.

#### Диагностика
1. Перейдите в **Настройки → Устройства и Сервисы**.
2. Найдите интеграцию Speedtest RT.RU.
3. Нажмите ⋮ и выберите **Скачать диагностику**.

---

### Устранение неполадок
- Ошибка **`Exec format error`** → архитектура системы не поддерживается. Поддерживаются только **x86_64** и **ARM64 (aarch64)**.
- **Ошибка загрузки бинарника** → проверьте доступность [speedtest.rt.ru](https://speedtest.rt.ru) и `lib.qms.ru` с вашего хоста HA.
- **Тест зависает** → тесты автоматически прерываются через 120 секунд.
- **Карточки не появляются** → перейдите в **Настройки → Устройства и Сервисы**, найдите интеграцию и перезапустите HA. Карточки регистрируются автоматически при установке.
- Логи доступны в **Настройки → Система → Журналы**.

---

### Поддержите проект

Эта интеграция разрабатывается и поддерживается в свободное время и предоставляется бесплатно сообществу Home Assistant. Если вы находите её полезной, любая помощь будет высоко оценена — но никогда не обязательна ❤️

### Способы поддержки

* **PayPal** – [https://paypal.me/SKatoaroo](https://paypal.me/SKatoaroo)
* **Bitcoin (BTC)** – `bc1qvu8a9gdy3dcxa94jge7d3rd7claapsydjsjxn0`
* **Solana (SOL)** – `4jvCR2YFQLqguoyz9qAMPzVbaEcDsG5nzRHFG8SeaeBK`

Вы также можете помочь:
* Сообщая об ошибках
* Отправляя pull-запросы
* Предлагая новые функции
* Помогая другим пользователям
* Поставив звёздочку репозиторию ⭐

Спасибо, что вы часть сообщества Home Assistant!

---

## Links and Credits
- [RT.RU Speedtest](https://speedtest.rt.ru)
- [Home Assistant](https://www.home-assistant.io)
- [HACS Integration Guide](https://hacs.xyz/docs/faq/custom_repositories/)
- Developed by [soulripper13](https://github.com/soulripper13)

---

[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Default-41BDF5?style=for-the-badge
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
