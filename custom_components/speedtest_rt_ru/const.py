"""Constants for the Speedtest RT.RU integration."""

DOMAIN = "speedtest_rt_ru"

# Configuration keys
CONF_SCAN_INTERVAL = "scan_interval"
CONF_AUTO_UPDATE = "auto_update"
CONF_SERVER_ID = "server_id"

# Defaults
DEFAULT_SCAN_INTERVAL = 1800  # 30 minutes in seconds
DEFAULT_AUTO_UPDATE = True
DEFAULT_SERVER_ID = "auto"  # Auto-select server

# Sensor attributes
ATTR_DOWNLOAD = "download"
ATTR_UPLOAD = "upload"
ATTR_PING = "ping"
ATTR_JITTER = "jitter"
ATTR_ISP = "isp"
ATTR_SERVER = "server"

# Binary paths and URLs
BINARY_NAME = "qms_lib"
BINARY_URL_X86 = "https://lib.qms.ru/bin/linux/qms_lib.zip"
BINARY_URL_ARM64 = "https://lib.qms.ru/bin/linux_arm64/qms_lib.zip"
BINARY_DIR = "custom_components/speedtest_rt_ru"
