"""
AEGIS-SWARM :: Commander Agent
=================================
ROLE: Final decision-maker. Receives the Critic's consensus-validated
threat assessment and generates a specific, actionable response plan.

WHY COMMANDER RECEIVES CRITIC OUTPUT, NOT RISK OUTPUT (design decision):
The Commander must act on the FINAL, debate-validated threat level --
not on the Risk Agent's initial (potentially under-stated) assessment.
Routing Commander through Critic's output ensures that any threat
escalations from the debate loop are fully reflected in the action plan.

WHY 2-3 ACTIONS ONLY (design decision):
In a real crowd emergency, responders have seconds to parse instructions.
A 10-point action list causes decision paralysis. The 2-3 action
constraint forces the model to prioritize the highest-impact interventions
rather than generating comprehensive-but-unactionable lists.

WHY personnel_required IS A BOOLEAN (design decision):
Downstream systems (dispatch, alert systems) need a binary signal to
trigger human escalation. A boolean is directly machine-readable without
NLP parsing -- a judge or integration can check `if personnel_required`
and trigger a real-world response.

WHY temperature=0.3 (design decision):
Slightly higher than Scout/Risk/Critic to allow the Commander to generate
varied, creative action plans tailored to the specific scenario rather
than templated responses. Still low enough to keep plans operationally
coherent and non-contradictory.
"""

import os
from google import genai
from google.genai import types
from pydantic import BaseModel


class ActionPlan(BaseModel):
    """
    Output contract for the Commander Agent.
    - immediate_actions: 2-3 specific, ordered steps for first responders.
      Each step should be a complete, executable instruction.
    - personnel_required: True if the threat level requires dispatching
      human responders (physical intervention beyond automated alerts).
    """
    immediate_actions: list[str]  # 2-3 ordered, specific response steps
    personnel_required: bool      # True = dispatch human responders


def generate_action_plan(critic_json_data: str) -> str:
    """
    Generate a tactical action plan from the Critic's validated threat
    assessment. Plans are specific to the threat level, environment type,
    and hazard factors identified earlier in the pipeline.

    Args:
        critic_json_data: JSON string from Critic Agent containing
                          adjusted_threat_level and critic_reasoning.

    Returns:
        JSON string conforming to ActionPlan schema.

    Raises:
        ValueError: If GEMINI_API_KEY is not set.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set.")

    client = genai.Client(api_key=api_key)

    prompt = f"""You are the Commander Agent in a multi-agent crowd safety system.
You are the final decision-maker. The threat assessment below has been independently
validated by a Critic Agent -- treat it as ground truth.

Validated threat assessment:
{critic_json_data}

Your task:
Generate a tactical action plan with exactly 2-3 immediate, specific steps.

Requirements for each step:
- Start with an action verb (Deploy, Activate, Redirect, Dispatch, Close, Alert...)
- Be specific to the environment type and threat level in the assessment
- Be executable by a real crowd safety officer in under 60 seconds
- Address the specific hazard factors mentioned in the assessment

Threat level guidance:
- LOW: preventive measures, monitoring adjustments
- MEDIUM: active crowd flow management, barrier deployment
- HIGH: partial evacuation, emergency services on standby
- CRITICAL: immediate full evacuation, emergency services dispatch, area lockdown

Set personnel_required to True for HIGH or CRITICAL threat levels."""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=ActionPlan,
            # Slightly higher temperature than other agents.
            # See module docstring for rationale.
            temperature=0.3,
        ),
    )
    return response.text
