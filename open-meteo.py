# --------------------------Weather Forecast API Example using Open-Meteo---------------------

import requests

CITY = "Dehradun"

# 1. Get coordinates from Open-Meteo Geocoding API
geo_url = "https://geocoding-api.open-meteo.com/v1/search"
geo_params = {
    "name": CITY,
    "count": 1,
    "language": "en",
    "format": "json"
}
geo_resp = requests.get(geo_url, params=geo_params)
geo_data = geo_resp.json()

if "results" not in geo_data:
    print("City not found!")
    exit()

lat = geo_data["results"][0]["latitude"]
lon = geo_data["results"][0]["longitude"]
print(f"Coordinates for {CITY}: {lat}, {lon}")

# 2. Get full forecast from Open-Meteo Weather API
weather_url = "https://api.open-meteo.com/v1/forecast"
weather_params = {
    "latitude": lat,
    "longitude": lon,
    "daily": [
        "temperature_2m_max", "temperature_2m_min",
        "apparent_temperature_max", "apparent_temperature_min",
        "precipitation_sum", "rain_sum", "snowfall_sum",
        "sunrise", "sunset",
        "windspeed_10m_max", "windgusts_10m_max",
        "winddirection_10m_dominant",
        "shortwave_radiation_sum", "et0_fao_evapotranspiration"
    ],
    "hourly": [
        "temperature_2m", "relative_humidity_2m", "dewpoint_2m",
        "apparent_temperature", "precipitation", "rain", "snowfall",
        "cloudcover", "cloudcover_low", "cloudcover_mid", "cloudcover_high",
        "windspeed_10m", "windgusts_10m", "winddirection_10m",
        "surface_pressure", "visibility",
        "shortwave_radiation", "direct_radiation", "diffuse_radiation"
    ],
    "forecast_days": 14,
    "timezone": "auto"
}

weather_resp = requests.get(weather_url, params=weather_params)
weather_data = weather_resp.json()

# 3. Print daily data
print("\n--- 14-Day Daily Forecast ---")
daily = weather_data.get("daily", {})
for i in range(len(daily["time"])):
    date = daily["time"][i]
    tmax = daily["temperature_2m_max"][i]
    tmin = daily["temperature_2m_min"][i]
    precip = daily["precipitation_sum"][i]
    rain = daily["rain_sum"][i]
    snow = daily["snowfall_sum"][i]
    wind = daily["windspeed_10m_max"][i]
    print(f"{date}: Min {tmin}°C, Max {tmax}°C, Precip: {precip} mm, Rain: {rain} mm, Snow: {snow} cm, Wind Max: {wind} km/h")

# 4. Print first 24 hours of hourly data
print("\n--- Next 24 Hours (Hourly) ---")
hourly = weather_data.get("hourly", {})
for i in range(24):
    time = hourly["time"][i]
    temp = hourly["temperature_2m"][i]
    humidity = hourly["relative_humidity_2m"][i]
    clouds = hourly["cloudcover"][i]
    precip = hourly["precipitation"][i]
    wind = hourly["windspeed_10m"][i]
    pressure = hourly["surface_pressure"][i]
    print(f"{time} | Temp: {temp}°C, Humidity: {humidity}%, Clouds: {clouds}%, Precip: {precip} mm, Wind: {wind} km/h, Pressure: {pressure} hPa")

# --------------------------Open-Meteo Historical Weather Data Example---------------------------

# import requests

# # City to fetch (we'll get its lat/lon first)
# city = "Dehradun"

# # Step 1: Geocode city to get latitude/longitude
# geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city}&count=1"
# geo_resp = requests.get(geo_url)
# geo_data = geo_resp.json()

# if "results" not in geo_data:
#     print(f"City '{city}' not found.")
#     exit()

# lat = geo_data["results"][0]["latitude"]
# lon = geo_data["results"][0]["longitude"]
# print(f"Coordinates for {city}: {lat}, {lon}")

# # Step 2: Fetch oldest historical weather data
# # ERA5 dataset covers from 1940 to near-present
# historical_url = (
#     "https://archive-api.open-meteo.com/v1/archive"
#     f"?latitude={lat}&longitude={lon}"
#     "&start_date=2025-08-08&end_date=2025-08-10"
#     "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max"
#     "&timezone=auto"
# )

# historical_resp = requests.get(historical_url)
# historical_data = historical_resp.json()

# # Step 3: Display sample results
# print("\n--- Historical Weather Data (1940) ---")
# for date, tmax, tmin, rain, wind in zip(
#     historical_data["daily"]["time"],
#     historical_data["daily"]["temperature_2m_max"],
#     historical_data["daily"]["temperature_2m_min"],
#     historical_data["daily"]["precipitation_sum"],
#     historical_data["daily"]["windspeed_10m_max"],
# ):
#     print(f"{date}: Max {tmax}°C, Min {tmin}°C, Rain {rain} mm, Max Wind {wind} km/h")


# --------------------------Open-Meteo Elevation API Example---------------------------------

# import requests

# # Example coordinates (Dehradun)
# latitude = 30.3256
# longitude = 78.0437

# elevation_url = "https://api.open-meteo.com/v1/elevation"
# params = {
#     "latitude": latitude,
#     "longitude": longitude
# }

# resp = requests.get(elevation_url, params=params)
# data = resp.json()

# if "elevation" in data:
#     print(f"Elevation at ({latitude}, {longitude}): {data['elevation']} meters")
# else:
#     print("Elevation data not found.")

# ...existing code...

