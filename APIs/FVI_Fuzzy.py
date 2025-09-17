#APIs/FVI_Fuzzy.py
"""

Enhanced Flood Vulnerability Index (FVI) analyzer for Uttarakhand (and arbitrary lat/lon).
Fetches data from Open-Meteo, Open-Elevation, and OSM (via osmnx) and computes FVI using fuzzy logic.
Fixed issues with fuzzy system computation.
"""

import time
import logging
from typing import Tuple, Dict, Any, Optional
import requests
import numpy as np
import skfuzzy as fuzz
from skfuzzy import control as ctrl

# Spatial libs
import osmnx as ox
import geopandas as gpd
from shapely.geometry import Point

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("FVI")

# ---- District dictionary for Uttarakhand (expandable) ----
UTTARAKHAND_DISTRICTS = {
    "dehradun": {"lat": 30.3165, "lon": 78.0322, "pop_density": 550, "urbanization": 65, "dev_pressure": 80},
    "haridwar": {"lat": 29.9457, "lon": 78.1642, "pop_density": 820, "urbanization": 50, "dev_pressure": 70},
    "nainital": {"lat": 29.3919, "lon": 79.4542, "pop_density": 225, "urbanization": 35, "dev_pressure": 60},
    "rishikesh": {"lat": 30.0869, "lon": 78.2676, "pop_density": 400, "urbanization": 45, "dev_pressure": 55},
    "almora": {"lat": 29.5971, "lon": 79.6593, "pop_density": 140, "urbanization": 20, "dev_pressure": 30},
    "uttarkashi": {"lat": 31.0916, "lon": 78.4547, "pop_density": 85, "urbanization": 12, "dev_pressure": 20},
    "tehri": {"lat": 30.3271, "lon": 78.0021, "pop_density": 160, "urbanization": 22, "dev_pressure": 35}
}

def district_to_coords(name: str) -> Optional[Tuple[float, float, Dict[str, float]]]:
    key = name.strip().lower()
    if key in UTTARAKHAND_DISTRICTS:
        d = UTTARAKHAND_DISTRICTS[key]
        return d["lat"], d["lon"], {"pop_density": d["pop_density"], "urbanization": d["urbanization"], "dev_pressure": d["dev_pressure"]}
    return None


