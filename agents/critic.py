"""
AEGIS-SWARM :: Critic Agent
============================
ROLE: Independent challenger. The Critic receives both the raw Scout
data AND the Risk Agent's assessment, then decides whether the threat
level is accurate, under-stated, or over-stated.

WHY THIS IS THE MOST IMPORTANT AGENT (design decision):
Every multi-agent system risks "echo chamber" failure -- agents that
agree with each other because they share the same context and biases.
The Critic is specifically prompted to DISAGREE when evidence supports it.
It has access to live environmental telemetry (via MCP) that the Risk
Agent does not weight directly, giving it genuinely independent context.

WHY THE CRITIC CAN ONLY ESCALATE, NOT DE-ESCALATE (design decision):
In a crowd safety scenario, under-reporting risk is more dangerous than
over-reporting. The Critic is instructed to elevate threat levels when
environmental factors (stairs, narrow corridors, wind) increase danger,
but NOT to reduce a HIGH to a LOW without strong justification. This is
a deliberate asymmetric design: err on the side of caution.

WHY adjusted_threat_level IS THE OUTPUT (not a boolean) (design decision):
Returning a boolean "agrees/disagrees" forces the orchestrator to make
an implicit mapping to a threat level. Returning the actual adjusted
threat level directly makes the Critic's output immediately actionable
by the Commander without additional inference.
"""

import os
from google import genai
from google.genai import types
from pydantic import BaseModel


class CriticReview(BaseModel):
    """
    Output contract for the Critic Agent.
    - agrees_with_risk_level: explicit agreement flag for the debate loop
      (False triggers a loop-back to Risk Agent with critic_reasoning as feedback)
    - adjusted_threat_level: the Critic's final threat level verdict
      (may match or differ from Risk Agent's threat_level)
    - critic_reasoning: explanation of why the Critic agreed or overrode,
      citing specific environmental or telemetry factors
    """
    agrees_with_risk_level: bool
    adjusted_threat_level: str   # LOW | MEDIUM | HIGH | CRITICAL
    critic_reasoning: str        # Must cite the specific factor driving the decision


def challenge_risk_assessment(scout_json: str, risk_json: str) -> str:
    """
    Independently evaluate whether the Risk Agent's threat classification
    is accurate given ALL available context -- including environmental
    factors and live telemetry that may not have been fully weighted.

    Args:
        scout_json: JSON string from Scout (may include live MCP telemetry
                    as "live_telemetry" field when called from server.py).
        risk_json:  JSON string from Risk Agent's current assessment.

    Returns:
        JSON string conforming to CriticReview schema.

    Raises:
        ValueError: If GEMINI_API_KEY is not set.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set.")

    client = genai.Client(api_key=api_key)

    prompt = f"""You are the Critic Agent in a multi-agent crowd safety system.
Your role is to act as an independent safety auditor -- NOT a rubber stamp.

Raw observational data (Scout output + live environmental telemetry if available):
{scout_json}

Risk Agent's current assessment:
{risk_json}

Your task:
1. Critically evaluate whether the threat level is accurate.
2. Pay special attention to:
   - Environment type: stairs, corridors, and narrow paths dramatically increase
     crush risk at the SAME density as open areas.
   - Live telemetry: high wind speed increases risk near elevated or exposed areas.
     High temperature increases crowd agitation and medical emergency risk.
   - Hazard factors: each additional hazard factor should push threat level UP,
     not be averaged away.
3. If ANY of these factors were under-weighted by the Risk Agent, you MUST
   elevate the threat level and set agrees_with_risk_level to false.
4. Provide a specific, evidence-based reason citing the exact factor(s) you are
   responding to.

Important: In a crowd safety system, under-reporting risk costs lives.
When in doubt, escalate."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=CriticReview,
            # Slightly higher than Risk Agent -- the Critic needs to reason
            # about nuanced trade-offs between multiple risk factors.
            # Still low enough for consistent, reliable outputs.
            temperature=0.2,
        ),
    )
    return response.text