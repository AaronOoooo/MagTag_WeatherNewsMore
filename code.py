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
import secret  # Contains OPENWEATHERMAP_API_KEY, WIFI_SSID, WIFI_PASSWORD, ALPHAVANTAGE_API_KEY
from adafruit_magtag.magtag import MagTag

# -------------------------------------------------
# Configuration Constants
# -------------------------------------------------
CITY = "Chicago"               # City for weather queries
TZ_OFFSET = -6                 # Time zone offset (CST is UTC-6)
TIME_UPDATE_INTERVAL = 60      # Update time every 60 seconds
WEATHER_UPDATE_INTERVAL = 300  # Update weather every 5 minutes
FORECAST_UPDATE_INTERVAL = 1800  # Update forecast every 30 minutes
NEWS_UPDATE_INTERVAL = 900     # Update news every 15 minutes (900 seconds)
STOCK_UPDATE_INTERVAL = 3600   # Update stocks at the top of every hour

# Define stock groups.
STOCKS_GROUP_1 = ["DJIA", "IXIC", "SPX"]
STOCKS_GROUP_2 = ["WMT", "GOOG", "V", "BDX", "META"]

# -------------------------------------------------
# Initialize MagTag and Global Variables
# -------------------------------------------------
magtag = MagTag()              # Create a MagTag object

# Set initial view mode: "weather", "forecast", "news", or "stocks".
current_view = "weather"

# Time markers for periodic updates.
last_weather_update = time.monotonic()
last_forecast_update = time.monotonic()
last_news_update = time.monotonic()
last_stock_update = 0  # Will update stock data at the top of every hour.

# Global variable for news headlines paging.
news_list = []   
news_page = 0  # 0: headlines 0-1, 1: headlines 2-3, 2: headlines 4-5

# Global dictionary for stock data.
stock_data = {}  # Keys: ticker symbols; Values: dict with "price", "change", "change_percent".

# Global variable to hold the formatted time when stock data was last fetched.
last_stock_time_str = "N/A"

# Global variable for stocks page (0: Group 1, 1: Group 2).
stocks_page = 0

# -------------------------------------------------
# Setup Display Text Fields
# -------------------------------------------------
header_index = magtag.add_text(
    text_font="/fonts/Arial-Bold-12.bdf",  # Bold font for headers/date-time.
    text_position=(5, 0),                  # Position at the top.
    text_color=0x000000,                   # Black text.
)

