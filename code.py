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

# ------------------------------
# Utility Functions
# ------------------------------
def connect_to_wifi():
    """Connect to Wi-Fi using credentials in secret.py."""
    print("Connecting to WiFi...")
    wifi.radio.connect(secret.WIFI_SSID, secret.WIFI_PASSWORD)
    print("Connected to WiFi!")

def sync_time(pool, tz_offset=-6):
    """
    Sync the microcontroller's RTC with an NTP server.
    tz_offset: Timezone offset from UTC (e.g., -6 for CST, -5 for CDT).
    """
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
    # Everything after the comma goes on a new line
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

    # Combine into one line
    return "{}, {} {} {}, {}:{:02d} {}".format(
        weekday_str, month_str, day, year, hour_12, now.tm_min, am_pm
    )

def display_data(datetime_str, weather_str):
    """
    Display the date/time and weather strings on the MagTag.
    Adjust text_position or fonts as needed.
    """
    magtag = MagTag()

    # 1) Date/Time in smaller font
    datetime_index = magtag.add_text(
        text_font="/fonts/Arial-Bold-12.bdf",
        text_position=(10, 10),
        text_color=0x000000,
    )

    # 2) Weather info in larger font, further down
    weather_index = magtag.add_text(
        text_font="/fonts/Helvetica-Bold-16.bdf",
        text_position=(10, 50),
        text_color=0x000000,
    )

    magtag.set_text(datetime_str, datetime_index)
    magtag.set_text(weather_str, weather_index)
    magtag.refresh()

# ------------------------------
# Main Program Flow
# ------------------------------
def main():
    # Connect to Wi-Fi
    connect_to_wifi()

    # Create a socket pool
    pool = socketpool.SocketPool(wifi.radio)

    # Sync time via NTP (adjust tz_offset for your time zone)
    sync_time(pool, tz_offset=-6)

    # Create an HTTP session
    session = adafruit_requests.Session(pool, ssl.create_default_context())

    # Fetch weather data
    city = "Chicago"  # Change if desired
    data = fetch_weather(session, city, secret.OPENWEATHERMAP_API_KEY)

    # Format the weather string
    weather_str = format_weather(data, city)

    # Get the current local time
    now = time.localtime()

    # Format the date/time
    datetime_str = format_datetime(now)

    # Display everything on the MagTag
    display_data(datetime_str, weather_str)

    # Keep the display on screen for 10 seconds (or longer if you wish)
    time.sleep(10)

# Run the main function when the code starts
main()
