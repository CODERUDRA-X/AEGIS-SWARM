"""
AEGIS-SWARM :: Scout Agent
===========================
ROLE: Visual extraction only. The Scout does NOT reason about danger --
it outputs structured spatial facts that all downstream agents receive
as their shared ground truth.

WHY SEPARATE FROM RISK (design decision):
Mixing vision extraction with threat reasoning in one agent creates a
single point of failure and makes the reasoning unauditable. Keeping
Scout purely observational means Risk and Critic are always working
from the same raw facts, not from pre-interpreted conclusions.

WHY PYDANTIC SCHEMA (design decision):
Gemini's response_schema param enforces structured JSON output at the
API level -- the model is constrained to return ONLY the fields defined
in ScoutReport. This eliminates the need for fragile regex parsing and
makes the Scout's output contract explicit and machine-readable.

WHY temperature=0.1 (design decision):
Scout is a factual extraction task -- lower temperature = less creative
variation = more deterministic counts and classifications. We want the
same image to produce consistent outputs across runs.

WHY scene_category EXISTS (bug fix -- confirmed 16-08-2026):
A live test sent a dense vehicular traffic jam through the pipeline.
Scout correctly reported high entity density, multiple blocked paths,
and a restricted environment -- and the downstream Risk/Critic agents,
which were only ever tuned for PEDESTRIAN crowd-crush risk, applied
that same crush logic to cars and rated it CATASTROPHIC. The visual
signature of "many entities packed into a constrained space" looks
structurally identical whether the entities are humans or vehicles,
but the risk profile is completely different (a traffic jam is not a
stampede hazard). scene_category gives Risk the context it needs to
tell these apart, without touching Scout's core job: it still only
observes and reports, it does not judge danger.
"""

import os
from typing import Literal
from google import genai
from google.genai import types
from pydantic import BaseModel


class ScoutReport(BaseModel):
    """
    Structured output contract for the Scout Agent.
    Every field is consumed by downstream agents (Risk, Critic).
    - people_count: absolute headcount estimate of HUMAN entities only
      (do not count vehicles here -- see scene_category for that)
    - density: qualitative descriptor ("sparse", "moderate", "dense", "critical")
    - blocked_paths: number of visible egress routes that appear obstructed
    - environment_type: spatial context -- critical for risk calibration
      (stairs carry higher crush risk than open streets at same density)
    - hazard_factors: list of observed visual risks beyond density alone
    - scene_category: what KIND of "crowd" this is. A dense traffic jam
      and a dense pedestrian crowd look structurally similar (high
      entity count, blocked paths) but carry completely different risk
      profiles. This field is the difference between the two.
    """
    people_count: int
    density: str
    blocked_paths: int
    environment_type: str   # e.g., "stairway", "crosswalk", "hallway", "open plaza"
    hazard_factors: list[str]  # e.g., ["narrow path", "carrying heavy objects"]
    scene_category: Literal["pedestrian", "vehicular", "mixed", "unclear"]


def analyze_crowd_frame(image_path: str) -> str:
    """
    Upload an image to Gemini's vision model and extract structured
    crowd intelligence. Cleans up the uploaded file after extraction
    to avoid retaining surveillance footage on external servers
    (privacy best practice for a crowd safety system).

    Args:
        image_path: Local path to the drone/CCTV image file.

    Returns:
        JSON string conforming to ScoutReport schema.

    Raises:
        ValueError: If GEMINI_API_KEY is not set in environment.
        Exception: Propagated from Gemini API on model or network failure.
    """
    # Fail fast with a clear message if the API key is missing.
    # Without this check, the Gemini client silently accepts None and
    # only raises a confusing AuthenticationError much later in the call.
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not set. "
            "Create a .env file with: GEMINI_API_KEY=your_key_here"
        )

    client = genai.Client(api_key=api_key)
    uploaded_file = None

    try:
        print(f"  [Scout] Uploading '{image_path}' to Gemini vision API...")
        uploaded_file = client.files.upload(file=image_path)

        prompt = """You are analyzing drone or security camera footage for crowd safety assessment.

Extract the following with high precision:
1. Count the number of visible HUMAN people (estimate if partially occluded).
   Do NOT count vehicles, animals, or objects as people.
2. Classify density: sparse (<1 person/m²), moderate (1-2/m²), dense (2-4/m²), or critical (>4/m²).
   This density estimate applies to HUMAN entities only.
3. Count the number of blocked or obstructed exit/egress paths visible.
4. Identify the environment type (e.g., "stairway", "open street", "narrow corridor", "plaza", "crosswalk").
5. List specific visual hazard factors observed (e.g., "uneven terrain", "crowd carrying bags",
   "single exit point", "low visibility", "wet surface").
6. Classify scene_category -- this is critical and must be evaluated carefully:
   - "pedestrian": the scene is primarily people on foot (crowds, queues, stairways, gatherings)
   - "vehicular": the scene is primarily vehicles (cars, motorcycles, trucks) -- e.g. a traffic
     jam, a parking lot, a highway. A dense traffic jam is a VEHICULAR scene, not a human crowd,
     even though it may look visually dense and congested.
   - "mixed": significant presence of both pedestrians and vehicles in close proximity
     (e.g., pedestrians crossing near heavy traffic, a market street with both foot and vehicle traffic)
   - "unclear": cannot confidently determine which category applies from the image

Be factual and precise. Do not infer danger or risk level -- only report what is visually present.
The distinction between pedestrian and vehicular scenes matters enormously for how downstream
safety systems will interpret this data -- a stopped car is not a person trapped in a crush,
so classify carefully and do not default to "pedestrian" when the scene is clearly traffic."""

        response = client.models.generate_content(
            model="gemini-3.5-flash-lite",
            contents=[uploaded_file, prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=ScoutReport,
                # Low temperature: factual extraction task.
                # Higher temp would introduce hallucinated variation in counts.
                temperature=0.1,
            ),
        )
        return response.text

    finally:
        # PRIVACY: Always delete the uploaded file from Gemini's servers
        # after extraction, regardless of whether the API call succeeded.
        # Crowd surveillance footage must not persist on external systems.
        if uploaded_file is not None:
            try:
                client.files.delete(name=uploaded_file.name)
                print(f"  [Scout] Uploaded file deleted from Gemini servers (privacy cleanup).")
            except Exception as cleanup_err:
                # Log but don't raise -- cleanup failure should not mask the
                # primary result if extraction succeeded.
                print(f"  [Scout] Warning: Could not delete uploaded file: {cleanup_err}")
