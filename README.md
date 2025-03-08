# 🌟 Adafruit MagTag Weather, Forecast, News, & Stocks Display 🌟

This project transforms your **Adafruit MagTag** into a versatile information hub that shows:
- **Current Weather** (with local forecasts)
- **5‑Day Forecast**
- **Latest News Headlines**
- **Real-Time Stock Market Data**

All data is fetched via APIs and updated periodically, while the built‑in NeoPixels offer dynamic visual feedback on the active view.

---

## ✨ Features ✨

### Weather & Forecast
- **Current Weather:**  
  - Displays temperature, “feels like” temperature, high/low values, humidity, wind speed, and sunrise/sunset times.
  - Uses the right‑most LED (LED 3) to indicate the weather view (lit **white**).
  
- **5‑Day Forecast:**  
  - Shows one forecast entry per day by selecting every 8th data point from the 3‑hour forecast.
  - In forecast view, the right‑most LED (LED 3) lights **blue**.

### News Headlines
- **News Display:**  
  - Retrieves up to six headlines from [lite.cnn.com](https://lite.cnn.com/en) and displays them two at a time.
  - Press **Button 1** (second from left) to cycle through news pages:
    - **Page 0:** Headlines 1–2, with the second‑from‑right LED (LED 2) lit **white**.
    - **Page 1:** Headlines 3–4, with LED 2 lit **green**.
    - **Page 2:** Headlines 5–6, with LED 2 lit **orange**.

### Stock Market Data
- **Stocks View:**  
  - Powered by **Alpha Vantage**, this view fetches and displays key stock data.
  - Two groups of tickers are supported:
    - **Group 1:** DJIA, IXIC, SPX
    - **Group 2:** WMT, GOOG, V, BDX, META  
  - Ticker symbols are shown in **alphabetical order**, with prices and percentage changes formatted to two decimal places.
  - The header displays the text:  
    **"Stock info as of 1:04 pm Monday"** (example)  
    indicating the time the stock data was last fetched.
  - In stocks view, the left‑most LED (LED 0) lights **purple**.

### System Integration & Updates
- **Wi‑Fi & NTP:**  
  - Automatically connects to Wi‑Fi using credentials from `secret.py`.
  - Synchronizes time via NTP using your specified time zone (default is CST, UTC‑6).

- **Periodic Data Updates:**  
  - Weather data updates every **5 minutes**.
  - Forecast updates every **30 minutes**.
  - News headlines refresh every **15 minutes**.
  - Stock data is fetched **at the top of every hour**.

- **User Interaction & Button Mapping:**  
  - **Button 0 (left‑most):** Toggles between weather and forecast views.
  - **Button 1 (second from left):** Switches to news view or cycles through news pages.
  - **Button 2 (third from left):** Activates the stocks view (and toggles between stock groups).
  - **Button 3 (fourth from left):** Currently reserved for future use.

---

## 🛠️ Requirements

### Hardware
- **Adafruit MagTag** with a 2.9" e‑ink display and **4 NeoPixels** (positioned along the top).
- A reliable Wi‑Fi access point.

### Software / Libraries
- **CircuitPython** installed on your MagTag.
- Required libraries in the `lib` folder on your CIRCUITPY drive:
  - `adafruit_requests`
  - `adafruit_ntp`
  - `adafruit_magtag`
- **Font Files:**  
  Place `Arial-Bold-12.bdf` (for headers/date-time) and `Arial-12.bdf` (for body text) in a `/fonts` folder on your CIRCUITPY drive.

### API Keys
- A valid **OpenWeatherMap API key**.
- A valid **Alpha Vantage API key**.

### `secret.py` File
Create a file named `secret.py` on your CIRCUITPY drive with content similar to:

```python
WIFI_SSID = "your_wifi_ssid"
WIFI_PASSWORD = "your_wifi_password"
OPENWEATHERMAP_API_KEY = "your_openweathermap_api_key"
ALPHAVANTAGE_API_KEY = "your_alphavantage_api_key"


=========================================

 Installation & Setup
Clone or Download the Project:
Download the repository or clone it to your local machine.

Create secret.py:
In the root of your CIRCUITPY drive, create secret.py and enter your Wi‑Fi credentials and API keys as shown above.

Install Required Libraries:
Download the latest Adafruit CircuitPython Bundle and copy the required libraries into the lib folder on your CIRCUITPY drive.

Add Font Files:
Place Arial-Bold-12.bdf and Arial-12.bdf into a /fonts folder on your CIRCUITPY drive.

Upload the Code:
Copy the provided code.py file into the root of your CIRCUITPY drive.

Power or Reset the MagTag:
The device will automatically connect to Wi‑Fi, sync time, and begin fetching and displaying data.

📖 Usage
Weather/Forecast Views:

Weather View: Displays current weather data with the right‑most LED (LED 3) lit white.
Forecast View: Displays a 5‑day forecast with the right‑most LED (LED 3) lit blue.
Toggle: Press Button 0 to switch between weather and forecast views.
News View:

Press Button 1 to switch to news view, which displays headlines in pages (2 headlines per page).
Cycle through pages by pressing Button 1 repeatedly.
The second‑from‑right LED (LED 2) indicates the current news page (white, green, or orange).
Stocks View:

Press Button 2 to switch to the stocks view.
Stocks view displays key data for two groups of ticker symbols (sorted alphabetically) with prices and percentage changes formatted to two decimal places.
The header will show the retrieval time in the format "Stock info as of 1:04 pm Monday".
The left‑most LED (LED 0) lights purple in stocks view.
Automatic Updates:
Data updates occur automatically:

Time: Every 60 seconds.
Weather: Every 5 minutes.
Forecast: Every 30 minutes.
News: Every 15 minutes.
Stocks: At the top of every hour.
🗂️ Code Structure
Global Configuration:
All key settings (city, time zone offset, update intervals) are defined at the top.

Function Definitions:

connect_to_wifi(): Connects to Wi‑Fi using secret.py.
sync_time(pool): Synchronizes time via NTP.
fetch_weather(), fetch_forecast(): Retrieve weather data from OpenWeatherMap.
fetch_headlines(): Retrieves and formats news headlines from CNN Lite.
fetch_stock_data(): Retrieves stock data from Alpha Vantage.
format_stock_view(): Formats stock information for display.
format_weather(), format_forecast(), format_datetime(): Format data for display.
update_display(): Updates the display based on the active view and sets LED indicators.
Main Loop:
The main loop monitors button presses to switch views (weather, forecast, news, stocks) and updates the displayed data at set intervals.

🔧 Troubleshooting
Wi‑Fi Issues:
Verify that your Wi‑Fi credentials in secret.py are correct.

API Errors:
Make sure your API keys (OpenWeatherMap and Alpha Vantage) are valid and active.

Font Issues:
Confirm that the required .bdf font files are placed in the /fonts folder.

Library Issues:
Check that all necessary libraries are in the lib folder on your CIRCUITPY drive.

📜 License
This project is provided "as-is" without any warranty. You are free to use, modify, and distribute the code. If you use this project in your own work, please provide appropriate attribution.