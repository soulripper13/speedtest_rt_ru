# Speedtest RT.RU Integration for Home Assistant

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
- Works on x86 and ARM devices (depending on QMS binary compatibility)

### Installation

#### Manual installation

1. Copy the `custom_components/speedtest_rt_ru` folder to your Home Assistant `config/custom_components` directory  
2. Restart Home Assistant  
3. Go to **Settings → Devices & Services → Add Integration → Speedtest RT.RU**  
4. Configure update interval or leave default

#### HACS installation

1. Add this repository to HACS as a **custom integration**  
2. Install via HACS  
3. Add the integration via the UI as above

### Usage

After setup, you will see six sensors:

- `sensor.speedtest_rt_ru_download`  
- `sensor.speedtest_rt_ru_upload`  
- `sensor.speedtest_rt_ru_ping`  
- `sensor.speedtest_rt_ru_jitter`  
- `sensor.speedtest_rt_ru_isp`  
- `sensor.speedtest_rt_ru_server`  

These can be used in automations, Lovelace dashboards, or for monitoring your internet connection.

### Troubleshooting

- If you see `Exec format error`, ensure that the QMS binary matches your system architecture  
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
- Работает на устройствах x86 и ARM (в зависимости от совместимости бинарника QMS)

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

После установки будут доступны шесть сенсоров:

- `sensor.speedtest_rt_ru_download`  
- `sensor.speedtest_rt_ru_upload`  
- `sensor.speedtest_rt_ru_ping`  
- `sensor.speedtest_rt_ru_jitter`  
- `sensor.speedtest_rt_ru_isp`  
- `sensor.speedtest_rt_ru_server`  

Их можно использовать в автоматизациях, Lovelace дашбордах или для мониторинга интернет-соединения.

### Устранение неполадок

- Если появляется ошибка `Exec format error`, убедитесь, что бинарник QMS соответствует архитектуре вашей системы  
- Логи доступны в **Настройки → Система → Журналы**
