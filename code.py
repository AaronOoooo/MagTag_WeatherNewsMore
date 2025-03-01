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
CITY = "Chicago"      
TZ_OFFSET = -6        
TIME_UPDATE_INTERVAL = 60    # Update time every 60 seconds
WEATHER_UPDATE_INTERVAL = 300  # Update weather every 5 minutes
FORECAST_UPDATE_INTERVAL = 1800  # Update forecast every 30 minutes

# -------------------------------------------------
# Initialize MagTag
# -------------------------------------------------
magtag = MagTag()
current_view = "weather"  # Start with current weather
last_weather_update = last_forecast_update = time.monotonic()

# Initialize weather and forecast strings
weather_str = ""
forecast_str = ""

# -------------------------------------------------
# Text Fields
# -------------------------------------------------
# Header (shared between views)
header_index = magtag.add_text(
    text_font="/fonts/Arial-Bold-12.bdf",
    text_position=(10, 10),
    text_color=0x000000,
)

# Content (weather or forecast)
content_index = magtag.add_text(
    text_font="/fonts/Arial-12.bdf",
    text_position=(10, 30),
    text_color=0x000000,
    line_spacing=12,  # Reduce spacing between lines
)

# -------------------------------------------------
# Modular Functions
# -------------------------------------------------
def connect_to_wifi():
    """Connect to Wi-Fi."""
    print("Connecting to WiFi...")
    wifi.radio.connect(secret.WIFI_SSID, secret.WIFI_PASSWORD)
    print("Connected!")

def sync_time(pool):
    """Sync time via NTP."""
    print("Syncing time...")
    ntp = adafruit_ntp.NTP(pool, tz_offset=TZ_OFFSET)
    RTC().datetime = ntp.datetime
    print("Time synced!")

def fetch_weather(session, city, api_key):
    """Fetch current weather data."""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=imperial"
    print("Fetching weather...")
    response = session.get(url)
    data = response.json()
    response.close()
    return data

def fetch_forecast(session, city, api_key):
    """Fetch 5-day forecast data."""
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=imperial"
    print("Fetching forecast...")
    response = session.get(url)
    data = response.json()
    response.close()
    return data

def format_weather(data, city):
    """Format current weather into a string."""
    temp = data["main"]["temp"]
    temp_max = data["main"]["temp_max"]
    temp_min = data["main"]["temp_min"]
    humidity = data["main"]["humidity"]
    wind_speed = data["wind"]["speed"]
    wind_deg = data["wind"]["deg"]
    
    # Wind direction logic (fixed)
    wind_dir = "N"
    if 22.5 <= wind_deg < 67.5:
        wind_dir = "NE"
    elif 67.5 <= wind_deg < 112.5:
        wind_dir = "E"
    elif 112.5 <= wind_deg < 157.5:
        wind_dir = "SE"
    elif 157.5 <= wind_deg < 202.5:
        wind_dir = "S"
    elif 202.5 <= wind_deg < 247.5:
        wind_dir = "SW"
    elif 247.5 <= wind_deg < 292.5:
        wind_dir = "W"
    elif 292.5 <= wind_deg < 337.5:
        wind_dir = "NW"

    return (
        "Weather in {}: {}°F\n".format(city, temp) +
        "High: {}°F, Low: {}°F\n".format(temp_max, temp_min) +
        "Humidity: {}%, Wind: {} mph {}".format(humidity, wind_speed, wind_dir)
    )

def format_forecast(data):
    """Format forecast into a string."""
    forecast_str = ""
    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    for entry in data["list"][:5]:  # First 5 entries
        date = time.localtime(entry["dt"])  # Fixed: Removed extra parenthesis
        weekday = weekday_names[date.tm_wday]
        temp = entry["main"]["temp"]
        desc = entry["weather"][0]["description"]
        forecast_str += f"{weekday}: {temp}°F, {desc}\n"
    return forecast_str

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

def update_display():
    """Refresh the screen based on current view."""
    magtag.set_text("", header_index)  # Clear header
    magtag.set_text("", content_index)  # Clear content
    
    if current_view == "weather":
        # Show current weather
        magtag.set_text(format_datetime(time.localtime()), header_index)
        magtag.set_text(weather_str, content_index)
    else:
        # Show forecast
        magtag.set_text("5-Day Forecast", header_index)
        magtag.set_text(forecast_str, content_index)
    
    magtag.refresh()

# -------------------------------------------------
# Main Program Flow
# -------------------------------------------------
def main():
    global current_view, weather_str, forecast_str, last_weather_update, last_forecast_update
    
    # 1. Connect to Wi-Fi
    connect_to_wifi()
    
    # 2. Sync time
    pool = socketpool.SocketPool(wifi.radio)
    sync_time(pool)
    
    # 3. Create HTTP session
    session = adafruit_requests.Session(pool, ssl.create_default_context())
    
    # 4. Initial data fetch
    weather_data = fetch_weather(session, CITY, secret.OPENWEATHERMAP_API_KEY)
    forecast_data = fetch_forecast(session, CITY, secret.OPENWEATHERMAP_API_KEY)
    weather_str = format_weather(weather_data, CITY)
    forecast_str = format_forecast(forecast_data)
    update_display()
    
    # 5. Main loop
    while True:
        current_time = time.monotonic()
        
        # Check for button press (leftmost button: Button A)
        if not magtag.peripherals.buttons[0].value:  # Use index 0 for Button A
            current_view = "forecast" if current_view == "weather" else "weather"
            update_display()
            time.sleep(0.5)  # Debounce
        
        # Update weather every 5 minutes
        if current_time - last_weather_update >= WEATHER_UPDATE_INTERVAL:
            weather_data = fetch_weather(session, CITY, secret.OPENWEATHERMAP_API_KEY)
            weather_str = format_weather(weather_data, CITY)
            if current_view == "weather":
                update_display()
            last_weather_update = current_time
        
        # Update forecast every 30 minutes
        if current_time - last_forecast_update >= FORECAST_UPDATE_INTERVAL:
            forecast_data = fetch_forecast(session, CITY, secret.OPENWEATHERMAP_API_KEY)
            forecast_str = format_forecast(forecast_data)
            if current_view == "forecast":
                update_display()
            last_forecast_update = current_time
        
        time.sleep(0.1)  # Reduce sleep for responsive button presses

# Run the program
main()
