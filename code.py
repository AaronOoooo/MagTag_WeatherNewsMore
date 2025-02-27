import time
import board
import wifi
import socketpool
import ssl
import adafruit_requests
import adafruit_ntp
from rtc import RTC

import secret  # Contains OPENWEATHERMAP_API_KEY, WIFI_SSID, WIFI_PASSWORD
from adafruit_magtag.magtag import MagTag

# -------------------------------------------------
# Configuration
# -------------------------------------------------
CITY = "Chicago"      # Change to your preferred city
TZ_OFFSET = -6        # Timezone offset from UTC (e.g., -6 for CST, -5 for CDT)
TIME_UPDATE_INTERVAL = 60    # Update displayed time every 60 seconds
WEATHER_UPDATE_INTERVAL = 300  # Fetch/update weather every 5 minutes

# -------------------------------------------------
# Modular Functions
# -------------------------------------------------
def connect_to_wifi():
    """Connect to Wi-Fi using credentials in secret.py."""
    print("Connecting to WiFi...")
    wifi.radio.connect(secret.WIFI_SSID, secret.WIFI_PASSWORD)
    print("Connected to WiFi!")

def sync_time(pool, tz_offset):
    """
    Sync the microcontroller's RTC with an NTP server.
    tz_offset: Timezone offset from UTC (e.g., -6 for CST, -5 for CDT).
    """
    print("Syncing time via NTP...")
    ntp = adafruit_ntp.NTP(pool, tz_offset=tz_offset)
    RTC().datetime = ntp.datetime
    print("Time synced via NTP!")

def fetch_weather(session, city, api_key):
    """
    Fetch current weather data from OpenWeatherMap for the given city and API key.
    Returns the parsed JSON data.
    """
    url = (
        "http://api.openweathermap.org/data/2.5/weather?"
        "q={}&appid={}&units=imperial".format(city, api_key)
    )
    print("Fetching weather data from OpenWeatherMap...")
    response = session.get(url)
    data = response.json()
    response.close()
    return data

def format_weather(data, city):
    """
    Given the weather JSON data and city name, return a multi-line weather string.
    Example:
      Weather in Chicago: 44°F,
      broken clouds
    """
    temp = data["main"]["temp"]
    description = data["weather"][0]["description"]
    return "Weather in {}: {}°F,\n{}".format(city, temp, description)

def format_datetime(now):
    """
    Given a time.struct_time object, return a string with abbreviated weekday,
    abbreviated month, day, year, and 12-hour format time with AM/PM.
    Example: "Tue, Mar 1 2025, 7:05 PM"
    """
    # Abbreviated weekday and month names
    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    weekday_str = weekday_names[now.tm_wday]
    month_str = month_names[now.tm_mon - 1]
    day = now.tm_mday
    year = now.tm_year

    # Convert to 12-hour format with AM/PM
    hour_12 = now.tm_hour % 12
    if hour_12 == 0:
        hour_12 = 12
    am_pm = "AM" if now.tm_hour < 12 else "PM"

    return "{}, {} {} {}, {}:{:02d} {}".format(
        weekday_str, month_str, day, year, hour_12, now.tm_min, am_pm
    )

def update_time_display(magtag, date_index):
    """Update only the date/time text on the display using the RTC."""
    now = time.localtime()
    datetime_str = format_datetime(now)
    magtag.set_text(datetime_str, date_index)
    magtag.refresh()

def update_weather_display(magtag, weather_index, session, city, api_key):
    """Fetch and update the weather text on the display."""
    data = fetch_weather(session, city, api_key)
    weather_str = format_weather(data, city)
    magtag.set_text(weather_str, weather_index)
    magtag.refresh()

# -------------------------------------------------
# Main Program Flow
# -------------------------------------------------
def main():
    # 1. Connect to Wi-Fi
    connect_to_wifi()

    # 2. Create a socket pool and sync time
    pool = socketpool.SocketPool(wifi.radio)
    sync_time(pool, TZ_OFFSET)

    # 3. Create an HTTP session
    session = adafruit_requests.Session(pool, ssl.create_default_context())

    # 4. Set up the MagTag display & text fields
    magtag = MagTag()

    # Index for date/time (small font)
    date_index = magtag.add_text(
        text_font="/fonts/Arial-Bold-12.bdf",
        text_position=(10, 10),
        text_color=0x000000,
    )

    # Index for weather (larger font)
    weather_index = magtag.add_text(
        text_font="/fonts/Helvetica-Bold-16.bdf",
        text_position=(10, 50),
        text_color=0x000000,
    )

    # 5. Initial data display
    # Update weather first so we have something on the display
    update_weather_display(magtag, weather_index, session, CITY, secret.OPENWEATHERMAP_API_KEY)
    update_time_display(magtag, date_index)

    # Track last update times (monotonic seconds)
    last_time_update = time.monotonic()
    last_weather_update = time.monotonic()

    # 6. Loop forever, updating time & weather on different schedules
    while True:
        current = time.monotonic()

        # Update time every 60 seconds
        if current - last_time_update >= TIME_UPDATE_INTERVAL:
            update_time_display(magtag, date_index)
            last_time_update = current

        # Update weather every 5 minutes
        if current - last_weather_update >= WEATHER_UPDATE_INTERVAL:
            update_weather_display(magtag, weather_index, session, CITY, secret.OPENWEATHERMAP_API_KEY)
            last_weather_update = current

        # Small sleep to avoid busy-waiting
        time.sleep(1)

# Run the main function at startup
main()
