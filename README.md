# Adafruit MagTag Weather Display

This project displays current weather information and the current date/time on an Adafruit MagTag e‑ink display. The device connects to Wi‑Fi, synchronizes its real‑time clock (RTC) via NTP, and fetches weather data from the OpenWeatherMap API. The display is updated periodically: the time every 60 seconds and the weather every 5 minutes.

The "Today" section (left side) shows detailed current weather—including extra info like humidity, wind speed, sunrise/sunset times, min/max temperatures, and what the temperature feels like—while the "Forecast" section (right side) is reserved for a five‑day forecast with weather icons (BMP files) that you will provide.

## Features

- **Current Weather Display**  
  - Displays current temperature, "feels like" temperature, humidity, wind speed, sunrise/sunset times, and min/max temperatures.
  - Shows a weather description with text wrapping.

- **Date/Time Display**  
  - Shows the current date and time in abbreviated form (e.g., "Mon, Jan 1 2025, 7:05 PM") using a small font.

- **Periodic Updates**  
  - Time updates every 60 seconds.
  - Weather (both current conditions and forecast) updates every 5 minutes.

- **Modular Code Structure**  
  - The code is organized into functions for Wi‑Fi connection, time synchronization, weather fetching, formatting, and display updates.

- **Customizable Layout**  
  - Uses displayio to draw borders and divide the screen into "Today" and "Future" sections.
  - Forecast icons (BMP files) are displayed on the right side for a 5‑day forecast.

## Requirements

### Hardware
- **Adafruit MagTag** with a 296×128 pixel e‑ink display.
- A stable Wi‑Fi connection.

### Software
- **CircuitPython** installed on your MagTag.
- Required libraries (placed in the `lib` folder on CIRCUITPY):
  - `adafruit_requests`
  - `adafruit_ntp`
  - `adafruit_magtag`
- Font files (placed in a `/fonts` folder on CIRCUITPY):
  - `Arial-Bold-12.bdf` (for date/time)
  - `Helvetica-Bold-16.bdf` (for current weather)
- (Optional) BMP icon files for the forecast, to be placed in an `/icons` folder.

### API
- An OpenWeatherMap API key (the free version is sufficient).

### Configuration File
- A `secret.py` file containing:
  ```python
  WIFI_SSID = "your_wifi_ssid"
  WIFI_PASSWORD = "your_wifi_password"
  OPENWEATHERMAP_API_KEY = "your_openweathermap_api_key"


Installation
Clone or Download the Repository
Clone this repository or download the project files onto your computer.

Create the secret.py File
In the root of your project, create a file named secret.py and add your Wi‑Fi credentials and OpenWeatherMap API key as shown above.

Install Required Libraries
Download the latest versions of the required libraries from the Adafruit CircuitPython Bundle and copy them into the lib folder on your CIRCUITPY drive.

Add Font Files
Place the required font files (Arial-Bold-12.bdf and Helvetica-Bold-16.bdf) in a folder named /fonts on your CIRCUITPY drive.

(Optional) Add Forecast Icons
Create an /icons folder on CIRCUITPY and add BMP files for the forecast icons (naming them by their OpenWeatherMap icon code, e.g., 10d.bmp).

Upload the Code
Copy the provided code.py file into your CIRCUITPY drive.

Usage
Power on or Reset the MagTag
The device will automatically connect to your Wi‑Fi, sync the time via NTP, and fetch current weather data from OpenWeatherMap.

Display Behavior

The "Today" section (left side) will show current weather details along with the date/time.
The "Forecast" section (right side) is set up for a 5‑day forecast with icons.
Periodic Updates

The time is refreshed every 60 seconds.
The weather is refreshed every 5 minutes.
Code Structure
The code is organized into modular functions:

Wi‑Fi and Time Synchronization

connect_to_wifi(): Connects to Wi‑Fi using credentials from secret.py.
sync_time(pool, tz_offset): Synchronizes the RTC with an NTP server.
Weather Data Handling

fetch_weather(session, city, api_key): Retrieves current weather data.
format_weather(data, city): Formats the weather data into a multi‑line string.
Date/Time Formatting

format_datetime(now): Formats the current date/time into a concise, abbreviated string.
Display Updates

update_time_display(magtag, date_index): Updates the time display.
update_weather_display(magtag, weather_index, session, city, api_key): Updates the weather display.
Main Loop
The main loop updates the displayed time every minute and the weather every 5 minutes.

Customization
City and Timezone
Change the CITY constant and adjust TZ_OFFSET as needed.

Update Intervals
Modify TIME_UPDATE_INTERVAL and WEATHER_UPDATE_INTERVAL in the code to change how frequently the data is refreshed.

Fonts and Layout
Adjust the text positions and font sizes by editing the text_position and text_font parameters in the code.

Forecast Icons
Supply your own BMP files for forecast icons in the /icons folder, naming them according to OpenWeatherMap icon codes.

Troubleshooting
Wi‑Fi Issues
Ensure your credentials in secret.py are correct.

Library Errors
Verify that all required libraries are present in the lib folder.

Font Issues
Confirm that the font files are correctly placed in the /fonts directory.

API Errors
Check that your OpenWeatherMap API key is valid and you haven't exceeded rate limits.

License
This project is provided "as-is" with no warranty. You are free to use, modify, and distribute this code. Please include proper attribution if you use this project as the basis for your own work.