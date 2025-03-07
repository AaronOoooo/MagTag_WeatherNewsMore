# Import necessary modules for time management, board functions, WiFi, HTTP requests, and NTP.
import time
import board
import wifi
import socketpool
import ssl
import adafruit_requests
import adafruit_ntp
from rtc import RTC

# Import secret configuration (WiFi credentials, API keys) and the MagTag library.
import secret  # Contains OPENWEATHERMAP_API_KEY, WIFI_SSID, WIFI_PASSWORD
from adafruit_magtag.magtag import MagTag

# -------------------------------------------------
# Configuration Constants
# -------------------------------------------------
CITY = "Chicago"               # City name for weather queries
TZ_OFFSET = -6                 # Time zone offset (CST is UTC-6)
TIME_UPDATE_INTERVAL = 60      # Update time every 60 seconds
WEATHER_UPDATE_INTERVAL = 300  # Update weather every 5 minutes
FORECAST_UPDATE_INTERVAL = 1800  # Update forecast every 30 minutes
NEWS_UPDATE_INTERVAL = 900     # Update news every 15 minutes (900 seconds)

# -------------------------------------------------
# Initialize MagTag and Global Variables
# -------------------------------------------------
magtag = MagTag()              # Create a MagTag object

# Set initial view mode: "weather" by default.
current_view = "weather"

# Time markers for last updates (using time.monotonic for elapsed time measurement).
last_weather_update = time.monotonic()
last_forecast_update = time.monotonic()
last_news_update = time.monotonic()

# Global variable to hold fetched news headlines.
# We'll fetch up to six headlines. These will be paged two-at-a-time.
news_list = []   
news_page = 0  # News page: 0 means headlines 0-1, 1 means headlines 2-3, and 2 means headlines 4-5

# -------------------------------------------------
# Setup Display Text Fields
# -------------------------------------------------
# Header text (e.g., for displaying the current time or titles).
header_index = magtag.add_text(
    text_font="/fonts/Arial-Bold-12.bdf",  # Bold font for headers
    text_position=(5, 0),                  # X and Y position on the display
    text_color=0x000000,                   # Black text
)

# Content text (e.g., for weather details, forecasts, or news headlines).
content_index = magtag.add_text(
    text_font="/fonts/Arial-12.bdf",       # Regular font for body text
    text_position=(5, 60),                 # Position below the header
    text_color=0x000000,                   # Black text
    line_spacing=0.7,                      # Adjust line spacing as desired
    # text_wrap=28,  # Uncomment to let the library handle text wrapping automatically
)

# -------------------------------------------------
# Function Definitions
# -------------------------------------------------

def connect_to_wifi():
    """Connects to Wi-Fi using credentials stored in secret.py."""
    print("Connecting to WiFi...")
    wifi.radio.connect(secret.WIFI_SSID, secret.WIFI_PASSWORD)
    print("Connected!")

def sync_time(pool):
    """Synchronizes the real-time clock via an NTP server using the provided time zone offset."""
    print("Syncing time...")
    ntp = adafruit_ntp.NTP(pool, tz_offset=TZ_OFFSET)
    RTC().datetime = ntp.datetime  # Set RTC to current NTP time
    print("Time synced!")

def fetch_weather(session, city, api_key):
    """Fetches the current weather from OpenWeatherMap for the given city."""
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=imperial"
    print("Fetching weather...")
    response = session.get(url)
    data = response.json()  # Parse JSON response
    response.close()
    return data

def fetch_forecast(session, city, api_key):
    """Fetches a 5-day weather forecast (in 3-hour increments) from OpenWeatherMap."""
    url = f"http://api.openweathermap.org/data/2.5/forecast?q={city}&appid={api_key}&units=imperial"
    print("Fetching forecast...")
    response = session.get(url)
    data = response.json()
    response.close()
    return data

def fetch_headlines(session):
    """
    Fetches up to six headlines from lite.cnn.com.
    This function replaces unsupported glyphs with ASCII equivalents,
    wraps long headlines, and returns a list of formatted headlines.
    """
    url = "https://lite.cnn.com/en"
    print("Fetching headlines from lite.cnn.com...")
    response = session.get(url)
    html = response.text
    response.close()

    # Dictionary for replacing curly quotes and other fancy punctuation with plain ASCII.
    replace_map = {
        "’": "'",
        "‘": "'",
        "“": '"',
        "”": '"',
        "—": "-",
        "–": "-",
        "…": "...",
    }

    def wrap_text(text, max_chars=38):
        """
        Wraps a string so that each line does not exceed max_chars.
        Returns the wrapped text with newline characters.
        """
        words = text.split()
        lines = []
        current_line = []
        current_length = 0
        for w in words:
            # If adding the next word exceeds max_chars, start a new line.
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
    # Split HTML by list item tags.
    parts = html.split("<li ")
    for part in parts[1:]:
        if "<a href=" not in part:
            continue
        a_start = part.find("<a href=")
        anchor_close = part.find(">", a_start)
        anchor_end = part.find("</a>", anchor_close)
        if anchor_close == -1 or anchor_end == -1:
            continue
        # Extract the headline text.
        headline = part[anchor_close+1:anchor_end].strip()
        if "Terms" in headline or "Privacy" in headline:
            continue
        # Replace any unsupported glyphs.
        for old_char, new_char in replace_map.items():
            headline = headline.replace(old_char, new_char)
        # Wrap the headline text.
        wrapped = wrap_text(headline, max_chars=38)
        if len(wrapped) > 5:
            headlines.append(wrapped)
        if len(headlines) >= 6:
            break
    return headlines