content_index = magtag.add_text(
    text_font="/fonts/Arial-12.bdf",       # Regular font for content.
    text_position=(5, 60),                 # Positioned below the header.
    text_color=0x000000,                   # Black text.
    line_spacing=0.7,                      # Tighter line spacing.
    # text_wrap=28,  # Uncomment to let the library handle text wrapping.
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
    """Synchronizes the real-time clock via NTP using the provided time zone offset."""
    print("Syncing time...")
    ntp = adafruit_ntp.NTP(pool, tz_offset=TZ_OFFSET)
    RTC().datetime = ntp.datetime  # Set RTC to current NTP time
    print("Time synced!")

def fetch_weather(session, city, api_key):
    """Fetches current weather data from OpenWeatherMap for the given city."""
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
    Fetches up to six news headlines from lite.cnn.com.
    Replaces unsupported glyphs with ASCII equivalents, wraps long headlines,
    and returns a list of formatted headlines.
    """
    url = "https://lite.cnn.com/en"
    print("Fetching headlines from lite.cnn.com...")
    response = session.get(url)
    html = response.text
    response.close()

    # Dictionary for replacing fancy punctuation with plain ASCII.
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
        """Wraps a string so that each line does not exceed max_chars."""
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

def fetch_stock_data(session):
    """
    Fetches stock data for specified ticker symbols from Alpha Vantage's Global Quote endpoint.
    Updates the global 'stock_data' dictionary with the latest price, change, and change percent.
    Also updates 'last_stock_time_str' with the current time in the format:
      "h:mm pm Weekday" (e.g., "1:04 pm Monday").
    """
    global stock_data, last_stock_time_str
    # Combine symbols from both groups (remove duplicates)
    symbols = list(set(STOCKS_GROUP_1 + STOCKS_GROUP_2))
    for symbol in symbols:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={secret.ALPHAVANTAGE_API_KEY}"
        try:
            response = session.get(url)
            data = response.json()
            response.close()
            quote = data.get("Global Quote", {})
            price = quote.get("05. price", "N/A")
            change = quote.get("09. change", "0")
            change_percent = quote.get("10. change percent", "0%")
            stock_data[symbol] = {
                "price": price,
                "change": change,
                "change_percent": change_percent
            }
            print(f"Fetched stock data for {symbol}: {stock_data[symbol]}")
        except Exception as e:
            print(f"Error fetching stock data for {symbol}: {e}")
    # Update the last stock retrieval time using our custom format.
    last_stock_time_str = format_stock_time(time.localtime())

def format_stock_time(now):
    """
    Returns the current time in the format "h:mm pm Weekday"
    (e.g., "1:04 pm Monday") using 12-hour time in CST.
    """
    hour = now.tm_hour % 12
    if hour == 0:
        hour = 12
    minute = now.tm_min
    am_pm = "am" if now.tm_hour < 12 else "pm"
    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday = weekday_names[now.tm_wday]
    return f"{hour}:{minute:02d} {am_pm} {weekday}"

def format_stock_view(group):
    """
    Formats stock information for a given group (list of ticker symbols) into a multi-line string.
    Displays the symbol, current price, change, and change percent, formatted to two decimals.
    Ticker symbols are sorted alphabetically.
    """
    lines = []
    for symbol in sorted(group):
        info = stock_data.get(symbol, {})
        try:
            price = float(info.get("price", 0))
            price_str = f"{price:.2f}"
        except:
            price_str = "N/A"
        try:
            change = float(info.get("change", 0))
            change_str = f"{change:.2f}"
        except:
            change_str = "0.00"
        cp = info.get("change_percent", "0%")
        try:
            cp_val = float(cp.strip('%'))
            cp_str = f"{cp_val:.2f}%"
        except:
            cp_str = "0.00%"
        line = f"{symbol}: ${price_str}  {change_str} ({cp_str})"
        lines.append(line)
    return "\n".join(lines)

def format_weather(data, city):
    """
    Formats current weather data into a multi-line string.
    Rounds temperatures and adjusts sunrise/sunset times using TZ_OFFSET.
    """
    temp = round(data["main"]["temp"])
    temp_max = round(data["main"]["temp_max"])
    temp_min = round(data["main"]["temp_min"])
    feels_like = round(data["main"]["feels_like"])
    humidity = data["main"]["humidity"]
    wind_speed = round(data["wind"]["speed"])
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
    Formats a 5-day forecast into a multi-line string by selecting every 8th data point.
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
    Refreshes the MagTag display based on the current view and updates the NeoPixel LEDs.
    
    LED Indicators:
      - **Weather/Forecast view:** The right-most LED (LED 3) is lit white (weather) or blue (forecast).
      - **News view:** The second-from-right LED (LED 2) is lit based on the news page:
                      white for page 0, green for page 1, and orange for page 2.
      - **Stocks view:** The header shows "Stock info as of <time>" and the left-most LED (LED 0) lights purple.
    """
    magtag.set_text("", header_index)
    magtag.set_text("", content_index)
    
    # Clear the LEDs used for indication.
    # LED 3: Right-most, LED 2: Second-from-right, LED 0: Left-most.
    magtag.peripherals.neopixels[3] = (0, 0, 0)
    magtag.peripherals.neopixels[2] = (0, 0, 0)
    magtag.peripherals.neopixels[0] = (0, 0, 0)
    
    if current_view == "weather":
        magtag.set_text(format_datetime(time.localtime()), header_index)
        magtag.set_text(weather_str, content_index)
        # In weather view, light the right-most LED (LED 3) white.
        magtag.peripherals.neopixels[3] = (255, 255, 255)
    elif current_view == "forecast":
        magtag.set_text("5-Day Forecast", header_index)
        magtag.set_text(forecast_str, content_index)
        # In forecast view, light the right-most LED (LED 3) blue.
        magtag.peripherals.neopixels[3] = (0, 0, 255)
    elif current_view == "news":
        magtag.set_text("News Headlines", header_index)
        start_index = news_page * 2
        end_index = start_index + 2
        display_news = "\n\n".join(news_list[start_index:end_index])
        magtag.set_text(display_news, content_index)
        # In news view, light the second-from-right LED (LED 2) based on news_page.
        if news_page == 0:
            magtag.peripherals.neopixels[2] = (255, 255, 255)  # white
        elif news_page == 1:
            magtag.peripherals.neopixels[2] = (0, 255, 0)      # green
        elif news_page == 2:
            magtag.peripherals.neopixels[2] = (255, 165, 0)    # orange
    elif current_view == "stocks":
        # Set header with last stock retrieval time in format "Stock info as of h:mm pm Weekday".
        header_text = "Stock info as of " + last_stock_time_str
        magtag.set_text(header_text, header_index)
        # Select stock group based on stocks_page.
        if stocks_page == 0:
            group = STOCKS_GROUP_1
        else:
            group = STOCKS_GROUP_2
        display_stocks = format_stock_view(group)
        magtag.set_text(display_stocks, content_index)
        # In stocks view, light the left-most LED (LED 0) purple.
        magtag.peripherals.neopixels[0] = (128, 0, 128)
    magtag.refresh()

def main():
    """
    Main function:
      - Connects to Wi-Fi and synchronizes time.
      - Fetches weather, forecast, news, and stock data.
      - Checks for button presses to switch views.
      - Performs periodic updates.
    """
    global current_view, weather_str, forecast_str, news_list, news_page
    global last_weather_update, last_forecast_update, last_news_update, last_stock_update
    global stock_data, stocks_page, last_stock_time_str

    connect_to_wifi()  # Connect to Wi-Fi.
    pool = socketpool.SocketPool(wifi.radio)
    sync_time(pool)    # Synchronize time with NTP.
    session = adafruit_requests.Session(pool, ssl.create_default_context())

    # Fetch initial weather, forecast, and news data.
    weather_data = fetch_weather(session, CITY, secret.OPENWEATHERMAP_API_KEY)
    forecast_data = fetch_forecast(session, CITY, secret.OPENWEATHERMAP_API_KEY)
    weather_str = format_weather(weather_data, CITY)
    forecast_str = format_forecast(forecast_data)
    news_list = fetch_headlines(session)
    news_page = 0  # Start with the first two headlines.

    # Fetch initial stock data.
    stock_data = {}
    stocks_page = 0  # 0: Group 1 (DJIA, IXIC, SPX), 1: Group 2 (WMT, GOOG, V, BDX, META).
    fetch_stock_data(session)
    last_stock_update = time.monotonic()

    update_display()  # Update the display with initial data.

    while True:
        current_time = time.monotonic()
        local_time = time.localtime()

        # Button 0 (left-most): Toggle between weather and forecast views.
        if not magtag.peripherals.buttons[0].value:
            current_view = "forecast" if current_view == "weather" else "weather"
            update_display()
            time.sleep(0.5)

        # Button 1 (second from left): Switch to news view or cycle through news pages.
        if not magtag.peripherals.buttons[1].value:
            if current_view != "news":
                current_view = "news"
                news_page = 0
            else:
                num_pages = max(1, (len(news_list) + 1) // 2)
                news_page = (news_page + 1) % num_pages
            update_display()
            time.sleep(0.5)

        # Button 2 (third from left): Switch to stocks view or toggle between stock pages.
        if not magtag.peripherals.buttons[2].value:
            if current_view != "stocks":
                current_view = "stocks"
                stocks_page = 0
            else:
                stocks_page = 1 - stocks_page  # Toggle between 0 and 1.
            update_display()
            time.sleep(0.5)

        # Button 3 (fourth from left): Currently no functionality.

        # Periodic updates:
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

        # Update stock data at the top of every hour.
        if local_time.tm_min == 0 and (current_time - last_stock_update) >= STOCK_UPDATE_INTERVAL:
            fetch_stock_data(session)
            if current_view == "stocks":
                update_display()
            last_stock_update = current_time

        time.sleep(0.1)

# Run the main function.
main()
