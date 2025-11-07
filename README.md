# Speedtest RT.RU Integration for Home Assistant

## English

**Speedtest RT.RU** is a Home Assistant integration that automatically downloads and runs the QMS binary from [RT.RU](https://speedtest.rt.ru) to measure your internet speed. It provides sensors for:

- **Download speed** (Mbps)  
- **Upload speed** (Mbps)  
- **Ping** (ms)  
- **Jitter** (ms)  
- **ISP** (name of your Internet Service Provider)  
- **Server** (the speedtest server used)

### Features

- Automatic download of the QMS speedtest binary on setup.  
- Configurable update interval through the UI or manual update.  
- Fully compatible with Home Assistant and HACS.  
- Works on x86 and ARM devices (depending on the QMS binary compatibility).

### Installation

#### Manual installation

1. Copy the `custom_components/speedtest_rt_ru` folder to your Home Assistant `config/custom_components` directory.  
2. Restart Home Assistant.  
3. Go to **Settings → Devices & Services → Add Integration → Speedtest RT.RU**.  
4. Configure update interval or leave default.

#### HACS installation

1. Add the repository to HACS as a custom repository (category: Integration).  
2. Install via HACS.  
3. Follow the same steps above to add the integration via the UI.

### Usage

After setup, you will see six sensors in Home Assistant:

- `sensor.speedtest_rt_ru_download`  
- `sensor.speedtest_rt_ru_upload`  
- `sensor.speedtest_rt_ru_ping`  
- `sensor.speedtest_rt_ru_jitter`  
- `sensor.speedtest_rt_ru_isp`  
- `sensor.speedtest_rt_ru_server`  

These can be used in automations, dashboards, or energy monitoring.

### Troubleshooting

- If you see `Exec format error`, check that the QMS binary matches your system architecture.  
- Logs can be found under **Settings → System → Logs**.

---

## Русский

**Speedtest RT.RU** — интеграция для Home Assistant, которая автоматически скачивает и запускает бинарник QMS с [RT.RU](https://speedtest.rt.ru) для измерения скорости интернета. Она предоставляет сенсоры:

- **Скорость загрузки** (Мбит/с)  
- **Скорость отдачи** (Мбит/с)  
- **Ping** (мс)  
- **Jitter** (мс)  
- **ISP** (название интернет-провайдера)  
- **Server** (используемый сервер Speedtest)

### Возможности

- Автоматическая загрузка бинарника QMS при установке.  
- Настраиваемый интервал обновления через UI или ручное обновление.  
- Полностью совместимо с Home Assistant и HACS.  
- Работает на x86 и ARM устройствах (в зависимости от совместимости бинарника QMS).

### Установка

#### Ручная установка

1. Скопируйте папку `custom_components/speedtest_rt_ru` в директорию `config/custom_components` Home Assistant.  
2. Перезапустите Home Assistant.  
3. Перейдите в **Настройки → Устройства и Сервисы → Добавить интеграцию → Speedtest RT.RU**.  
4. Настройте интервал обновления или оставьте значение по умолчанию.

#### Установка через HACS

1. Добавьте репозиторий в HACS как пользовательский (категория: Integration).  
2. Установите через HACS.  
3. Добавьте интеграцию через UI, как описано выше.

### Использование

После установки вы увидите шесть сенсоров:

- `sensor.speedtest_rt_ru_download`  
- `sensor.speedtest_rt_ru_upload`  
- `sensor.speedtest_rt_ru_ping`  
- `sensor.speedtest_rt_ru_jitter`  
- `sensor.speedtest_rt_ru_isp`  
- `sensor.speedtest_rt_ru_server`  

Их можно использовать в автоматизациях, дашбордах или для мониторинга интернета.

### Устранение неполадок

- Если появляется ошибка `Exec format error`, убедитесь, что бинарник QMS соответствует архитектуре вашей системы.  
- Логи доступны в **Настройки → Система → Журналы**.
