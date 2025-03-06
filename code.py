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
TIME_UPDATE_INTERVAL = 60       # Update time every 60 seconds
WEATHER_UPDATE_INTERVAL = 300   # Update weather every 5 minutes
FORECAST_UPDATE_INTERVAL = 1800 # Update forecast every 30 minutes
NEWS_UPDATE_INTERVAL = 900      # Update news every 15 minutes (900 seconds)

# -------------------------------------------------
# Initialize MagTag
# -------------------------------------------------
magtag = MagTag()
current_view = "weather"  # Start with current weather

# Keep track of last update times
last_weather_update = time.monotonic()
last_forecast_update = time.monotonic()
last_news_update = time.monotonic()

# Global variable for news headlines paging
news_list = []  # Will store up to six headlines
news_page = 0   # 0: headlines 0-1, 1: headlines 2-3, 2: headlines 4-5

# -------------------------------------------------
# Text Fields
# -------------------------------------------------
header_index = magtag.add_text(
    text_font="/fonts/Arial-Bold-12.bdf",
    text_position=(5, 0),
    text_color=0x000000,
)

content_index = magtag.add_text(
    text_font="/fonts/Arial-12.bdf",
    text_position=(5, 60),
    text_color=0x000000,
    line_spacing=0.7,
    # text_wrap=28,  # If you prefer automatic wrapping, uncomment this
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
    """Fetch 5-day forecast data (3-hour increments)."""
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=imperial"
    print("Fetching forecast...")
    response = session.get(url)
    data = response.json()
    response.close()
    return data

def fetch_headlines(session):
    """
    Fetch the first six headlines from lite.cnn.com,
    replace unsupported glyphs, and wrap long lines.
    Returns a list of headlines.
    """
    url = "https://lite.cnn.com/en"
    print("Fetching headlines from lite.cnn.com...")
    response = session.get(url)
    html = response.text
    response.close()

    # Helper dict to replace fancy punctuation with ASCII
    replace_map = {
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "—": "-",
        "–": "-",
        "…": "...",
    }

    # Simple word-wrapping helper
    def wrap_text(text, max_chars=38):
        words = text.split()
        lines = []
        current_line = []
        current_length = 0

        for w in words:
            if current_length + len(w) + (1 if current_line else 0) > max_chars:
                lines.append(" ".join(current_line))
                current_line = [w]
                current_length = len(w)
            else:
                current_line.append(w)
                current_length += len(w) + (1 if current_line else 0)
        if current_line:
            lines.append(" ".join(current_line))
        return "\n".join(lines)

    headlines = []
    parts = html.split("<li ")
    for part in parts[1:]:
        if "<a href=" not in part:
            continue
        a_start = part.find("<a href=")
        anchor_close = part.find(">", a_start)
        anchor_end = part.find("</a>", anchor_close)
        if anchor_close == -1 or anchor_end == -1:
            continue

        headline = part[anchor_close+1:anchor_end].strip()
        if "Terms" in headline or "Privacy" in headline:
            continue

        for old_char, new_char in replace_map.items():
            headline = headline.replace(old_char, new_char)

        wrapped = wrap_text(headline, max_chars=38)
        if len(wrapped) > 5:
            headlines.append(wrapped)
        if len(headlines) >= 6:
            break

    return headlines

def format_weather(data, city):
    """Format current weather into a string with whole-number temps."""
    temp = round(data["main"]["temp"])
    temp_max = round(data["main"]["temp_max"])
    temp_min = round(data["main"]["temp_min"])
    feels_like = round(data["main"]["feels_like"])
    humidity = data["main"]["humidity"]
    wind_speed = round(data["wind"]["speed"])

    # Adjust sunrise and sunset times by adding the timezone offset (in seconds)
    sunrise = time.localtime(data["sys"]["sunrise"] + (TZ_OFFSET * 3600))
    sunset = time.localtime(data["sys"]["sunset"] + (TZ_OFFSET * 3600))

    sunrise_time = "{}:{:02d} AM".format(sunrise.tm_hour, sunrise.tm_min)
    sunset_hour_12 = sunset.tm_hour - 12 if sunset.tm_hour > 12 else sunset.tm_hour
    if sunset_hour_12 == 0:
        sunset_hour_12 = 12
    sunset_am_pm = "PM" if sunset.tm_hour >= 12 else "AM"
    sunset_time = "{}:{:02d} {}".format(sunset_hour_12, sunset.tm_min, sunset_am_pm)

    return (
        "Weather in {}: {}°F\n".format(city, temp) +
        "High: {}°F, Low: {}°F\n".format(temp_max, temp_min) +
        "Feels like: {}°F\n".format(feels_like) +
        "Humidity: {}%, Wind: {} mph\n".format(humidity, wind_speed) +
        "Sunrise: {}, Sunset: {}".format(sunrise_time, sunset_time)
    )

def format_forecast(data):
    """
    Format the forecast for the next five days using every 8th entry
    (since the forecast is in 3-hour increments).
    """
    forecast_str = ""
    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

    for i in range(5):
        entry = data["list"][i * 8]
        date_struct = time.localtime(entry["dt"])
        weekday = weekday_names[date_struct.tm_wday]
        temp = round(entry["main"]["temp"])
        desc = entry["weather"][0]["description"]
        forecast_str += f"{weekday}: {temp}°F, {desc}\n"

    return forecast_str

def format_datetime(now):
    """
    Return a string with abbreviated weekday, abbreviated month, day, year,
    and 12-hour format time with AM/PM.
    Example: "Tue, Mar 1 2025, 7:05 PM"
    """
    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
                   "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

    weekday_str = weekday_names[now.tm_wday]
    month_str = month_names[now.tm_mon - 1]
    day = now.tm_mday
    year = now.tm_year

    hour_12 = now.tm_hour % 12
    if hour_12 == 0:
        hour_12 = 12
    am_pm = "AM" if now.tm_hour < 12 else "PM"

    return "{}, {} {} {}, {}:{:02d} {}".format(
        weekday_str, month_str, day, year, hour_12, now.tm_min, am_pm
    )

def update_display():
    """Refresh the screen based on current view."""
    magtag.set_text("", header_index)
    magtag.set_text("", content_index)

    if current_view == "weather":
        magtag.set_text(format_datetime(time.localtime()), header_index)
        magtag.set_text(weather_str, content_index)
    elif current_view == "forecast":
        magtag.set_text("5-Day Forecast", header_index)
        magtag.set_text(forecast_str, content_index)
    elif current_view == "news":
        magtag.set_text("News Headlines", header_index)
        # Determine how many pages there are:
        num_pages = max(1, (len(news_list) + 1) // 2)
        # Compute start and end indices for the current page (2 headlines per page)
        start_index = news_page * 2
        end_index = start_index + 2
        display_news = "\n\n".join(news_list[start_index:end_index])
        magtag.set_text(display_news, content_index)

    magtag.refresh()

# -------------------------------------------------
# Main Program Flow
# -------------------------------------------------
def main():
    global current_view, weather_str, forecast_str, news_list, news_page
    global last_weather_update, last_forecast_update, last_news_update

    connect_to_wifi()
    pool = socketpool.SocketPool(wifi.radio)
    sync_time(pool)
    session = adafruit_requests.Session(pool, ssl.create_default_context())

    weather_data = fetch_weather(session, CITY, secret.OPENWEATHERMAP_API_KEY)
    forecast_data = fetch_forecast(session, CITY, secret.OPENWEATHERMAP_API_KEY)
    weather_str = format_weather(weather_data, CITY)
    forecast_str = format_forecast(forecast_data)
    news_list = fetch_headlines(session)
    news_page = 0  # Start with the first two headlines

    update_display()

    while True:
        current_time = time.monotonic()

        # Button 0 (leftmost): toggle weather/forecast view
        if not magtag.peripherals.buttons[0].value:
            current_view = "forecast" if current_view == "weather" else "weather"
            update_display()
            time.sleep(0.5)

        # Button 1 (second from left): switch to news view or cycle through news pages
        if not magtag.peripherals.buttons[1].value:
            if current_view != "news":
                current_view = "news"
                news_page = 0  # Start with the first two headlines
            else:
                # Cycle to the next page of headlines
                num_pages = max(1, (len(news_list) + 1) // 2)
                news_page = (news_page + 1) % num_pages
            update_display()
            time.sleep(0.5)

        # (Button 2 currently has no functionality)

        # Timed updates
        if current_time - last_weather_update >= WEATHER_UPDATE_INTERVAL:
            weather_data = fetch_weather(session, CITY, secret.OPENWEATHERMAP_API_KEY)
            weather_str = format_weather(weather_data, CITY)
            if current_view == "weather":
                update_display()
            last_weather_update = current_time

        if current_time - last_forecast_update >= FORECAST_UPDATE_INTERVAL:
            forecast_data = fetch_forecast(session, CITY, secret.OPENWEATHERMAP_API_KEY)
            forecast_str = format_forecast(forecast_data)
            if current_view == "forecast":
                update_display()
            last_forecast_update = current_time

        if current_time - last_news_update >= NEWS_UPDATE_INTERVAL:
            news_list = fetch_headlines(session)
            if current_view == "news":
                update_display()
            last_news_update = current_time

        time.sleep(0.1)

# Run the program
main()
