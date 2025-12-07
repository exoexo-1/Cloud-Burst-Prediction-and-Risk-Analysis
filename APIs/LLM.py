# APIs/LLM.py
import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
import joblib
import numpy as np
from datetime import date, timedelta
import requests
from openai import OpenAI


# Load environment variables
load_dotenv()

class RAGService:
    def __init__(self, db_path="vector_db"):
        self.embeddings = OpenAIEmbeddings()
        try:
            self.vectorstore = Chroma(
                persist_directory=db_path,
                embedding_function=self.embeddings
            )
            print(f"Connected to RAG database with {self.vectorstore._collection.count()} documents")
        except Exception as e:
            print(f"Warning: Could not connect to RAG database: {e}")
            self.vectorstore = None

    def get_context(self, district_name: str, k: int = 3):
        """
        Fetch comprehensive context for a district using fixed queries
        """
        if not self.vectorstore:
            return "RAG database not available"

        try:
            queries = [
                f"{district_name} risk factors vulnerability hazards",
                f"{district_name} historical events disasters",
                f"{district_name} geography topography elevation",
                f"{district_name} flood cloudburst patterns"
            ]

            all_context = f"CONTEXT FOR {district_name.upper()}:\n\n"

            for i, query in enumerate(queries, 1):
                docs = self.vectorstore.similarity_search(query, k=k)
                if docs:
                    all_context += f"Section {i} ({query}):\n"
                    for doc in docs:
                        doc_type = doc.metadata.get('doc_type', 'Unknown')
                        preview = doc.page_content[:400]  # limit preview
                        all_context += f"- From {doc_type}: {preview}...\n"
                    all_context += "\n"

            return all_context if len(all_context) > 50 else f"No relevant information found for {district_name}"

        except Exception as e:
            return f"Error retrieving context: {str(e)}"
        
# rag = RAGService(db_path="vector_db")
# district = "Chamoli"
# result = rag.get_context(district, k=2)

# print(result)


