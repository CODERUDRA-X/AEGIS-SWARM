"""
AEGIS-SWARM :: Batch Processor
=================================
WHY THIS FILE EXISTS:
Processes an entire directory of drone/CCTV images in sequence,
saving each result as a structured JSON report. Designed for
offline evaluation of large image datasets (e.g., Kaggle test sets)
without running the full HTTP server.

WHY SKIP-IF-EXISTS (design decision):
Gemini API has rate limits. If a run is interrupted mid-batch,
re-running from scratch wastes quota and time. Checking for an
existing output file lets us resume exactly where we left off.

Usage:
    python run_all.py
    # Images in test_images/, reports saved to outputs/
"""

import os
import json
import time
from dotenv import load_dotenv

from agents.scout import analyze_crowd_frame
from agents.risk import evaluate_risk
from agents.critic import challenge_risk_assessment
from agents.commander import generate_action_plan

load_dotenv()


def safe_parse(text: str, fallback: dict) -> dict:
    """
    Safely parse LLM JSON output. Strips markdown fences, returns
    fallback dict on any failure so a single bad response never
    aborts the entire batch run.
    """
    try:
        if not text:
            return fallback
        cleaned = text.replace("```json", "").replace("```", "").strip()
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return fallback


def process_single_image(image_path: str, output_dir: str = "outputs") -> bool:
    filename = os.path.basename(image_path)
    out_name = f"{os.path.splitext(filename)[0]}_report.json"
    out_path = os.path.join(output_dir, out_name)

    # Skip already-processed images to preserve API quota on resume
    if os.path.exists(out_path):
        print(f"⏩ Skipping {filename} — report already exists.")
        return True

    print(f"\n🚀 Processing: {filename}...")

    try:
        # Stage 1: Scout visual extraction
        scout_raw = analyze_crowd_frame(image_path)
        scout_json = safe_parse(scout_raw, {"people_count": 0, "environment_type": "Unknown", "hazard_factors": []})
        time.sleep(2)  # Respectful pacing to avoid Gemini API rate-limit bursts

        # Stages 2+3: Risk/Critic debate loop (max 2 rounds)
        MAX_ITERATIONS = 2
        iteration = 0
        consensus_reached = False
        critic_feedback = ""
        risk_json = {}
        critic_json = {}

        while iteration < MAX_ITERATIONS and not consensus_reached:
            context = {"visual_extraction": scout_json}
            if critic_feedback:
                context["critic_override_reasoning"] = critic_feedback

            risk_raw = evaluate_risk(json.dumps(context))
            risk_json = safe_parse(risk_raw, {"threat_level": "UNKNOWN", "reason": "Parse failure."})
            time.sleep(2)

            critic_raw = challenge_risk_assessment(json.dumps(context), json.dumps(risk_json))
            critic_json = safe_parse(critic_raw, {
                "agrees_with_risk_level": True,
                "adjusted_threat_level": risk_json.get("threat_level", "UNKNOWN"),
                "critic_reasoning": "Parse failure."
            })
            time.sleep(2)

            if risk_json.get("threat_level") != critic_json.get("adjusted_threat_level"):
                critic_feedback = critic_json.get("critic_reasoning", "")
                iteration += 1
                print(f"  🔴 Debate: Critic overrode Risk (iteration {iteration}). Re-evaluating...")
            else:
                consensus_reached = True
                print("  🟢 Consensus reached.")

        # Stage 4: Commander action plan
        plan_raw = generate_action_plan(json.dumps(critic_json))
        plan_json = safe_parse(plan_raw, {"immediate_actions": ["Manual review required."], "personnel_required": True})

        # Compile and save full report
        full_report = {
            "image": filename,
            "scout_data": scout_json,
            "risk_assessment": risk_json,
            "critic_review": critic_json,
            "commander_plan": plan_json,
            "debate_iterations": iteration,
            "consensus_reached": consensus_reached,
        }

        with open(out_path, "w") as f:
            json.dump(full_report, f, indent=2)

        print(f"✅ Report saved: {out_path}")
        return True

    except Exception as e:
        print(f"❌ Failed on {filename}: {e}")
        return False


def process_all_images(input_dir: str = "test_images", output_dir: str = "outputs"):
    os.makedirs(output_dir, exist_ok=True)

    image_files = [
        f for f in os.listdir(input_dir)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp"))
    ]

    if not image_files:
        print(f"[INFO] No images found in '{input_dir}/'.")
        return

    print(f"[INFO] Found {len(image_files)} image(s) to process.")

    for filename in image_files:
        image_path = os.path.join(input_dir, filename)
        success = process_single_image(image_path, output_dir)

        if not success:
            # On failure, wait 60s before next image to recover from API throttling
            print("⏳ Cooling down 60s after failure before next image...")
            time.sleep(60)


if __name__ == "__main__":
    process_all_images()