class FloodVulnerabilityAnalyzer:
    def __init__(self, cache_enabled: bool = True):
        self.cache = {} if cache_enabled else None
        self.fuzzy_system = None

    def get_weather_data(self, lat: float, lon: float) -> Dict[str, float]:
        """Fetch hourly/daily weather from Open-Meteo. Returns aggregated metrics used by FVI."""
        key = f"weather_{lat:.5f}_{lon:.5f}"
        if self.cache is not None and key in self.cache:
            return self.cache[key]

        try:
            url = (
                "https://api.open-meteo.com/v1/forecast?"
                f"latitude={lat}&longitude={lon}"
                "&hourly=precipitation,relative_humidity_2m,temperature_2m"
                "&daily=precipitation_sum,precipitation_probability_max"
                "&forecast_days=3&timezone=auto"
            )

            r = requests.get(url, timeout=12)
            r.raise_for_status()
            j = r.json()

            hourly = j.get("hourly", {})
            daily = j.get("daily", {})

            precip_hourly = hourly.get("precipitation", [])
            humidity_hourly = hourly.get("relative_humidity_2m", [])
            temp_hourly = hourly.get("temperature_2m", [])

            current_rain = float(sum(precip_hourly[:24])) if precip_hourly else 0.0
            weekly_rain = float(sum(daily.get("precipitation_sum", [])[:7])) if daily.get("precipitation_sum") else current_rain
            soil_moisture = 0.25  # Default since Open-Meteo doesn't always provide this
            humidity = float(np.mean(humidity_hourly[:24])) if humidity_hourly else 70.0
            temperature = float(np.mean(temp_hourly[:24])) if temp_hourly else 20.0
            precip_prob = float(np.mean(daily.get("precipitation_probability_max", [0.0])[:3]))

            out = {
                "current_rainfall": current_rain,
                "weekly_rainfall": weekly_rain,
                "soil_moisture": soil_moisture,
                "humidity": humidity,
                "temperature": temperature,
                "precipitation_probability": precip_prob
            }
            if self.cache is not None:
                self.cache[key] = out
            return out

        except Exception as e:
            logger.warning(f"Open-Meteo fetch failed ({e}), using defaults")
            return {
                "current_rainfall": 10.0,
                "weekly_rainfall": 50.0,
                "soil_moisture": 0.3,
                "humidity": 70.0,
                "temperature": 20.0,
                "precipitation_probability": 20.0
            }

    def get_elevation(self, lat: float, lon: float) -> float:
        """Fetch elevation using open-elevation.public API. Returns meters."""
        key = f"elev_{lat:.5f}_{lon:.5f}"
        if self.cache is not None and key in self.cache:
            return self.cache[key]

        try:
            url = f"https://api.open-elevation.com/api/v1/lookup?locations={lat},{lon}"
            r = requests.get(url, timeout=8)
            r.raise_for_status()
            j = r.json()
            elev = float(j["results"][0]["elevation"])
            if self.cache is not None:
                self.cache[key] = elev
            return elev
        except Exception as e:
            logger.warning(f"Open-elevation failed ({e}) - defaulting elevation")
            return 500.0

    def _sample_nearby_elevations(self, lat: float, lon: float, offsets=0.0009):
        """Return small list of elevations around point for slope estimate"""
        samples = []
        try:
            pts = [(lat + offsets, lon), (lat - offsets, lon), (lat, lon + offsets), (lat, lon - offsets)]
            for (la, lo) in pts:
                try:
                    elev = self.get_elevation(la, lo)
                    samples.append(elev)
                    time.sleep(0.05)
                except Exception:
                    continue
        except Exception:
            pass
        return samples

    def estimate_slope(self, lat: float, lon: float) -> float:
        """Estimate slope (degrees) using sampled elevation deltas."""
        samples = self._sample_nearby_elevations(lat, lon)
        try:
            if len(samples) >= 2:
                elev_diff = max(samples) - min(samples)
                slope_rad = np.arctan(elev_diff / 200.0)
                slope_deg = float(np.degrees(slope_rad))
                return max(0.0, min(slope_deg, 45.0))
            else:
                return 8.0
        except Exception:
            return 8.0

    def get_hydrology(self, lat: float, lon: float, search_dist_m: int = 10000) -> Dict[str, float]:
        """Use osmnx to find nearby water features and compute minimum distance (meters)."""
        key = f"hydro_{lat:.5f}_{lon:.5f}"
        if self.cache is not None and key in self.cache:
            return self.cache[key]

        try:
            tags = {"waterway": True, "natural": ["water", "wetland"], "water": True}
            geom = ox.features_from_point((lat, lon), tags=tags, dist=search_dist_m)

            user_point = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326").to_crs(epsg=3857)[0]

            min_dist_m = float(search_dist_m)
            if not geom.empty:
                geom_gdf = gpd.GeoDataFrame(geom, geometry=geom.geometry, crs="EPSG:4326").to_crs(epsg=3857)
                distances = geom_gdf.geometry.distance(user_point)
                min_dist_m = float(max(0.0, distances.min()))
            
            drainage_density = 8.0 if lat > 30.0 else 6.0
            out = {"distance_to_water": min_dist_m, "drainage_density": drainage_density}
            if self.cache is not None:
                self.cache[key] = out
            return out
        except Exception as e:
            logger.warning(f"OSM hydrology fetch failed ({e}) - returning defaults")
            return {"distance_to_water": 2000.0, "drainage_density": 7.0}

    def get_socioeconomic(self, lat: float, lon: float, district_info: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """Return population density, urbanization, imperviousness estimate"""
        if district_info:
            pop_density = district_info.get("pop_density", 180)
            urb = district_info.get("urbanization", 25)
            dev_pressure = district_info.get("dev_pressure", 40)
        else:
            pop_density = 180
            urb = 25
            dev_pressure = 40

        # Fixed imperviousness calculation - was too high before
        imperviousness = float(min(95.0, urb * 0.8 + dev_pressure * 0.3))
        return {
            "population_density": pop_density, 
            "urbanization_level": urb, 
            "imperviousness": imperviousness, 
            "development_pressure": dev_pressure
        }

    def build_fuzzy_system(self):
        """Define fuzzy variables, membership functions and rule base - FIXED VERSION"""
        # Inputs
        rainfall = ctrl.Antecedent(np.arange(0, 201, 1), "rainfall")          # Reduced range for better sensitivity
        slope = ctrl.Antecedent(np.arange(0, 46, 1), "slope")                
        imperv = ctrl.Antecedent(np.arange(0, 101, 1), "imperviousness")     
        dist_water = ctrl.Antecedent(np.arange(0, 10001, 1), "distance_water")# Reduced range
        soil = ctrl.Antecedent(np.arange(0, 1.01, 0.01), "soil_moisture")
        elevation = ctrl.Antecedent(np.arange(0, 3001, 1), "elevation")      # Reduced range for Uttarakhand

        # Output
        fvi = ctrl.Consequent(np.arange(0, 101, 1), "fvi")

        # FIXED: More realistic membership functions for the actual data ranges
        rainfall["very_low"] = fuzz.trapmf(rainfall.universe, [0, 0, 2, 8])
        rainfall["low"] = fuzz.trimf(rainfall.universe, [5, 15, 30])
        rainfall["moderate"] = fuzz.trimf(rainfall.universe, [25, 50, 80])
        rainfall["high"] = fuzz.trimf(rainfall.universe, [70, 100, 150])
        rainfall["extreme"] = fuzz.trapmf(rainfall.universe, [120, 150, 200, 200])

        slope["flat"] = fuzz.trapmf(slope.universe, [0, 0, 3, 8])
        slope["gentle"] = fuzz.trimf(slope.universe, [5, 12, 20])
        slope["moderate"] = fuzz.trimf(slope.universe, [15, 25, 35])
        slope["steep"] = fuzz.trapmf(slope.universe, [30, 35, 45, 45])

        imperv["low"] = fuzz.trapmf(imperv.universe, [0, 0, 20, 40])
        imperv["medium"] = fuzz.trimf(imperv.universe, [30, 50, 70])
        imperv["high"] = fuzz.trapmf(imperv.universe, [60, 80, 100, 100])

        dist_water["very_near"] = fuzz.trapmf(dist_water.universe, [0, 0, 100, 500])
        dist_water["near"] = fuzz.trimf(dist_water.universe, [300, 1000, 2000])
        dist_water["moderate"] = fuzz.trimf(dist_water.universe, [1500, 3000, 5000])
        dist_water["far"] = fuzz.trapmf(dist_water.universe, [4000, 6000, 10000, 10000])

        soil["dry"] = fuzz.trapmf(soil.universe, [0, 0, 0.2, 0.4])
        soil["moderate"] = fuzz.trimf(soil.universe, [0.3, 0.5, 0.7])
        soil["saturated"] = fuzz.trapmf(soil.universe, [0.6, 0.8, 1.0, 1.0])

        elevation["low"] = fuzz.trapmf(elevation.universe, [0, 0, 300, 600])
        elevation["mid"] = fuzz.trimf(elevation.universe, [400, 1000, 1800])
        elevation["high"] = fuzz.trapmf(elevation.universe, [1500, 2000, 3000, 3000])

        # Output membership functions
        fvi["very_low"] = fuzz.trapmf(fvi.universe, [0, 0, 15, 25])
        fvi["low"] = fuzz.trimf(fvi.universe, [20, 30, 45])
        fvi["moderate"] = fuzz.trimf(fvi.universe, [40, 50, 65])
        fvi["high"] = fuzz.trimf(fvi.universe, [60, 75, 85])
        fvi["very_high"] = fuzz.trapmf(fvi.universe, [80, 90, 100, 100])

        # SIMPLIFIED and MORE COMPREHENSIVE rule base
        rules = []

        # High imperviousness rules (urban flooding)
        rules.append(ctrl.Rule(imperv["high"] & dist_water["very_near"], fvi["very_high"]))
        rules.append(ctrl.Rule(imperv["high"] & rainfall["high"], fvi["very_high"]))
        rules.append(ctrl.Rule(imperv["high"] & rainfall["moderate"], fvi["high"]))
        rules.append(ctrl.Rule(imperv["high"], fvi["moderate"]))  # Base rule for high imperviousness

        # Water proximity rules
        rules.append(ctrl.Rule(dist_water["very_near"] & elevation["low"], fvi["high"]))
        rules.append(ctrl.Rule(dist_water["very_near"] & rainfall["moderate"], fvi["high"]))
        rules.append(ctrl.Rule(dist_water["very_near"], fvi["moderate"]))  # Base rule for water proximity

        # Rainfall rules
        rules.append(ctrl.Rule(rainfall["extreme"], fvi["very_high"]))
        rules.append(ctrl.Rule(rainfall["high"] & slope["flat"], fvi["high"]))
        rules.append(ctrl.Rule(rainfall["high"], fvi["moderate"]))
        rules.append(ctrl.Rule(rainfall["moderate"] & slope["flat"], fvi["moderate"]))

        # Slope and elevation rules
        rules.append(ctrl.Rule(slope["flat"] & elevation["low"], fvi["moderate"]))
        rules.append(ctrl.Rule(slope["steep"] & rainfall["high"], fvi["high"]))  # Flash flood risk

        # Low risk rules
        rules.append(ctrl.Rule(imperv["low"] & dist_water["far"] & elevation["high"], fvi["very_low"]))
        rules.append(ctrl.Rule(rainfall["very_low"] & dist_water["far"], fvi["low"]))
        rules.append(ctrl.Rule(elevation["high"] & slope["steep"] & rainfall["low"], fvi["low"]))

        # Default/fallback rules
        rules.append(ctrl.Rule(soil["moderate"] & rainfall["low"], fvi["low"]))
        rules.append(ctrl.Rule(elevation["mid"] & imperv["medium"], fvi["moderate"]))

        # Build control system
        self.fuzzy_system = ctrl.ControlSystem(rules)
        logger.info("Fuzzy system built with %d rules", len(rules))

    def calculate_fvi(self, lat: float, lon: float, district_info: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """Compute the FVI for a location with live data fetching and fuzzy logic - FIXED VERSION"""
        # 1) Fetch data
        weather = self.get_weather_data(lat, lon)
        elevation = self.get_elevation(lat, lon)
        slope = self.estimate_slope(lat, lon)
        hydro = self.get_hydrology(lat, lon)
        socio = self.get_socioeconomic(lat, lon, district_info)

        # 2) Build fuzzy system if needed
        if self.fuzzy_system is None:
            self.build_fuzzy_system()

        # 3) Create fresh simulation each time
        sim = ctrl.ControlSystemSimulation(self.fuzzy_system)

        # 4) FIXED: Ensure inputs are within expected ranges and add debugging
        inputs = {
            "rainfall": max(0.0, min(weather["current_rainfall"], 200.0)),
            "slope": max(0.0, min(slope, 45.0)),
            "imperviousness": max(0.0, min(socio["imperviousness"], 100.0)),
            "distance_water": max(0.0, min(hydro["distance_to_water"], 10000.0)),
            "soil_moisture": max(0.0, min(weather["soil_moisture"], 1.0)),
            "elevation": max(0.0, min(elevation, 3000.0))
        }

        logger.info(f"Fuzzy inputs: {inputs}")

        try:
            # Set inputs
            for key, value in inputs.items():
                sim.input[key] = float(value)

            # Compute
            sim.compute()
            fvi_score = float(sim.output["fvi"])
            logger.info(f"Computed FVI score: {fvi_score}")
            
        except Exception as e:
            logger.error("Fuzzy compute failed: %s", e)
            # Fallback calculation based on key factors
            fvi_score = self._fallback_fvi_calculation(inputs)
            logger.info(f"Using fallback FVI score: {fvi_score}")

        # 5) Interpret results
        def interpret(score: float) -> str:
            if score <= 25: return "Very Low"
            if score <= 45: return "Low" 
            if score <= 65: return "Moderate"
            if score <= 85: return "High"
            return "Very High"

        # 6) Enhanced key factor extraction
        factors = []
        if inputs["rainfall"] >= 50:
            factors.append(f"Heavy recent rainfall ({inputs['rainfall']:.1f} mm)")
        elif inputs["rainfall"] >= 20:
            factors.append(f"Moderate rainfall ({inputs['rainfall']:.1f} mm)")

        if inputs["imperviousness"] >= 60:
            factors.append(f"High imperviousness ({inputs['imperviousness']:.1f}%)")
        elif inputs["imperviousness"] >= 40:
            factors.append(f"Moderate imperviousness ({inputs['imperviousness']:.1f}%)")

        if inputs["distance_water"] <= 500:
            factors.append(f"Very close to water body ({inputs['distance_water']:.0f} m)")
        elif inputs["distance_water"] <= 2000:
            factors.append(f"Close to water body ({inputs['distance_water']:.0f} m)")

        if inputs["elevation"] <= 400:
            factors.append(f"Low elevation ({inputs['elevation']:.0f} m)")

        if inputs["slope"] <= 5:
            factors.append(f"Very flat terrain ({inputs['slope']:.1f}° slope)")

        if not factors:
            factors = ["Moderate risk from combined factors"]

        result = {
            "location": {"latitude": lat, "longitude": lon},
            "fvi_score": round(fvi_score, 2),
            "risk_level": interpret(fvi_score),
            "inputs": {
                "weather": weather,
                "terrain": {"elevation": elevation, "slope": slope},
                "hydrology": hydro,
                "socioeconomic": socio,
                "processed_inputs": inputs  # Add this for debugging
            },
            "key_factors": factors,
            "timestamp": time.time()
        }
        return result

    def _fallback_fvi_calculation(self, inputs: Dict[str, float]) -> float:
        """Fallback FVI calculation if fuzzy system fails"""
        score = 30.0  # Base score
        
        # Rainfall contribution (0-25 points)
        if inputs["rainfall"] >= 100:
            score += 25
        elif inputs["rainfall"] >= 50:
            score += 15
        elif inputs["rainfall"] >= 20:
            score += 8
        
        # Imperviousness contribution (0-20 points)
        if inputs["imperviousness"] >= 70:
            score += 20
        elif inputs["imperviousness"] >= 50:
            score += 12
        elif inputs["imperviousness"] >= 30:
            score += 6
        
        # Water proximity contribution (0-15 points)
        if inputs["distance_water"] <= 100:
            score += 15
        elif inputs["distance_water"] <= 500:
            score += 10
        elif inputs["distance_water"] <= 2000:
            score += 5
        
        # Elevation contribution (0-10 points)
        if inputs["elevation"] <= 300:
            score += 10
        elif inputs["elevation"] <= 600:
            score += 5
        
        # Slope contribution (-5 to +5 points)
        if inputs["slope"] <= 3:
            score += 5  # Flat areas more prone to flooding
        elif inputs["slope"] >= 25:
            score -= 5  # Very steep areas less prone to standing water
        
        return max(0.0, min(100.0, score))


# ---- CLI / Example usage ----
if __name__ == "__main__":
    analyzer = FloodVulnerabilityAnalyzer(cache_enabled=True)

    # Example usage
    user_input = input("Enter Uttarakhand district name (or 'lat,lon'): ").strip()
    lat_lon = None
    district_info = None

    if "," in user_input:
        try:
            lat_str, lon_str = user_input.split(",", 1)
            lat = float(lat_str.strip()); lon = float(lon_str.strip())
            lat_lon = (lat, lon)
        except Exception:
            print("Could not parse lat,lon. Try a district name.")
            exit(1)
    else:
        coords = district_to_coords(user_input)
        if coords is None:
            print("District not in built-in list. Please use 'lat,lon' format or add district.")
            exit(1)
        lat, lon, district_info = coords
        lat_lon = (lat, lon)

    print(f"Calculating FVI for {lat_lon[0]:.5f}, {lat_lon[1]:.5f} ...")
    res = analyzer.calculate_fvi(lat_lon[0], lat_lon[1], district_info=district_info)
    
    print("\nFVI RESULT")
    print("----------")
    print(f"Location: {res['location']}")
    print(f"FVI Score: {res['fvi_score']}/100")
    print(f"Risk Level: {res['risk_level']}")
    print("Key Factors:")
    for f in res["key_factors"]:
        print(" -", f)
    print("\nInputs Snapshot:")
    import json
    print(json.dumps(res["inputs"], indent=2))