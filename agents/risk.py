"""
AEGIS-SWARM :: Risk Agent
==========================
ROLE: First-pass threat assessment. Receives Scout's structured visual
facts (+ optional Critic feedback on loop-back) and outputs a threat
level classification with a single-sentence justification.

WHY THIS AGENT EXISTS SEPARATELY FROM CRITIC (design decision):
The Risk Agent is the system's baseline assessor -- it reasons from
raw data without any prior assumptions. The Critic then challenges this
baseline using additional context (environment type, live telemetry).
Having them as separate agents with separate prompts prevents the
confirmation bias that would occur if a single agent both assessed
AND validated its own output.

WHY temperature=0.2 (design decision):
Slightly above 0 to allow the model to reason about edge cases, but
low enough to keep threat classifications stable and reproducible.
Higher temperature would produce inconsistent HIGH/CRITICAL flipping
across identical inputs, which undermines the debate loop's reliability.

WHY threat_level IS A Literal, NOT A str (bug fix -- confirmed 16-08-2026):
A live test on a vehicular traffic scene produced a threat_level of
"CATASTROPHIC" -- a tier that does not exist anywhere in this system's
design. The original schema declared threat_level as a plain `str` with
only a comment listing the intended four values; a comment is not an
enforced constraint, so nothing stopped the model from inventing a fifth
tier when its escalation-biased prompt ("under-reporting costs lives,
when in doubt escalate") pushed it past CRITICAL on an unusually
alarming-looking scene. Literal["LOW","MEDIUM","HIGH","CRITICAL"]
compiles down to a JSON schema enum constraint that Gemini's controlled
generation must sample from -- this makes a 5th invented tier
structurally impossible, not just discouraged by prompt wording. This
is a stronger, more general fix than any single-scenario prompt patch:
it closes the loophole for every future edge case, not just this one.

WHY ONLY 4 THREAT LEVELS (design decision):
LOW/MEDIUM/HIGH/CRITICAL maps directly to standard incident command
system (ICS) protocols used by real crowd safety personnel. This makes
Commander Agent's action plans actionable by actual responders, not
just meaningful to an AI.
"""

import os
from typing import Literal
from google import genai
from google.genai import types
from pydantic import BaseModel


class RiskAssessment(BaseModel):
    """
    Output contract for the Risk Agent.
    - threat_level: constrained to exactly these 4 values by the type
      system itself -- Gemini's structured output cannot generate
      anything outside this set, regardless of how the prompt is worded.
    - reason: single-sentence justification citing specific data points
      from Scout's report -- makes the reasoning auditable
    """
    threat_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    reason: str         # One sentence, citing specific Scout observations


def evaluate_risk(scout_json_data: str) -> str:
    """
    Classify crowd threat level from Scout's extracted facts.
    On loop-back from the debate system, scout_json_data will also
    contain a "critic_override_reasoning" key -- the Risk Agent is
    instructed to consider this feedback when revising its assessment.

    Args:
        scout_json_data: JSON string from Scout Agent (may include
                         critic_override_reasoning on second iteration).

    Returns:
        JSON string conforming to RiskAssessment schema.

    Raises:
        ValueError: If GEMINI_API_KEY is not set.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set.")

    client = genai.Client(api_key=api_key)

    prompt = f"""You are the Risk Analyst Agent in a multi-agent crowd safety system.

Input data from Scout and context:
{scout_json_data}

Your task:
Determine the threat level (LOW, MEDIUM, HIGH, or CRITICAL) for crowd crush or stampede risk.

CRITICAL CONTEXT RULE -- read scene_category before scoring:
This system's threat scale exists to assess PEDESTRIAN crowd-crush and stampede risk.
- If scene_category is "vehicular" (a traffic jam, parked vehicles, highway congestion) and
  there is no direct evidence of a life-threatening incident (active fire, structural collapse,
  a trapped ambulance, visible collision with injuries), do NOT apply pedestrian crowd-crush
  thresholds. A stopped car is not a person trapped in a crush. Standard traffic congestion,
  however dense-looking, should not exceed LOW unless direct hazard evidence is present.
- If scene_category is "pedestrian" or "mixed" with meaningful pedestrian presence, apply full
  crowd-safety scrutiny as normal.
- If scene_category is "unclear", treat the scene cautiously as if pedestrian until evidence
  clarifies otherwise -- do not use "unclear" as a reason to under-report.

Threat level guidelines (for pedestrian/mixed scenes):
- LOW: sparse density, open environment, no significant hazards
- MEDIUM: moderate density OR one environmental risk factor present
- HIGH: dense crowd OR multiple hazard factors OR restricted environment (stairs, corridors)
- CRITICAL: critical density AND restricted environment AND multiple hazard factors

There is no tier above CRITICAL. If a scene seems to warrant more concern than CRITICAL
already implies, CRITICAL is still the correct and final answer -- describe the added
severity in your reasoning text instead of inventing a new label.

If a "critic_override_reasoning" field is present in the input, this means a previous
assessment was challenged. You MUST carefully re-evaluate your threat level in light of
that feedback before responding.

Provide a 1-sentence reason that explicitly references the data points driving your conclusion."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=RiskAssessment,
            # Low temperature for consistent threat classification.
            # See module docstring for rationale.
            temperature=0.2,
        ),
    )
    return response.text
