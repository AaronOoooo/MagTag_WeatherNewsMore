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
# Step 1: Connect to Wi-Fi
# ------------------------------
print("Connecting to WiFi...")
wifi.radio.connect(secret.WIFI_SSID, secret.WIFI_PASSWORD)
print("Connected to WiFi!")

# ------------------------------
# Step 2: Sync Time via NTP
# ------------------------------
pool = socketpool.SocketPool(wifi.radio)
# Adjust tz_offset for your local timezone (e.g., -6 for CST, -5 for CDT in Chicago)
ntp = adafruit_ntp.NTP(pool, tz_offset=-6)
RTC().datetime = ntp.datetime
print("Time synced via NTP!")

# ------------------------------
# Step 3: Fetch Weather Data
# ------------------------------
http = adafruit_requests.Session(pool, ssl.create_default_context())

city = "Chicago"  # Change to your preferred city
url = (
    "http://api.openweathermap.org/data/2.5/weather?"
    "q={}&appid={}&units=imperial".format(city, secret.OPENWEATHERMAP_API_KEY)
)
print("Fetching weather data...")
response = http.get(url)
data = response.json()
response.close()

temp = data["main"]["temp"]
weather_description = data["weather"][0]["description"]

# Create weather string, placing everything after the comma on a new line
weather_info = "Weather in {}: {}°F,\n{}".format(city, temp, weather_description)
print(weather_info)

# ------------------------------
# Step 4: Prepare Abbreviated Date/Time Strings
# ------------------------------
now = time.localtime()

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

# Combine abbreviated day, month, date, and time on one line
datetime_str = "{}, {} {} {}, {}:{:02d} {}".format(
    weekday_str, month_str, day, year, hour_12, now.tm_min, am_pm
)
print(datetime_str)

# ------------------------------
# Step 5: Display on the MagTag
# ------------------------------
magtag = MagTag()

# 1) Date/Time in smaller font (Arial-Bold-12)
datetime_index = magtag.add_text(
    text_font="/fonts/Arial-Bold-12.bdf",
    text_position=(10, 10),
    text_color=0x000000,
)

# 2) Weather info in larger font (Helvetica-Bold-16), placed lower at y=50
weather_index = magtag.add_text(
    text_font="/fonts/Helvetica-Bold-16.bdf",
    text_position=(10, 50),
    text_color=0x000000,
)

# Set the text for each field
magtag.set_text(datetime_str, datetime_index)
magtag.set_text(weather_info, weather_index)

# Refresh the display to show the updates
magtag.refresh()

# Pause so you can read the display
time.sleep(10)
