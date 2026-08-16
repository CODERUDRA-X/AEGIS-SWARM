import os
import json
import shutil
import asyncio
import requests  # <-- ADDED THIS FOR TELEGRAM BYPASS
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import uvicorn
from dotenv import load_dotenv

# MCP CLIENT IMPORTS
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# CASPIAN SDK IMPORT
from caspian_sdk import CommClient

# MODULAR AGENT IMPORTS
from agents.scout import analyze_crowd_frame
from agents.risk import evaluate_risk
from agents.critic import challenge_risk_assessment
from agents.commander import generate_action_plan

load_dotenv()

caspian_client = CommClient()

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
MAX_FILE_SIZE = 5 * 1024 * 1024
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


async def get_telemetry_via_mcp(lat: float = 34.0522, lon: float = -118.2437) -> dict:
    print("📡 [MCP CLIENT] Establishing protocol connection...")

    server_params = StdioServerParameters(
        command="python",
        args=["mcp_server.py"],
        env=None
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                result = await session.call_tool(
                    "get_live_telemetry",
                    arguments={"lat": lat, "lon": lon}
                )

                if result.content and len(result.content) > 0:
                    raw_data = result.content[0].text
                    return json.loads(raw_data)

                return {"error": "Empty response from MCP tool"}

    except Exception as e:
        print(f"❌ [MCP CLIENT] Protocol communication failed: {e}")
        return {"source": "OFFLINE", "temperature": "N/A", "wind_speed": "N/A", "mcp_status": "Protocol Failure"}


def dispatch_caspian_alert(scout_json: dict, final_threat: str, critic_json: dict, commander_json: dict) -> dict:
    status = {"telegram": False, "email": False, "errors": []}
    
    actions_text = "\n".join(
        f"  {i+1}. {act}" for i, act in enumerate(commander_json.get("immediate_actions", []))
    )
    alert_msg = (
        f"🚨 AEGIS-SWARM EMERGENCY ALERT 🚨\n"
        f"{'='*30}\n"
        f"Scene: {scout_json.get('environment_type', 'Unknown')}\n"
        f"Threat Level: {final_threat}\n"
        f"Critic Reasoning: {critic_json.get('critic_reasoning', 'N/A')}\n\n"
        f"Commander Action Plan:\n{actions_text}\n\n"
        f"🌐 View Live HQ: https://aegis-swarm-tan.vercel.app/"
    )

    # 1. TELEGRAM (Direct Bypass - Guaranteed Delivery)
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat_id = os.environ.get("DISPATCH_TELEGRAM_CHAT_ID")
    
    if tg_token and tg_chat_id:
        try:
            tg_url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
            res = requests.post(tg_url, json={"chat_id": tg_chat_id, "text": alert_msg})
            if res.status_code == 200:
                status["telegram"] = True
                print("   ✓ [CASPIAN/TG] Dispatched to Telegram successfully!")
            else:
                print(f"   ❌ [TG ERROR] Telegram rejected payload: {res.text}")
                status["errors"].append(f"telegram: {res.text}")
        except Exception as e:
            print(f"   ❌ [TG ERROR] Request failed: {e}")
            status["errors"].append(f"telegram: {e}")

    # 2. EMAIL (Real Caspian Initiate Protocol)
    admin_email = os.environ.get("DISPATCH_ADMIN_EMAIL")
    if admin_email:
        try:
            # Connect and request INITIATE capability
            email_conn = caspian_client.connect_email(display_name="AEGIS HQ", capabilities=["INITIATE"])
            
            # Send the actual email payload
            caspian_client.initiate(connection_id=email_conn["id"], recipient=admin_email, text=alert_msg)
            status["email"] = True
            print("   ✓ [CASPIAN/HQ] Actual Email Dispatched via Caspian!")
        except Exception as e:
            print(f"   ❌ [EMAIL ERROR] Caspian server failed: {e}")
            status["errors"].append(f"email: {e}")

    return status


@app.post("/api/analyze")
@limiter.limit("10/minute")
async def analyze_incident(request: Request, file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Invalid file type.")

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
        print("👀 [API] Running Scout Agent...")
        scout_out = analyze_crowd_frame(file_path)
        scout_json = safe_json_parse(scout_out, {"people_count": 0, "blocked_paths": 0, "environment_type": "Unknown", "hazard_factors": []})

        print("🌐 [API] Requesting Context Protocol Tools...")
        mcp_data = await get_telemetry_via_mcp()

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
                print(f"🔴 [DEBATE] Critic Overrode Risk! ({current_risk_lvl} -> {adjusted_risk_lvl})")
                critic_feedback = critic_json.get("critic_reasoning")
                iteration += 1
            else:
                print("🟢 [DEBATE] Consensus Reached.")
                consensus_reached = True

        print("🛡️ [API] Running Commander Agent...")
        plan_out = generate_action_plan(json.dumps(critic_json))
        commander_json = safe_json_parse(plan_out, {"immediate_actions": ["Review logs.", "", ""]})

        final_threat = critic_json.get("adjusted_threat_level", "STANDBY")
        dispatch_status = None
        
        if final_threat in ["HIGH", "CRITICAL"]:
            print(f"🚀 [CASPIAN] High threat ({final_threat}). Initiating proactive dispatch...")
            dispatch_status = dispatch_caspian_alert(scout_json, final_threat, critic_json, commander_json)

        final_report = {
            "image": safe_filename,
            "scout_data": scout_json,
            "mcp_data": mcp_data,
            "risk_assessment": risk_json,
            "critic_review": critic_json,
            "commander_plan": commander_json,
            "dispatch_status": dispatch_status,
        }

        print(f"✅ [API] Analysis complete.")
        return final_report

    except Exception as e:
        print(f"❌ [API] System Failure: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": "Critical pipeline failure."}


if __name__ == "__main__":
    print("🔥 AEGIS-SWARM Backend initializing on port 8000...")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)