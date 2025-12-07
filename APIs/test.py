# import requests

# url = "http://127.0.0.1:8000/analysis"  # use local if testing locally

# payload = {
#     "place_name": "Chamoli",
#     "fvi_data": {
#         "location": {"latitude": 29.9457, "longitude": 78.1642},
#         "fvi_score": 62.5,
#         "risk_level": "Moderate",
#         "inputs": {
#             "weather": {"current_rainfall": 6.2, "weekly_rainfall": 22.3, "soil_moisture": 0.25, "humidity": 78, "precipitation_probability": 65},
#             "terrain": {"elevation": 1800, "slope": 25},
#             "hydrology": {"distance_to_water": 200, "drainage_density": 0.45},
#             "socioeconomic": {"population_density": 320, "urbanization_level": 45, "imperviousness": 30, "district": "Chamoli"}
#         },
#         "key_factors": ["High slope", "Moderate rainfall", "Medium population density"]
#     }
# }

# res = requests.post(url, json=payload)
# print(res.status_code)
# print(res.json())
