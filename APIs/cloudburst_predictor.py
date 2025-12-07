import requests
import numpy as np
import joblib
from datetime import date, timedelta

# -----------------------------
# Load the saved ML models
# -----------------------------
scaler = joblib.load("scaler.pkl")
regressor = joblib.load("cloudburst_regressor.pkl")

# -----------------------------
# Wind and weather mappings (same as your app)
# -----------------------------
wind_direction_mapping = {"E": 0, "N": 1, "NE": 2, "NW": 3, "S": 4, "SE": 5, "SW": 6, "W": 7}
is_day_mapping = {1: 0, 0: 1}

def map_weather_description_to_encoding(code):
    weather_encoding_map = {
        0: 0, 1: 0, 2: 5, 3: 4,
        45: 2, 48: 2,
        51: 1, 53: 1, 55: 1, 56: 1, 57: 1,
        61: 6, 63: 6, 65: 3,
        66: 6, 67: 3,
        71: 6, 73: 6, 75: 6, 77: 6,
        80: 6, 81: 6, 82: 3,
        85: 6, 86: 6,
        95: 7, 96: 7, 99: 7
    }
    try:
        return weather_encoding_map.get(int(code), 0)
    except:
        return 0

def degrees_to_cardinal(deg):
    dirs = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    try:
        deg = float(deg)
        return dirs[int((deg + 22.5) / 45) % 8]
    except:
        return "N"

# -----------------------------
# Historical averaging (same as app.py)
# -----------------------------
def get_previous_week_data(lat, lon):
    today = date.today()
    start_date = today - timedelta(days=8)
    end_date = today - timedelta(days=1)

    url = "https://api.open-meteo.com/v1/archive"
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": "precipitation_sum,rain_sum",
        "hourly": ("temperature_2m,relativehumidity_2m,pressure_msl,cloudcover,"
                   "windspeed_10m,windgusts_10m,precipitation_probability"),
        "timezone": "auto",
        "start_date": start_date.strftime("%Y-%m-%d"),
        "end_date": end_date.strftime("%Y-%m-%d")
    }

    defaults = {
        "avg_precipitation_sum": 0.1,
        "avg_rain_sum": 0.1,
        "avg_relativehumidity_2m": 65.0,
        "avg_pressure_msl": 1012.0,
        "avg_cloudcover": 40.0,
        "avg_temp": 22.0,
        "avg_wind_speed": 8.0,
        "avg_wind_gust": 12.0,
        "avg_precip_prob": 15.0
    }

    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()

        mapping = [
            (("daily", "precipitation_sum"), "avg_precipitation_sum"),
            (("daily", "rain_sum"), "avg_rain_sum"),
            (("hourly", "temperature_2m"), "avg_temp"),
            (("hourly", "relativehumidity_2m"), "avg_relativehumidity_2m"),
            (("hourly", "pressure_msl"), "avg_pressure_msl"),
            (("hourly", "cloudcover"), "avg_cloudcover"),
            (("hourly", "windspeed_10m"), "avg_wind_speed"),
            (("hourly", "windgusts_10m"), "avg_wind_gust"),
            (("hourly", "precipitation_probability"), "avg_precip_prob"),
        ]

        for (group, key), avg_key in mapping:
            values = [
                x for x in data.get(group, {}).get(key, [])
                if x is not None
            ]
            if values:
                defaults[avg_key] = float(np.mean(values))

    except:
        pass

    return defaults

# -----------------------------
# Main Prediction Function
# -----------------------------
def predict_cloudburst(lat: float, lon: float):
    """
    Standalone function that returns cloudburst probability at a location.
    Uses EXACT SAME feature calculation as the full Flask system.
    """

    # 1️⃣ Fetch current weather
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "timezone": "auto",
        "forecast_days": 1,
        "hourly": ("temperature_2m,relativehumidity_2m,pressure_msl,precipitation,rain,"
                   "cloudcover,windspeed_10m,windgusts_10m,winddirection_10m,is_day,"
                   "weathercode,precipitation_probability"),
        "daily": ("temperature_2m_max,temperature_2m_min,precipitation_sum,rain_sum,"
                  "precipitation_probability_max,weathercode,windspeed_10m_max,"
                  "windgusts_10m_max,winddirection_10m_dominant")
    }

    r = requests.get(url, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()

    hourly = data["hourly"]
    daily = data["daily"]
    current = data["current_weather"]

    hist = get_previous_week_data(lat, lon)

    # Find index of current hour
    curr_time = current["time"]
    hr_times = hourly["time"]
    idx = hr_times.index(curr_time) if curr_time in hr_times else 0

    # Helper getter
    def get(src, key, default):
        vals = src.get(key)
        return vals[idx] if vals and idx < len(vals) else default

    # 2️⃣ Build the 14 model inputs (same order)
    min_temp = daily["temperature_2m_min"][0]
    max_temp = daily["temperature_2m_max"][0]
    humidity = get(hourly, "relativehumidity_2m", hist["avg_relativehumidity_2m"])
    pressure = get(hourly, "pressure_msl", hist["avg_pressure_msl"])
    precipitation = daily["precipitation_sum"][0]
    rain = daily["rain_sum"][0]
    precip_prob = daily["precipitation_probability_max"][0]
    cloudcover = get(hourly, "cloudcover", hist["avg_cloudcover"])
    wind_speed = daily["windspeed_10m_max"][0]
    wind_gust = daily["windgusts_10m_max"][0]

    # Wind direction encoding
    deg = daily["winddirection_10m_dominant"][0]
    card = degrees_to_cardinal(deg)
    wind_dir_encoded = wind_direction_mapping.get(card, 1)

    is_day_api = get(hourly, "is_day", 1)
    is_day_encoded = is_day_mapping.get(is_day_api, 0)

    temp_2m = get(hourly, "temperature_2m", hist["avg_temp"])

    weathercode = daily["weathercode"][0]
    weather_enc = map_weather_description_to_encoding(weathercode)

    features = np.array([[
        min_temp, max_temp, humidity, pressure, precipitation, rain,
        precip_prob, cloudcover, wind_speed, wind_gust,
        wind_dir_encoded, is_day_encoded, temp_2m, weather_enc
    ]])

    # 3️⃣ Scale + predict
    scaled = scaler.transform(features)
    raw_pred = regressor.predict(scaled)[0]

    probability = int(max(0, min(100, round(raw_pred))))

    return {"probability": probability}

if __name__ == "__main__":
    res = predict_cloudburst(28.61, 77.20)
    print(res)