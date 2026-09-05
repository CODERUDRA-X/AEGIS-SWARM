import os
import json
import shutil
import asyncio
import sys
import time
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
from agents.safety_gate import evaluate_safety_gate

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

    # 🚀 THE BULLETPROOF FIX: Exact Python interpreter + Exact file path
    mcp_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mcp_server.py")

    server_params = StdioServerParameters(
        command=sys.executable,  # Tells Docker to use the CORRECT Python environment
        args=[mcp_script_path],  # Tells Docker the exact location of the file
        env=None
    )

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                weather_result = await session.call_tool(
                    "get_live_telemetry",
                    arguments={"lat": lat, "lon": lon}
                )
                weather_data = (
                    json.loads(weather_result.content[0].text)
                    if weather_result.content else {"error": "Empty weather response"}
                )

                venue_result = await session.call_tool(
                    "get_venue_safety_status",
                    arguments={}
                )
                venue_data = (
                    json.loads(venue_result.content[0].text)
                    if venue_result.content else {"error": "Empty venue response"}
                )

                # "evidence" is the PRIMARY independent signal for crowd-crush
                # risk (occupancy/capacity/exit status). "weather" stays
                # SECONDARY environmental context -- it must not be treated
                # as proof of crowd-crush risk on its own.
                return {"evidence": venue_data, "weather": weather_data}

    except Exception as e:
        print(f"❌ [MCP CLIENT] Protocol communication failed: {e}")
        return {
            "evidence": {"mcp_status": "unavailable", "data_source": "N/A"},
            "weather": {"source": "OFFLINE", "temperature": "N/A", "wind_speed": "N/A", "mcp_status": "Protocol Failure"},
        }


def send_telegram_with_retry(tg_url: str, payload: dict, max_attempts: int = 3) -> requests.Response:
    """
    Sends the Telegram dispatch with retries on transient connection
    failures (confirmed via live deployed logs: SSLEOFError during the
    TLS handshake, likely a stale/interrupted connection in the
    container's network stack -- not a code bug, but real enough to
    fail a live demo if left unhandled).

    Each retry uses `Connection: close` to force a brand-new TCP/TLS
    connection instead of reusing a potentially-stale one from requests'
    default connection pool, since connection reuse is the most common
    cause of this specific SSL EOF error.
    """
    last_error = None
    for attempt in range(1, max_attempts + 1):
        try:
            return requests.post(
                tg_url,
                json=payload,
                timeout=10,
                headers={"Connection": "close"},  # force a fresh connection each attempt
            )
        except requests.exceptions.RequestException as e:
            last_error = e
            print(f"   ⚠️ [TG RETRY] Attempt {attempt}/{max_attempts} failed: {e}")
            if attempt < max_attempts:
                time.sleep(0.75 * attempt)  # brief backoff: 0.75s, then 1.5s
    raise last_error


