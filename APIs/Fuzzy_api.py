from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from FVI_Fuzzy import FloodVulnerabilityAnalyzer, district_to_coords

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

analyzer = FloodVulnerabilityAnalyzer(cache_enabled=True)

@app.get("/fvi")
def get_fvi(lat: float = Query(...), lon: float = Query(...), district: str = None):
    district_info = None
    if district:
        coords = district_to_coords(district)
        if coords:
            lat, lon, district_info = coords
    return analyzer.calculate_fvi(lat, lon, district_info=district_info)