def format_weather(data, city):
    """
    Formats current weather data into a multi-line string.
    Temperatures are rounded to whole numbers.
    Adjusts sunrise and sunset times using the configured time zone offset.
    """
    temp = round(data["main"]["temp"])
    temp_max = round(data["main"]["temp_max"])
    temp_min = round(data["main"]["temp_min"])
    feels_like = round(data["main"]["feels_like"])
    humidity = data["main"]["humidity"]
    wind_speed = round(data["wind"]["speed"])
    
    # Convert UTC timestamps to local time by adding the offset in seconds.
    sunrise = time.localtime(data["sys"]["sunrise"] + (TZ_OFFSET * 3600))
    sunset = time.localtime(data["sys"]["sunset"] + (TZ_OFFSET * 3600))
    sunrise_time = "{}:{:02d} AM".format(sunrise.tm_hour, sunrise.tm_min)
    # Convert sunset time to 12-hour format.
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
    Formats the 5-day forecast into a multi-line string.
    Uses every 8th data point (approx. one per day).
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
    Returns a formatted string representing the current date and time.
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
    """
    Updates the MagTag display based on the current view.
    Also sets the NeoPixel LED indicators as follows:
      - Weather view: Right-most LED (LED 3) is lit white.
      - Forecast view: Right-most LED (LED 3) is lit blue.
      - News view: Second from right LED (LED 2) is lit with a color based on the current news page:
                  white for page 0, green for page 1, and orange for page 2.
    """
    magtag.set_text("", header_index)
    magtag.set_text("", content_index)
    
    # Clear the specific LEDs used for indication.
    # For this configuration, we assume:
    #   LED 3 is the right-most LED.
    #   LED 2 is the second from the right.
    magtag.peripherals.neopixels[3] = (0, 0, 0)
    magtag.peripherals.neopixels[2] = (0, 0, 0)
    
    if current_view == "weather":
        magtag.set_text(format_datetime(time.localtime()), header_index)
        magtag.set_text(weather_str, content_index)
        # Light the right-most LED (LED 3) white in weather view.
        magtag.peripherals.neopixels[3] = (255, 255, 255)
    elif current_view == "forecast":
        magtag.set_text("5-Day Forecast", header_index)
        magtag.set_text(forecast_str, content_index)
        # Light the right-most LED (LED 3) blue in forecast view.
        magtag.peripherals.neopixels[3] = (0, 0, 255)
    elif current_view == "news":
        magtag.set_text("News Headlines", header_index)
        # Determine which two headlines to display based on the current news page.
        start_index = news_page * 2
        end_index = start_index + 2
        display_news = "\n\n".join(news_list[start_index:end_index])
        magtag.set_text(display_news, content_index)
        # In news view, do not light the right-most LED.
        magtag.peripherals.neopixels[3] = (0, 0, 0)
        # Light the second from right LED (LED 2) based on news_page:
        if news_page == 0:
            magtag.peripherals.neopixels[2] = (255, 255, 255)  # white
        elif news_page == 1:
            magtag.peripherals.neopixels[2] = (0, 255, 0)      # green
        elif news_page == 2:
            magtag.peripherals.neopixels[2] = (255, 165, 0)    # orange
    magtag.refresh()

def main():
    """
    Main function:
      - Connects to Wi-Fi and synchronizes time.
      - Fetches weather, forecast, and news data.
      - Enters a loop to update the display and cycle between different views
        based on button presses.
    """
    global current_view, weather_str, forecast_str, news_list, news_page
    global last_weather_update, last_forecast_update, last_news_update

    connect_to_wifi()  # Connect to Wi-Fi
    pool = socketpool.SocketPool(wifi.radio)
    sync_time(pool)    # Synchronize time with NTP
    session = adafruit_requests.Session(pool, ssl.create_default_context())

    # Fetch initial weather, forecast, and news data.
    weather_data = fetch_weather(session, CITY, secret.OPENWEATHERMAP_API_KEY)
    forecast_data = fetch_forecast(session, CITY, secret.OPENWEATHERMAP_API_KEY)
    weather_str = format_weather(weather_data, CITY)
    forecast_str = format_forecast(forecast_data)
    news_list = fetch_headlines(session)
    news_page = 0  # Start by displaying the first two headlines

    update_display()  # Update the display with the initial data

    # Main loop to update the display based on button presses and timed updates.
    while True:
        current_time = time.monotonic()

        # Button 0 (left-most button) toggles between weather and forecast views.
        if not magtag.peripherals.buttons[0].value:
            current_view = "forecast" if current_view == "weather" else "weather"
            update_display()
            time.sleep(0.5)  # Debounce delay

        # Button 1 (second from left) switches to news view or cycles through news pages.
        if not magtag.peripherals.buttons[1].value:
            if current_view != "news":
                current_view = "news"
                news_page = 0  # Start with first set of news headlines
            else:
                num_pages = max(1, (len(news_list) + 1) // 2)
                news_page = (news_page + 1) % num_pages  # Cycle through news pages
            update_display()
            time.sleep(0.5)

        # Button 2 (third from left) currently has no functionality.
        # (Placeholder for future features.)

        # Periodic updates for weather, forecast, and news.
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

        time.sleep(0.1)  # Small delay for responsiveness

# Run the main function
main()
