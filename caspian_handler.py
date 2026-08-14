"""
AEGIS-SWARM x Caspian :: Multi-Channel Consensus Safety Agent
================================================================
WHY THIS FILE EXISTS:
The Caspian AI Agent Hackathon requires ONE on_message handler serving
AT LEAST TWO communication channels -- duplicating the handler per
channel disqualifies the submission. This file wraps the EXISTING
AEGIS-SWARM 4-agent pipeline (Scout -> Risk -> Critic -> Commander)
behind a single Caspian handler that answers identically whether the
message arrives via Telegram or Email.

The reasoning pipeline itself is UNCHANGED from the original AEGIS-SWARM
project -- only the entry point changes. This is intentional: the
hackathon rewards creativity of use case, not rewriting a working system.

USE CASE (the "creative angle" for judging):
"Text or email a photo from any crowd/disaster scene to one AI safety
identity -- reachable on Telegram AND Email -- and get back a
consensus-validated threat assessment that four independent agents
debated before agreeing on, not a single model's first guess."
"""

import os
import json
import requests
from dotenv import load_dotenv
from caspian_sdk import CommClient

# Reuse the EXISTING agent pipeline -- no agent logic is duplicated or
# rewritten here. This is the same Scout/Risk/Critic/Commander code
# already used by the FastAPI backend (server.py).
from agents.scout import analyze_crowd_frame
from agents.risk import evaluate_risk
from agents.critic import challenge_risk_assessment
from agents.commander import generate_action_plan

load_dotenv()

client = CommClient()  # reads COMM_API_KEY / COMM_BASE_URL from .env (via `comm init`)


def safe_parse(text: str, fallback: dict) -> dict:
    """Same crash-prevention parser used in server.py -- strips markdown
    fences from LLM output and returns a typed fallback on any failure,
    so a single bad agent response never crashes the Caspian listen loop."""
    try:
        if not text:
            return fallback
        cleaned = text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return fallback


def download_image(url: str, dest_path: str = "temp_uploads/incoming.jpg") -> str:
    """
    Caspian message attachments arrive as URLs (Telegram photo / email
    attachment), not local file paths. Scout Agent expects a local file
    path, so we download the attachment once before running the pipeline.
    """
    os.makedirs("temp_uploads", exist_ok=True)
    response = requests.get(url, timeout=15)
    response.raise_for_status()
    with open(dest_path, "wb") as f:
        f.write(response.content)
    return dest_path


def extract_image_url(message) -> str | None:
    """
    NOTE: The exact attribute Caspian uses for attachments is not
    confirmed in the public docs at the time of writing. Rather than
    guess one name and risk an AttributeError crash, this checks every
    plausible field defensively. Run this once locally and print
    vars(message) on a real incoming message to confirm the true name,
    then trim this list down to just that one.
    """
    for attr in ("attachments", "files", "media", "images"):
        value = getattr(message, attr, None)
        if value:
            item = value[0]
            # Item might be an object with .url, or a plain string URL.
            return getattr(item, "url", item)
    return None


