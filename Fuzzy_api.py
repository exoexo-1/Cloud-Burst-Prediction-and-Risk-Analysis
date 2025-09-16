# C:\major\Cloud-Burst-Prediction-and-Risk-Analysis\Fuzzy_api.py

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from FVI_Fuzzy import FloodVulnerabilityAnalyzer, district_to_coords

app = FastAPI()

# Enable CORS so React frontend can call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to ["http://localhost:3000"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = FloodVulnerabilityAnalyzer(cache_enabled=True)

@app.get("/fvi")
def get_fvi(lat: float = Query(...), lon: float = Query(...), district: str = None):
    """
    Returns Flood Vulnerability Index for given lat/lon or district
    """
    district_info = None
    if district:
        coords = district_to_coords(district)
        if coords:
            lat, lon, district_info = coords

    result = analyzer.calculate_fvi(lat, lon, district_info=district_info)
    return result


if __name__ == "__main__":
    uvicorn.run("Fuzzy_api:app", host="0.0.0.0", port=8000, reload=True)
