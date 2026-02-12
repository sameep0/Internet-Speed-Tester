"""
Configuration and constants for the speed test client
"""

# API Endpoints - use HTTPS
SPEEDTEST_CONFIG_URL = "https://www.speedtest.net/speedtest-config.php"
SPEEDTEST_SERVERS_URL = "https://www.speedtest.net/speedtest-servers-static.php"
SPEEDTEST_SERVERS_FALLBACK = "https://www.speedtest.net/speedtest-servers.php"

# Test Configuration
DEFAULT_TIMEOUT = 15                      # increased from 10
DEFAULT_THREADS_DOWNLOAD = 2
DEFAULT_THREADS_UPLOAD = 2
MAX_SERVERS_TO_TEST = 5

# Download test sizes (in KB)
DOWNLOAD_SIZES = [350, 500, 750, 1000, 1500, 2000, 2500, 3000, 3500, 4000]

# Upload test sizes (in bytes)
UPLOAD_SIZES = [32768, 65536, 131072, 262144, 524288, 1048576, 7340032]

# Test duration (seconds)
DOWNLOAD_TEST_DURATION = 10
UPLOAD_TEST_DURATION = 10

# User Agent (browser-like to avoid blocking)
USER_AGENT_TEMPLATE = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# UI Configuration
WINDOW_TITLE = "Speed Test Client"
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
BG_COLOR = "#1a1a2e"
PRIMARY_COLOR = "#0f3460"
ACCENT_COLOR = "#16213e"
TEXT_COLOR = "#eaeaea"
SUCCESS_COLOR = "#00d9ff"
ERROR_COLOR = "#ff6b6b"

# Chart colors
CHART_DOWNLOAD_COLOR = "#00d9ff"
CHART_UPLOAD_COLOR = "#ff9ff3"
CHART_PING_COLOR = "#54a0ff"

# Fallback mode – set to True to always show fake results (for testing)
USE_FAKE_DATA = False   # change to True if you never get real results