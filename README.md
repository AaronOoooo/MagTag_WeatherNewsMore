# Adafruit MagTag Weather Display

This project uses an **Adafruit MagTag** e‑ink display to show current weather information and a 5‑day forecast. The device connects to Wi‑Fi, synchronizes its time via NTP, and fetches weather data from OpenWeatherMap. You can toggle between the current weather and forecast views by pressing the leftmost button (Button A) on the MagTag.

---

## Features

- **Current Weather Display**  
  - Shows temperature, "feels like" temperature, humidity, wind speed, sunrise/sunset, and daily highs/lows.  
  - Temperatures are displayed as whole numbers (rounded).

- **5‑Day Forecast**  
  - Displays one forecast entry per day by selecting every 8th data point from the 3‑hourly forecast data.

- **Date/Time Display**  
  - Shows an abbreviated weekday, month, day, year, and 12‑hour format time with AM/PM.  
  - Time is refreshed every **60 seconds**.

- **Wi‑Fi & NTP**  
  - Automatically connects to Wi‑Fi using credentials from `secret.py`.  
  - Synchronizes time via an NTP server using the configured time zone offset.

- **Periodic Updates**  
  - Weather updates every **5 minutes**.  
  - Forecast updates every **30 minutes**.

- **User Interaction**  
  - Press Button A to switch between the current weather and forecast views.

---

## Requirements

### Hardware
- **Adafruit MagTag** with a 2.9" e‑ink display.
- A stable Wi‑Fi access point.

### Software / Libraries
- **CircuitPython** installed on your MagTag.
- Libraries (placed in the `lib` folder on CIRCUITPY):
  - `adafruit_requests`
  - `adafruit_ntp`
  - `adafruit_magtag`
- **Font files** (placed in a `/fonts` folder on CIRCUITPY):
  - `Arial-Bold-12.bdf` (for header/date-time)
  - `Arial-12.bdf` (for weather/forecast content)

### API
- A valid **OpenWeatherMap API key** (the free tier is sufficient).

### `secret.py` File
Create a file named `secret.py` on your CIRCUITPY drive that contains:
```python
WIFI_SSID = "your_wifi_ssid"
WIFI_PASSWORD = "your_wifi_password"
OPENWEATHERMAP_API_KEY = "your_api_key_here"


Installation & Setup
Clone or Download the Project
Download the repository or clone it to your local machine.

Create secret.py
In the root of your CIRCUITPY drive, create a file named secret.py and add your Wi‑Fi credentials and OpenWeatherMap API key as shown above.

Install Required Libraries
Download the latest Adafruit CircuitPython Bundle and copy the required libraries (adafruit_requests, adafruit_ntp, adafruit_magtag) into the lib folder on your CIRCUITPY drive.

Add Font Files
Place Arial-Bold-12.bdf and Arial-12.bdf into a /fonts folder on your CIRCUITPY drive.

Upload the Code
Copy the provided code.py file into the root of your CIRCUITPY drive.

Usage
Power or Reset the MagTag
The device will automatically connect to Wi‑Fi, sync time via NTP, and fetch weather data.

Display Behavior

Weather View: Displays the current date/time at the top and the current weather details below.
Forecast View: Shows a simple 5‑day forecast (one line per day).
Toggle Views
Press Button A (the leftmost button) to switch between the weather view and the forecast view.

Periodic Updates

Time updates every 60 seconds.
Weather updates every 5 minutes.
Forecast updates every 30 minutes.
Code Structure
Global Configuration:

CITY (default: "Chicago")
TZ_OFFSET (time zone offset, default: -6 for CST)
Update intervals for time, weather, and forecast are defined at the top of the code.
Functions:

connect_to_wifi(): Connects to Wi‑Fi using credentials in secret.py.
sync_time(pool): Synchronizes time with an NTP server.
fetch_weather(session, city, api_key): Retrieves current weather data from OpenWeatherMap.
fetch_forecast(session, city, api_key): Retrieves a 5‑day forecast (3‑hour increments) from OpenWeatherMap.
format_weather(data, city): Converts raw current weather data into a multi‑line string with rounded temperatures.
format_forecast(data): Generates a 5‑day forecast string by selecting every 8th data point and rounding temperatures.
format_datetime(now): Returns a formatted date/time string (e.g., "Sat, Mar 1 2025, 7:05 PM").
update_display(): Clears the display and updates it with either current weather or forecast text.
Main Loop:
Checks for button presses (to toggle views), periodically refetches data, and refreshes the display.

Customization
City & Time Zone:
Modify the CITY and TZ_OFFSET constants at the top of the code.

Refresh Intervals:
Change TIME_UPDATE_INTERVAL, WEATHER_UPDATE_INTERVAL, and FORECAST_UPDATE_INTERVAL as needed.

Fonts & Layout:
Adjust text_position, line_spacing, and text_wrap (if needed) in the code to customize the display.

Temperature Rounding:
Temperatures are rounded to whole numbers using round(). Change this to int() if you prefer truncation.

Troubleshooting
Wi‑Fi Issues:
Verify that the Wi‑Fi credentials in secret.py are correct.

API Errors:
Ensure your OpenWeatherMap API key is valid and active.

Font Issues:
Confirm that the required .bdf font files are placed in the /fonts folder on CIRCUITPY.

Library Issues:
Check that all required libraries are present in the lib folder on your CIRCUITPY drive.

License
This project is provided "as-is" without any warranty. You are free to use, modify, and distribute this code. If you use this project in your own work, please provide appropriate attribution.