class RiskAnalysisLLM:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = "gpt-4o-mini"

    def create_system_prompt(self):
        return """
        🌧️ Flood and Cloudburst Risk Assessment Report (Hydroprognosis AI)

            ### 1. Flood Risk Level
            - Output a single risk category: Low / Moderate / High / Severe.
            - Decide based on rainfall, soil moisture, slope, river flow, and other relevant factors.

            ### 2. Cloudburst Probability
            - Output: Yes / No. with a percentage likelihood (0-100%).


            ### 3. Key Risk Factors
            - List the most important 3–5 factors that influence the risk.
            - Format: bullet points.
            - Each factor should have a brief explanation (1–2 lines).
            - You may choose any relevant factors, for example:
            - Rainfall Intensity
            - Soil Moisture & Drainage
            - Terrain Slope & Elevation
            - River Proximity & Flow
            - Deforestation / Cloud Density / Other local risks
            - Note: You are free to pick which factors matter most for the current location; don’t limit yourself to a fixed list.

            ### 4. Historical & Geographical Context
            - Summarize past cloudburst/flood incidents in this region (if known).
            - Describe local terrain, elevation, drainage patterns, valleys, slopes, and ecological features that affect vulnerability.
            - Keep it short but informative.

            ### 5. Recommendations
            Split into two groups:

            For Residents:
            - Provide 3–4 clear, actionable safety steps (evacuation, shelter, monitoring, precautions).

            For Authorities:
            - Provide 3–4 preparedness and response steps (relief planning, resource allocation, public alerts, monitoring).

            ### 6. Future Prediction Report (24–72 hrs)
            - Describe expected weather conditions (rainfall, temperature, humidity).
            - Predict if risk levels may rise, stay same, or reduce.
            - Highlight key indicators to monitor for escalating risk.

            ⚠️ Guidelines for AI:
            - Always follow the section order and headings.
            - Keep writing clear, concise, and structured.
            - Use your knowledge and reasoning — don’t just repeat fixed phrases.
            - Focus on what is most relevant for this location and time.
        """
    


    def predict_cloudburst(lat: float, lon: float):
        import requests
        import numpy as np
        import joblib
        from datetime import date, timedelta

        # -----------------------------
        # Load models INSIDE function
        # -----------------------------
        scaler = joblib.load("scaler.pkl")
        regressor = joblib.load("cloudburst_regressor.pkl")

        # -----------------------------
        # Mappings
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
        # Get previous-week averages
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
                "hourly": (
                    "temperature_2m,relativehumidity_2m,pressure_msl,cloudcover,"
                    "windspeed_10m,windgusts_10m,precipitation_probability"
                ),
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
                    values = [x for x in data.get(group, {}).get(key, []) if x is not None]
                    if values:
                        defaults[avg_key] = float(np.mean(values))
            except:
                pass

            return defaults

        # -----------------------------
        # Fetch current weather
        # -----------------------------
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "current_weather": True,
            "timezone": "auto",
            "forecast_days": 1,
            "hourly": (
                "temperature_2m,relativehumidity_2m,pressure_msl,precipitation,rain,"
                "cloudcover,windspeed_10m,windgusts_10m,winddirection_10m,is_day,"
                "weathercode,precipitation_probability"
            ),
            "daily": (
                "temperature_2m_max,temperature_2m_min,precipitation_sum,rain_sum,"
                "precipitation_probability_max,weathercode,windspeed_10m_max,"
                "windgusts_10m_max,winddirection_10m_dominant"
            )
        }

        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()

        hourly = data["hourly"]
        daily = data["daily"]
        current = data["current_weather"]

        hist = get_previous_week_data(lat, lon)

        curr_time = current["time"]
        hr_times = hourly["time"]
        idx = hr_times.index(curr_time) if curr_time in hr_times else 0

        def get(src, key, default):
            vals = src.get(key)
            return vals[idx] if vals and idx < len(vals) else default

        # -----------------------------
        # Build 14-feature vector
        # -----------------------------
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

        # -----------------------------
        # Scale + Predict
        # -----------------------------
        scaled = scaler.transform(features)
        raw_pred = regressor.predict(scaled)[0]
        probability = int(max(0, min(100, round(raw_pred))))

        return {"probability": probability}
    

    def generate_risk_analysis(self, fvi_data: dict, rag_context: str):

        lat = fvi_data['location']['latitude']
        lon = fvi_data['location']['longitude']
        prediction = self.predict_cloudburst(lat, lon)
        """
        Generate comprehensive risk analysis report using:
        1. FVI calculated data (dict)
        2. RAG extracted context (str)
        """

        # Extract place name if available
        if 'district' in fvi_data.get('inputs', {}).get('socioeconomic', {}):
            place_name = fvi_data['inputs']['socioeconomic']['district']
        else:
            lat = fvi_data['location']['latitude']
            lon = fvi_data['location']['longitude']
            place_name = f"Location at {lat:.4f}, {lon:.4f}"
        
        

        # Construct user prompt
        user_prompt = f"""
        Here are the observed conditions and FVI analysis:

        LOCATION DETAILS:
        - Place: {place_name}
        - Coordinates: {fvi_data['location']['latitude']:.4f}, {fvi_data['location']['longitude']:.4f}
        - FVI Score: {fvi_data['fvi_score']}/100
        - Risk Level: {fvi_data['risk_level']}

        WEATHER DATA:
        - Current Rainfall: {fvi_data['inputs']['weather']['current_rainfall']} mm
        - Weekly Rainfall: {fvi_data['inputs']['weather']['weekly_rainfall']} mm
        - Soil Moisture: {fvi_data['inputs']['weather']['soil_moisture'] * 100}%
        - Humidity: {fvi_data['inputs']['weather']['humidity']}%
        - Precipitation Probability: {fvi_data['inputs']['weather']['precipitation_probability']}%

        TERRAIN DATA:
        - Elevation: {fvi_data['inputs']['terrain']['elevation']} m
        - Slope: {fvi_data['inputs']['terrain']['slope']}°

        HYDROLOGY:
        - Distance to Water: {fvi_data['inputs']['hydrology']['distance_to_water']} m
        - Drainage Density: {fvi_data['inputs']['hydrology']['drainage_density']}

        SOCIOECONOMIC:
        - Population Density: {fvi_data['inputs']['socioeconomic']['population_density']} people/km²
        - Urbanization Level: {fvi_data['inputs']['socioeconomic']['urbanization_level']}%
        - Imperviousness: {fvi_data['inputs']['socioeconomic']['imperviousness']}%

        KEY FACTORS IDENTIFIED:
        {', '.join(fvi_data['key_factors'])}

        KNOWLEDGE BASE CONTEXT:
        {rag_context}


        ML Model ouput in probablity percentage of cloud burst:
        {prediction}


        Question: Provide a comprehensive flood and cloudburst risk assessment report for this location.
        """

        messages = [
            {"role": "system", "content": self.create_system_prompt()},
            {"role": "user", "content": user_prompt}
        ]

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )

            return {
                "analysis": response.choices[0].message.content,
                "rag_context": rag_context[:500] + "..." if len(rag_context) > 500 else rag_context
            }

        except Exception as e:
            return {
                "analysis": f"Error generating risk analysis: {str(e)}",
                "rag_context": rag_context
            }
        

# fvi_data = {
#     "location": {"latitude": 29.9457, "longitude": 78.1642},
#     "fvi_score": 62.5,
#     "risk_level": "Moderate",
#     "inputs": {
#         "weather": {
#             "current_rainfall": 6.2,
#             "weekly_rainfall": 22.3,
#             "soil_moisture": 0.25,
#             "humidity": 78,
#             "precipitation_probability": 65
#         },
#         "terrain": {"elevation": 1800, "slope": 25},
#         "hydrology": {"distance_to_water": 200, "drainage_density": 0.45},
#         "socioeconomic": {
#             "population_density": 320,
#             "urbanization_level": 45,
#             "imperviousness": 30,
#             "district": "Chamoli"
#         }
#     },
#     "key_factors": ["High slope", "Moderate rainfall", "Medium population density"]
# }

# # # Get RAG context
# # rag_service = RAGService()
# # rag_context = rag_service.get_context("Chamoli")

# # # Generate analysis
# # llm = RiskAnalysisLLM()
# # result = llm.generate_risk_analysis(fvi_data, rag_context)
# # print(result["analysis"])