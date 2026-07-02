import os
import json
import shutil
import asyncio
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn
from dotenv import load_dotenv

# --- MCP CLIENT IMPORTS (REAL PROTOCOL) ---
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# ==========================================
# 1. MODULAR AGENT IMPORTS
# ==========================================
from agents.scout import analyze_crowd_frame
from agents.risk import evaluate_risk
from agents.critic import challenge_risk_assessment
from agents.commander import generate_action_plan

load_dotenv()

# ==========================================
# 2. SECURITY & INITIALIZATION
# ==========================================
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="AEGIS-SWARM Orchestration Engine")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "https://aegis-swarm-tan.vercel.app/", 
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS, 
    allow_credentials=True,
    allow_methods=["POST"], 
    allow_headers=["*"],
)

os.makedirs("temp_uploads", exist_ok=True)
MAX_FILE_SIZE = 5 * 1024 * 1024 # 5 MB limits
ALLOWED_CONTENT_TYPES = ["image/jpeg", "image/png", "image/webp"]

def safe_json_parse(response_text: str, default_fallback: dict) -> dict:
    try:
        if not response_text:
            return default_fallback
        cleaned = response_text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"[ERROR] JSON Parsing Failed: {str(e)}")
        return default_fallback

# ==========================================
# 3. THE REAL MCP CLIENT INTEGRATION
# ==========================================
async def get_telemetry_via_mcp(lat: float = 34.0522, lon: float = -118.2437) -> dict:
    """
    REAL MCP CLIENT: Spins up the mcp_server.py as a subprocess, establishes
    a stdio transport connection, and invokes the protocol-compliant tool.
    """
    print("📡 [MCP CLIENT] Establishing protocol connection to external tool server...")
    
    # Define the parameters to run our standalone MCP server
    server_params = StdioServerParameters(
        command="python", # Assumes python is in the environment path
        args=["mcp_server.py"], # The standalone MCP server we just created
        env=None
    )

    try:
        # Establish the protocol connection using the official mcp SDK
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the handshake
                await session.initialize()
                
                # Call the specific tool registered in our MCP server
                result = await session.call_tool(
                    "get_live_telemetry", 
                    arguments={"lat": lat, "lon": lon}
                )
                
                # The MCP protocol returns content as a list of TextContent parts.
                # Each part's .text field is a JSON-encoded string (not a Python repr),
                # so we MUST use json.loads() here -- NOT ast.literal_eval().
                # ast.literal_eval() would crash on valid JSON booleans (true/false/null)
                # because Python uses True/False/None. This is a common MCP pitfall.
                if result.content and len(result.content) > 0:
                    raw_data = result.content[0].text
                    return json.loads(raw_data)
                
                return {"error": "Empty response from MCP tool"}
                
    except Exception as e:
        print(f"❌ [MCP CLIENT] Protocol communication failed: {e}")
        return {"source": "OFFLINE", "temperature": "N/A", "wind_speed": "N/A", "mcp_status": "Protocol Failure"}

# ==========================================
# 4. MAIN ORCHESTRATION PIPELINE
# ==========================================
@app.post("/api/analyze")
@limiter.limit("10/minute") 
async def analyze_incident(request: Request, file: UploadFile = File(...)):
    
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type.")

    # SECURITY: os.path.basename() strips any directory traversal sequences.
    # Without this, a malicious filename like "../../server.py" could overwrite
    # critical application files. basename() ensures only the final filename component
    # is ever used, regardless of what the client sends.
    safe_filename = os.path.basename(file.filename)
    if not safe_filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")

    file_path = f"temp_uploads/{safe_filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    if os.path.getsize(file_path) > MAX_FILE_SIZE:
        os.remove(file_path)
        raise HTTPException(status_code=413, detail="File exceeds 5MB limit.")

    try:
        # 1. SCOUT
        print("👀 [API] Running Scout Agent...")
        scout_out = analyze_crowd_frame(file_path)
        scout_json = safe_json_parse(scout_out, {"people_count": 0, "blocked_paths": 0, "environment_type": "Unknown", "hazard_factors": []})
        
        # 2. REAL MCP TOOL CALL (Async execution)
        print("🌐 [API] Requesting Context Protocol Tools...")
        mcp_data = await get_telemetry_via_mcp()
        
        # 3. THE DEBATE LOOP (Max 2 iterations to prevent infinite looping)
        MAX_ITERATIONS = 2
        iteration = 0
        consensus_reached = False
        critic_feedback = ""
        risk_json = {}
        critic_json = {}

        while iteration < MAX_ITERATIONS and not consensus_reached:
            print(f"⚠️ [API] Risk Assessment - Iteration {iteration + 1}...")
            
            enriched_context = {
                "visual_extraction": scout_json,
                "live_telemetry": mcp_data
            }
            if critic_feedback:
                enriched_context["CRITICAL_FEEDBACK_FROM_PREVIOUS_ROUND"] = critic_feedback
            
            risk_out = evaluate_risk(json.dumps(enriched_context))
            risk_json = safe_json_parse(risk_out, {"threat_level": "STANDBY"})
            
            print("⚖️ [API] Running Critic Agent...")
            critic_out = challenge_risk_assessment(json.dumps(enriched_context), json.dumps(risk_json))
            critic_json = safe_json_parse(critic_out, {
                "adjusted_threat_level": risk_json.get("threat_level", "STANDBY"), 
                "critic_reasoning": "Error parsing critic."
            })
            
            current_risk_lvl = risk_json.get("threat_level")
            adjusted_risk_lvl = critic_json.get("adjusted_threat_level")
            
            if current_risk_lvl != adjusted_risk_lvl:
                print(f"🔴 [DEBATE] Critic Overrode Risk! ({current_risk_lvl} -> {adjusted_risk_lvl}). Looping back...")
                critic_feedback = critic_json.get("critic_reasoning")
                iteration += 1
            else:
                print("🟢 [DEBATE] Consensus Reached.")
                consensus_reached = True

        # 4. COMMANDER
        print("🛡️ [API] Running Commander Agent...")
        plan_out = generate_action_plan(json.dumps(critic_json))
        commander_json = safe_json_parse(plan_out, {"immediate_actions": ["Review logs.", "", ""]})
        
        final_report = {
            "image": safe_filename,
            "scout_data": scout_json,
            "mcp_data": mcp_data,
            "risk_assessment": risk_json,
            "critic_review": critic_json,
            "commander_plan": commander_json
        }
        
        print(f"✅ [API] Analysis complete.")
        return final_report
        
    except Exception as e:
        print(f"❌ [API] System Failure: {str(e)}")
        return {"error": "Critical pipeline failure."}

if __name__ == "__main__":
    print("🔥 AEGIS-SWARM Backend initializing on port 8000...")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)