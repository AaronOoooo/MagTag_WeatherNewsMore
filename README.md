# 🌟 Adafruit MagTag Weather, Forecast, and News Display 🌟

This project uses an **Adafruit MagTag** e‑ink display to show current weather information, a 5‑day forecast, and news headlines. The device connects to Wi‑Fi, synchronizes its time via NTP, and fetches data from OpenWeatherMap and CNN Lite. Visual indicators are provided by the built‑in NeoPixels.

---

## ✨ Features ✨

- **Current Weather Display**  
  - Displays temperature, "feels like" temperature, humidity, wind speed, sunrise/sunset, and daily highs/lows.  
  - Temperatures are rounded to whole numbers.  
  - The current date/time is updated every **60 seconds**.  
  - **LED Indicator:** When the weather view is active, the **right‑most LED (LED 3)** lights **white**.

- **5‑Day Forecast Display**  
  - Shows one forecast entry per day by selecting every 8th data point from the 3‑hourly forecast data.  
  - **LED Indicator:** In forecast view, the **right‑most LED (LED 3)** lights **blue**.

- **News Display**  
  - Fetches up to **six headlines** from [lite.cnn.com](https://lite.cnn.com/en) and pages them two at a time.  
  - Pressing **Button 1** cycles through the news pages:
    - **Page 0:** Headlines 1–2, with **LED 2** lighting **white**.  
    - **Page 1:** Headlines 3–4, with **LED 2** lighting **green**.  
    - **Page 2:** Headlines 5–6, with **LED 2** lighting **orange**.
  - **LED Indicator:** In news view, only the **second‑from‑right LED (LED 2)** is lit based on the current page.

- **Wi‑Fi & NTP**  
  - Automatically connects to Wi‑Fi using credentials from `secret.py`.  
  - Synchronizes time via an NTP server (configured for CST, UTC‑6 by default).

- **Periodic Updates**  
  - Weather updates every **5 minutes**.  
  - Forecast updates every **30 minutes**.  
  - News headlines refresh every **15 minutes**.

- **User Interaction**  
  - **Button 0 (left‑most):** Toggles between weather and forecast views.  
  - **Button 1 (second from left):** Switches to news view and cycles through news pages.  
  - **Button 2 (third from left):** Reserved for future features.

---

## 🛠️ Requirements

### Hardware
- **Adafruit MagTag** with a 2.9" e‑ink display and **4 NeoPixels** at the top.
- A stable Wi‑Fi access point.

### Software / Libraries
- **CircuitPython** installed on your MagTag.
- Required libraries in the `lib` folder on your CIRCUITPY drive:
  - `adafruit_requests`
  - `adafruit_ntp`
  - `adafruit_magtag`
- **Font Files:**  
  Place `Arial-Bold-12.bdf` and `Arial-12.bdf` into a `/fonts` folder on your CIRCUITPY drive.

### API
- A valid **OpenWeatherMap API key** (the free tier is sufficient).

### `secret.py` File
Create a file named `secret.py` in the root of your CIRCUITPY drive containing:
```python
WIFI_SSID = "your_wifi_ssid"
WIFI_PASSWORD = "your_wifi_password"
OPENWEATHERMAP_API_KEY = "your_api_key_here"

 Installation & Setup
Clone or Download the Project:
Download the repository or clone it to your local machine.

Create secret.py:
In the root of your CIRCUITPY drive, create a file named secret.py and add your Wi‑Fi credentials and API key.

Install Required Libraries:
Download the latest Adafruit CircuitPython Bundle and copy the required libraries into the lib folder on your CIRCUITPY drive.

Add Font Files:
Place Arial-Bold-12.bdf and Arial-12.bdf in a /fonts folder on your CIRCUITPY drive.

Upload the Code:
Copy the provided code.py file into the root of your CIRCUITPY drive.

Power or Reset the MagTag:
The device will auto-connect to Wi‑Fi, sync time, and fetch weather, forecast, and news data.

📖 Usage
Weather/Forecast View:

Weather View: Displays current weather details and date/time.
LED Indicator: The right‑most LED (LED 3) lights white.
Forecast View: Displays a simple 5‑day forecast.
LED Indicator: The right‑most LED (LED 3) lights blue.
Toggle Views: Press Button 0 (left‑most) to switch between weather and forecast views.
News View:

Press Button 1 (second from left) to enter news view.
Subsequent presses of Button 1 cycle through news pages:
Page 0: Headlines 1–2, with LED 2 (second‑from‑right) lighting white.
Page 1: Headlines 3–4, with LED 2 lighting green.
Page 2: Headlines 5–6, with LED 2 lighting orange.
Button 2: Currently has no functionality.
Automatic Updates:

Time updates every 60 seconds.
Weather updates every 5 minutes.
Forecast updates every 30 minutes.
News updates every 15 minutes.
