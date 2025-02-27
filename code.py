import time
import adafruit_ntp
from rtc import RTC
import board
import wifi
import socketpool
import ssl
import adafruit_requests as requests
import secret  # Contains your OPENWEATHERMAP_API_KEY, WIFI_SSID, and WIFI_PASSWORD

from adafruit_magtag.magtag import MagTag

# Custom text wrap function that breaks text into lines of a given character width.
def wrap_text(text, width):
    words = text.split(" ")
    lines = []
    current_line = ""
    for word in words:
        if current_line:
            test_line = current_line + " " + word
        else:
            test_line = word
        # If adding the next word exceeds the width, wrap to a new line.
        if len(test_line) > width:
            if current_line:  # Only add if there's already content
                lines.append(current_line)
            current_line = word  # Start a new line with the current word
        else:
            current_line = test_line
    if current_line:
        lines.append(current_line)
    return "\n".join(lines)

# ------------------------------
# Step 1: Connect to WiFi
# ------------------------------
print("Connecting to WiFi...")
wifi.radio.connect(secret.WIFI_SSID, secret.WIFI_PASSWORD)
print("Connected to WiFi!")

# ------------------------------
# Step 2: Set Up HTTP Session
# ------------------------------
pool = socketpool.SocketPool(wifi.radio)
http = requests.Session(pool, ssl.create_default_context())

# ------------------------------
# Step 3: Fetch Weather Data
# ------------------------------
city = "Chicago"  # Change to your desired city
url = "http://api.openweathermap.org/data/2.5/weather?q={}&appid={}&units=imperial".format(
    city, secret.OPENWEATHERMAP_API_KEY
)

print("Fetching weather data...")
response = http.get(url)
data = response.json()
response.close()

# Extract weather details
temp = data["main"]["temp"]
weather_description = data["weather"][0]["description"]
weather_info = "Weather in {}: {}°F, {}".format(city, temp, weather_description)
print(weather_info)

# ------------------------------
# Step 4: Initialize MagTag Display
# ------------------------------
magtag = MagTag()

# Add a text element using the specified font.
text_index = magtag.add_text(
    text_font="/fonts/Arial-Bold-12.bdf",
    text_position=(10, 10),
    text_color=0x000000,
    line_spacing=1.0,
)

# Wrap the weather info to prevent it from getting cut off.
wrapped_text = wrap_text(weather_info, 25)  # Adjust '25' as needed for your display

# Update the text element with the wrapped text.
magtag.set_text(wrapped_text, text_index)

# Refresh the display to show the updated text.
magtag.refresh()

# Optional: Pause to allow time to read the display.
time.sleep(10)