def run_aegis_pipeline_text_only(description: str) -> str:
    """
    Fallback path for messages with no image attached -- e.g. an
    emergency worker typing "Fire detected near school entrance" with
    no photo available. Scout's vision step is skipped; the user's
    text becomes the observation directly, and Risk/Critic/Commander
    run exactly as they do on Scout's normal output.
    """
    scout_json = {
        "people_count": "unknown (text report, no image)",
        "environment_type": "unspecified",
        "hazard_factors": [description],
        "source": "user-reported text, not vision-extracted",
    }

    risk_raw = evaluate_risk(json.dumps({"visual_extraction": scout_json}))
    risk_json = safe_parse(risk_raw, {"threat_level": "UNKNOWN", "reason": "Parse failure."})

    critic_raw = challenge_risk_assessment(json.dumps({"visual_extraction": scout_json}), json.dumps(risk_json))
    critic_json = safe_parse(critic_raw, {
        "adjusted_threat_level": risk_json.get("threat_level", "UNKNOWN"),
        "critic_reasoning": "Parse failure."
    })

    plan_raw = generate_action_plan(json.dumps(critic_json))
    plan_json = safe_parse(plan_raw, {"immediate_actions": ["Manual review required."]})

    actions = plan_json.get("immediate_actions", [])
    actions_text = "\n".join(f"  {i+1}. {a}" for i, a in enumerate(actions))

    return (
        f"AEGIS-SWARM Consensus Report (text-only report)\n"
        f"{'='*30}\n"
        f"Reported: {description}\n"
        f"Threat Level: {critic_json.get('adjusted_threat_level', 'UNKNOWN')}\n"
        f"Reasoning: {critic_json.get('critic_reasoning', 'N/A')}\n\n"
        f"Recommended Actions:\n{actions_text}\n\n"
        f"Note: this assessment is based on your text description only. "
        f"Send a photo for a more precise vision-based analysis."
    )
    """
    Runs the exact same consensus debate loop as server.py, but returns
    a plain-text summary suitable for a chat/email reply instead of raw
    JSON -- Telegram and Email are read by humans, not dashboards.
    """
    scout_raw = analyze_crowd_frame(image_path)
    scout_json = safe_parse(scout_raw, {
        "people_count": 0, "environment_type": "Unknown", "hazard_factors": []
    })

    MAX_ITERATIONS = 2
    iteration = 0
    consensus_reached = False
    critic_feedback = ""
    risk_json, critic_json = {}, {}

    while iteration < MAX_ITERATIONS and not consensus_reached:
        context = {"visual_extraction": scout_json}
        if critic_feedback:
            context["critic_override_reasoning"] = critic_feedback

        risk_raw = evaluate_risk(json.dumps(context))
        risk_json = safe_parse(risk_raw, {"threat_level": "UNKNOWN", "reason": "Parse failure."})

        critic_raw = challenge_risk_assessment(json.dumps(context), json.dumps(risk_json))
        critic_json = safe_parse(critic_raw, {
            "agrees_with_risk_level": True,
            "adjusted_threat_level": risk_json.get("threat_level", "UNKNOWN"),
            "critic_reasoning": "Parse failure."
        })

        if risk_json.get("threat_level") != critic_json.get("adjusted_threat_level"):
            critic_feedback = critic_json.get("critic_reasoning", "")
            iteration += 1
        else:
            consensus_reached = True

    plan_raw = generate_action_plan(json.dumps(critic_json))
    plan_json = safe_parse(plan_raw, {"immediate_actions": ["Manual review required."]})

    # Human-readable reply -- this is what actually shows up in Telegram/Email
    threat = critic_json.get("adjusted_threat_level", "UNKNOWN")
    reasoning = critic_json.get("critic_reasoning", "No override triggered.")
    actions = plan_json.get("immediate_actions", [])
    actions_text = "\n".join(f"  {i+1}. {a}" for i, a in enumerate(actions))

    return (
        f"AEGIS-SWARM Consensus Report\n"
        f"{'='*30}\n"
        f"Scene: {scout_json.get('environment_type', 'Unknown')} "
        f"({scout_json.get('people_count', 0)} people detected)\n"
        f"Final Threat Level: {threat}\n"
        f"Debate rounds: {iteration + 1} | Consensus: {'YES' if consensus_reached else 'ESCALATED'}\n"
        f"Critic reasoning: {reasoning}\n\n"
        f"Recommended Actions:\n{actions_text}"
    )


# ================================================================
# THE SINGLE HANDLER -- serves Telegram AND Email identically.
# This is the piece the hackathon rules require: ONE function,
# not one-per-channel.
# ================================================================
@client.on_message
def handle(message):
    image_url = extract_image_url(message)

    try:
        if image_url:
            local_path = download_image(image_url)
            report = run_aegis_pipeline(local_path)
            message.reply(report)
        elif message.text and message.text.strip():
            # Text-only report -- e.g. "Fire detected near school entrance"
            report = run_aegis_pipeline_text_only(message.text.strip())
            message.reply(report)
        else:
            message.reply(
                "Send me a photo of a crowd, disaster, or safety scene -- "
                "or just describe what you're seeing in text -- and I'll run "
                "it through AEGIS-SWARM's 4-agent consensus pipeline "
                "(Scout -> Risk -> Critic -> Commander) and reply with a "
                "validated threat assessment."
            )
    except Exception:
        # Never surface a raw stack trace to the person on the other end
        # of Telegram/Email -- log it server-side for debugging instead.
        print(f"[AEGIS-SWARM] Pipeline error while handling message: {message!r}")
        import traceback
        traceback.print_exc()
        message.reply(
            "Unable to analyze this right now. Please try again with a "
            "clearer photo or a short text description of the situation."
        )


if __name__ == "__main__":
    # Free channels: connect instantly, no external sign-in required.
    client.connect_telegram(bot_token=os.environ["TELEGRAM_BOT_TOKEN"])
    email_inbox = client.connect_email(display_name="AEGIS-SWARM Safety Agent")
    print(f"AEGIS-SWARM is live. Email it at: {email_inbox['address']}")
    print("AEGIS-SWARM is live on Telegram.")

    client.listen()  # one loop, both channels, one handler
