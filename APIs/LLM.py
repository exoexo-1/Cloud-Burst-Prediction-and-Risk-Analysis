# APIs/LLM.py
import os
from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

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
            - Output: Yes / No.
            - Provide short reasoning: why you think this is likely or unlikely (mention rainfall trends, terrain, historical similarity, etc.).

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

    def generate_risk_analysis(self, fvi_data: dict, rag_context: str):
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