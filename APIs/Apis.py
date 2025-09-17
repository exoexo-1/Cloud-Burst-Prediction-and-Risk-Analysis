# APIs/Apis.py
from fastapi import FastAPI, Query, Body
from fastapi.middleware.cors import CORSMiddleware
from APIs.FVI_Fuzzy import FloodVulnerabilityAnalyzer, district_to_coords
from APIs.LLM import RAGService, RiskAnalysisLLM

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],
)

analyzer = FloodVulnerabilityAnalyzer(cache_enabled=True)

# ✅ instantiate services here
rag_service = RAGService()
llm = RiskAnalysisLLM()

@app.get("/fvi")
def get_fvi(lat: float = Query(...), lon: float = Query(...), district: str = None):
    district_info = None
    if district:
        coords = district_to_coords(district)
        if coords:
            lat, lon, district_info = coords
    result = analyzer.calculate_fvi(lat, lon, district_info=district_info)
    return result

@app.post("/analysis")
def get_analysis(request: dict = Body(...)):
    try:
        place_name = request.get("place_name")
        fvi_data = request.get("fvi_data")
        
        if not place_name or not fvi_data:
            return {"error": "Missing place_name or fvi_data", "status": "error"}
            
        rag_context = rag_service.get_context(place_name)
        analysis_result = llm.generate_risk_analysis(fvi_data, rag_context)
        
        return {
            "analysis": analysis_result["analysis"],
            "rag_context": analysis_result["rag_context"], 
            "status": "success"
        }
    except Exception as e:
        return {"error": str(e), "status": "error"}