def dispatch_caspian_alert(scout_json: dict, final_threat: str, critic_json: dict, commander_json: dict, gate_result: dict) -> dict:
    status = {"telegram": False, "email": False, "errors": []}

    # The alert body reflects what the deterministic safety gate actually
    # decided -- it must never present a Commander plan as "the action"
    # when the gate blocked autonomous action. Human responders reading
    # this alert need to know whether it's an authorized plan or a
    # review/re-evaluation request.
    if gate_result.get("commander_authorized") and commander_json:
        actions_text = "\n".join(
            f"  {i+1}. {act}" for i, act in enumerate(commander_json.get("immediate_actions", []))
        )
        plan_section = f"Commander Action Plan (GATE-AUTHORIZED):\n{actions_text}"
    else:
        plan_section = (
            f"⛔ NO AUTONOMOUS ACTION PLAN GENERATED.\n"
            f"Safety Gate Decision: {gate_result.get('gate_decision', 'UNKNOWN')}\n"
            f"Reason: {gate_result.get('gate_reason', 'N/A')}"
        )

    alert_msg = (
        f"🚨 AEGIS-SWARM EMERGENCY ALERT 🚨\n"
        f"{'='*30}\n"
        f"Scene: {scout_json.get('environment_type', 'Unknown')}\n"
        f"Threat Level: {final_threat}\n"
        f"Critic Reasoning: {critic_json.get('critic_reasoning', 'N/A')}\n"
        f"Evidence Classification: {critic_json.get('evidence_classification', 'unavailable')}\n\n"
        f"{plan_section}\n\n"
        f"🌐 View Live HQ: https://aegis-swarm-tan.vercel.app/"
    )

    # 1. TELEGRAM (Direct Bypass - Guaranteed Delivery, now with retry
    #    on transient SSL/connection failures)
    tg_token = os.environ.get("TELEGRAM_BOT_TOKEN")
    tg_chat_id = os.environ.get("DISPATCH_TELEGRAM_CHAT_ID")
    
    if tg_token and tg_chat_id:
        try:
            tg_url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
            res = send_telegram_with_retry(tg_url, {"chat_id": tg_chat_id, "text": alert_msg})
            if res.status_code == 200:
                status["telegram"] = True
                print("   ✓ [CASPIAN/TG] Dispatched to Telegram successfully!")
            else:
                print(f"   ❌ [TG ERROR] Telegram rejected payload: {res.text}")
                status["errors"].append(f"telegram: {res.text}")
        except Exception as e:
            print(f"   ❌ [TG ERROR] Request failed after retries: {e}")
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
                "critic_reasoning": "Error parsing critic.",
                "evidence_classification": "unavailable"
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

        print("🚧 [API] Evaluating Deterministic Safety Gate...")
        gate_result = evaluate_safety_gate(critic_json)
        print(f"   Gate decision: {gate_result['gate_decision']} — {gate_result['gate_reason']}")

        final_threat = critic_json.get("adjusted_threat_level", "STANDBY")

        # The Commander is an ACTION PLANNER, not the final safety
        # authority: it is only invoked when the deterministic gate above
        # has authorized autonomous action. An LLM (Critic or Commander)
        # can never override this check -- `commander_authorized` comes
        # from plain if/else logic in agents/safety_gate.py, not a model.
        commander_json = None
        if gate_result["commander_authorized"]:
            print("🛡️ [API] Gate authorized action — running Commander Agent...")
            plan_out = generate_action_plan(json.dumps(critic_json))
            commander_json = safe_json_parse(plan_out, {"immediate_actions": ["Review logs.", "", ""]})
        else:
            print(f"🛑 [API] Gate blocked autonomous action ({gate_result['gate_decision']}). Commander not invoked.")

        dispatch_status = None
        if final_threat in ["HIGH", "CRITICAL"]:
            print(f"🚀 [CASPIAN] High threat ({final_threat}). Initiating proactive dispatch...")
            dispatch_status = dispatch_caspian_alert(scout_json, final_threat, critic_json, commander_json, gate_result)

        final_report = {
            "image": safe_filename,
            "scout_data": scout_json,
            "mcp_data": mcp_data,
            "risk_assessment": risk_json,          # kept for backward compatibility
            "initial_assessment": risk_json,       # explicit alias required by safety-gate report spec
            "critic_review": critic_json,
            "evidence_classification": critic_json.get("evidence_classification", "unavailable"),
            "safety_gate": gate_result,
            "commander_plan": commander_json,
            "final_decision": gate_result["gate_decision"],
            "dispatch_status": dispatch_status,
        }

        print(f"✅ [API] Analysis complete. Final decision: {gate_result['gate_decision']}")
        return final_report

    except Exception as e:
        print(f"❌ [API] System Failure: {str(e)}")
        import traceback
        traceback.print_exc()
        return {"error": "Critical pipeline failure."}


if __name__ == "__main__":
    print("🔥 AEGIS-SWARM Backend initializing on port 8000...")
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)