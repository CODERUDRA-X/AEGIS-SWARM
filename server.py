import os
import json
import shutil
import requests # Naya import real API calls ke liye
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

from agents.scout import analyze_crowd_frame
from agents.risk import evaluate_risk
from agents.critic import challenge_risk_assessment
from agents.commander import generate_action_plan

load_dotenv()

app = FastAPI(title="AEGIS-SWARM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("temp_uploads", exist_ok=True)

# ==========================================
# 🛠️ REAL MCP TOOL: Live Environmental Telemetry
# ==========================================
def mcp_get_live_telemetry(lat: float = 34.0522, lon: float = -118.2437):
    """
    REAL MCP TOOL: Makes an actual HTTP request to an external Weather API.
    (Defaults to Los Angeles coordinates, simulating drone GPS metadata).
    """
    print(f"📡 [MCP SERVER] Executing external HTTP request for live telemetry at Lat:{lat}, Lon:{lon}...")
    
    # Real live weather API (Open-Meteo)
    url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json().get("current_weather", {})
            
            temperature = data.get('temperature', 'Unknown')
            wind_speed = data.get('windspeed', 'Unknown')
            
            print(f"✅ [MCP SERVER] Live Data Secured: {temperature}°C, Wind: {wind_speed} km/h")
            
            return {
                "source": "Open-Meteo Live External API",
                "temperature": f"{temperature}°C",
                "wind_speed": f"{wind_speed} km/h",
                "mcp_status": "Success - Live telemetry integrated."
            }
        else:
            print(f"⚠️ [MCP SERVER] API returned status code {response.status_code}")
            return {"error": "External API failed to respond properly."}
            
    except requests.exceptions.RequestException as e:
        print(f"❌ [MCP SERVER] HTTP Request Failed: {e}")
        return {"error": "Network timeout while reaching external tool."}

@app.post("/api/analyze")
async def analyze_incident(file: UploadFile = File(...)):
    print(f"\n🚀 [API] Received emergency feed: {file.filename}")
    
    file_path = f"temp_uploads/{file.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    try:
        # 1. SCOUT AGENT
        print("👀 [API] Running Scout Agent...")
        scout_out = analyze_crowd_frame(file_path)
        scout_json = json.loads(scout_out)
        
        # 2. ACTUAL MCP TOOL EXECUTION
        # (In a real scenario, lat/lon comes from image EXIF data. Here we simulate the drone's GPS)
        drone_lat = 34.0522 
        drone_lon = -118.2437
        mcp_data = mcp_get_live_telemetry(drone_lat, drone_lon)
        
        # Combine Scout Data and Real MCP Data for the Risk Agent
        enriched_context = {
            "visual_extraction": scout_json,
            "live_telemetry": mcp_data
        }
        enriched_context_str = json.dumps(enriched_context)
        
        # 3. RISK AGENT (Now upgraded with REAL External Data)
        print("⚠️ [API] Running Risk Agent with Real Telemetry...")
        risk_out = evaluate_risk(enriched_context_str)
        
        # 4. CRITIC AGENT
        print("⚖️ [API] Running Critic Agent...")
        critic_out = challenge_risk_assessment(enriched_context_str, risk_out)
        
        # 5. COMMANDER AGENT
        print("🛡️ [API] Running Commander Agent...")
        plan_out = generate_action_plan(critic_out)
        
        # Package the final response for the Next.js Dashboard
        final_report = {
            "image": file.filename,
            "scout_data": scout_json,
            "mcp_data": mcp_data, # REAL API Data
            "risk_assessment": json.loads(risk_out),
            "critic_review": json.loads(critic_out),
            "commander_plan": json.loads(plan_out)
        }
        
        print(f"✅ [API] Analysis complete for {file.filename}")
        return final_report
        
    except Exception as e:
        print(f"❌ [API] System Failure: {str(e)}")
        return {"error": str(e)}

if __name__ == "__main__":
    print("🔥 AEGIS-SWARM Backend initializing on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)