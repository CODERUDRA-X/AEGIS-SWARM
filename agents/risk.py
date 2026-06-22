import os
from google import genai
from google.genai import types
from pydantic import BaseModel

class RiskAssessment(BaseModel):
    threat_level: str
    reason: str

def evaluate_risk(scout_json_data: str) -> str:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    
    prompt = f"""You are the Risk Analyst Agent. 
    Review this raw Scout data: {scout_json_data}
    
    Determine the threat level (LOW, MEDIUM, HIGH, CRITICAL) for crowd crush or stampede.
    Provide a concise 1-sentence reason based strictly on the data."""
    
    response = client.models.generate_content(
        model='gemini-2.5-flash', # Faster model for text reasoning
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RiskAssessment,
            temperature=0.2
        ),
    )
    return response.text