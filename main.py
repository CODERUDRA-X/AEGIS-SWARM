"""
AEGIS-SWARM :: CLI Runner (Local Debug Mode)
==============================================
WHY THIS FILE EXISTS:
server.py exposes the pipeline via HTTP for the Next.js frontend.
main.py is the local CLI entry point for rapid testing without
spinning up the full FastAPI server -- useful during development
and for Kaggle notebook demonstrations.

It mirrors the same pipeline logic as server.py (debate loop,
safe parsing, error handling) so results are consistent between
the API and CLI modes.

Usage:
    python main.py
    # Edit the `target_image` variable below to point at any test image.
"""

import os
import json
from dotenv import load_dotenv

from agents.scout import analyze_crowd_frame
from agents.risk import evaluate_risk
from agents.critic import challenge_risk_assessment
from agents.commander import generate_action_plan

load_dotenv()


def safe_parse(text: str, fallback: dict) -> dict:
    """
    Safely parse a JSON string from an LLM response.
    LLMs sometimes wrap output in markdown fences (```json```).
    We strip those before parsing. On any failure, return the fallback
    dict rather than crashing -- one agent failing should not kill
    the whole pipeline.
    """
    try:
        if not text:
            return fallback
        cleaned = text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f"  [WARN] JSON parse failed: {e}. Using fallback.")
        return fallback


def run_aegis_pipeline(image_path: str):
    print(f"\n{'='*55}")
    print(f"  AEGIS-SWARM :: INITIATING FOR: {image_path}")
    print(f"{'='*55}\n")

    # ── STAGE 1: SCOUT ──────────────────────────────────────
    # The Scout agent does visual extraction only -- it does not
    # reason about danger. It outputs structured spatial facts
    # (people count, environment type, hazard factors) that all
    # downstream agents receive as their ground truth.
    print("👁️  [STAGE 1] Scout Agent — Visual Extraction")
    try:
        scout_raw = analyze_crowd_frame(image_path)
        scout_json = safe_parse(scout_raw, {
            "people_count": 0, "density": "unknown",
            "blocked_paths": 0, "environment_type": "Unknown", "hazard_factors": []
        })
        print(json.dumps(scout_json, indent=2))
    except Exception as e:
        print(f"  [ERROR] Scout Agent failed: {e}")
        return
    print("-" * 55)

    # ── STAGE 2+3: RISK/CRITIC DEBATE LOOP ──────────────────
    # WHY A LOOP (design decision):
    # A single pass (Risk → Critic) means the Risk Agent never
    # gets to incorporate the Critic's challenge. The loop feeds
    # the Critic's reasoning back to Risk as explicit context so
    # Risk can update its threat level. Max 2 iterations prevents
    # infinite cycling while still allowing one meaningful revision.
    MAX_ITERATIONS = 2
    iteration = 0
    consensus_reached = False
    critic_feedback = ""
    risk_json = {}
    critic_json = {}

    while iteration < MAX_ITERATIONS and not consensus_reached:
        print(f"⚠️  [STAGE 2] Risk Agent — Threat Assessment (Iteration {iteration + 1})")

        # Build enriched context: Scout data + any prior Critic feedback
        context = {"visual_extraction": scout_json}
        if critic_feedback:
            # On loop-back, the Risk Agent receives the Critic's explicit
            # challenge as part of its input, forcing it to reconsider.
            context["critic_override_reasoning"] = critic_feedback

        try:
            risk_raw = evaluate_risk(json.dumps(context))
            risk_json = safe_parse(risk_raw, {"threat_level": "UNKNOWN", "reason": "Parse failure."})
            print(json.dumps(risk_json, indent=2))
        except Exception as e:
            print(f"  [ERROR] Risk Agent failed: {e}")
            break

        print(f"⚖️  [STAGE 3] Critic Agent — Challenging Risk (Iteration {iteration + 1})")
        try:
            critic_raw = challenge_risk_assessment(json.dumps(context), json.dumps(risk_json))
            critic_json = safe_parse(critic_raw, {
                "agrees_with_risk_level": True,
                "adjusted_threat_level": risk_json.get("threat_level", "UNKNOWN"),
                "critic_reasoning": "Parse failure."
            })
            print(json.dumps(critic_json, indent=2))
        except Exception as e:
            print(f"  [ERROR] Critic Agent failed: {e}")
            break

        # Consensus check: if Critic changed the threat level, loop back
        if risk_json.get("threat_level") != critic_json.get("adjusted_threat_level"):
            print(f"\n  🔴 DEBATE: Critic overrode Risk "
                  f"({risk_json.get('threat_level')} → {critic_json.get('adjusted_threat_level')}). "
                  f"Sending feedback to Risk for re-evaluation...\n")
            critic_feedback = critic_json.get("critic_reasoning", "")
            iteration += 1
        else:
            print("\n  🟢 CONSENSUS REACHED.\n")
            consensus_reached = True

    print("-" * 55)

    # ── STAGE 4: COMMANDER ──────────────────────────────────
    # Commander receives the FINAL, consensus-validated threat
    # level from the Critic (not the raw Risk output) to ensure
    # the action plan reflects the debated, adjusted reality.
    print("🛡️  [STAGE 4] Commander Agent — Action Plan")
    try:
        plan_raw = generate_action_plan(json.dumps(critic_json))
        plan_json = safe_parse(plan_raw, {"immediate_actions": ["Manual review required."], "personnel_required": True})
        print(json.dumps(plan_json, indent=2))
    except Exception as e:
        print(f"  [ERROR] Commander Agent failed: {e}")

    print(f"\n{'='*55}\n")


if __name__ == "__main__":
    target_image = "test_images/stairway_congestion_01.jpg"
    if os.path.exists(target_image):
        run_aegis_pipeline(target_image)
    else:
        print(f"[INFO] Test image not found at '{target_image}'.")
        print("[INFO] Add an image to test_images/ and update the path above.")
