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

IMPORTANT SCOPE OF THE ESCALATION BIAS (bug fix -- confirmed 16-08-2026):
A live test showed this escalation bias, when applied to a vehicular
traffic scene it was never meant to score, pushed the Critic to invent
a threat tier ("CATASTROPHIC") beyond the system's defined ceiling. The
bias is correct and must stay -- for genuine PEDESTRIAN crowd danger,
escalating on uncertainty saves lives. But it must not fire on scenes
that were never pedestrian crush scenarios to begin with. The fix here
is two-layered: (1) the schema itself now makes inventing a 5th tier
structurally impossible (see adjusted_threat_level's Literal type), and
(2) the prompt now explicitly scopes the escalation instinct to
pedestrian-relevant scenes, so the Critic's aggression is aimed at the
right target instead of firing indiscriminately.

WHY adjusted_threat_level IS THE OUTPUT (not a boolean) (design decision):
Returning a boolean "agrees/disagrees" forces the orchestrator to make
an implicit mapping to a threat level. Returning the actual adjusted
threat level directly makes the Critic's output immediately actionable
by the Commander without additional inference.
"""

import os
from typing import Literal
from google import genai
from google.genai import types
from pydantic import BaseModel


class CriticReview(BaseModel):
    """
    Output contract for the Critic Agent.
    - agrees_with_risk_level: explicit agreement flag for the debate loop
      (False triggers a loop-back to Risk Agent with critic_reasoning as feedback)
    - adjusted_threat_level: constrained to exactly these 4 values by the
      type system itself -- the Critic cannot generate a tier beyond
      CRITICAL no matter how alarming the scene looks or how the prompt
      is worded. This closes the exact loophole that previously produced
      an invented "CATASTROPHIC" label.
    - critic_reasoning: explanation of why the Critic agreed or overrode,
      citing specific environmental or telemetry factors
    """
    agrees_with_risk_level: bool
    adjusted_threat_level: Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    critic_reasoning: str        # Must cite the specific factor driving the decision
    evidence_classification: Literal["supporting", "contradicting", "insufficient", "unavailable"]
    # How the independent MCP evidence (occupancy/capacity/exits -- NOT
    # weather) relates to the Risk Agent's assessment:
    #   supporting     - evidence backs the current threat level
    #   contradicting   - evidence conflicts with it (e.g. occupancy near
    #                      capacity while Risk said LOW, or vice versa)
    #   insufficient    - evidence exists but doesn't clearly confirm or
    #                      deny the assessment
    #   unavailable     - MCP evidence could not be retrieved this cycle


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

Raw observational data (Scout visual output, plus MCP-provided context under
"live_telemetry" if available). "live_telemetry" contains up to two sub-keys:
  - "evidence": venue occupancy/capacity/exit-availability data. This is your
    PRIMARY independent evidence for crowd-crush risk -- it directly measures
    how full the space is and how much egress capacity exists. If its
    "data_source" says SIMULATED, treat the numbers as real for this
    exercise but note in your reasoning that the source is simulated, not a
    live venue feed.
  - "weather": temperature/wind. This is SECONDARY environmental context
    only. Weather alone is NEVER sufficient grounds to raise or lower a
    threat level -- it can only nudge a decision that is already supported
    by visual density/hazard data or by the "evidence" occupancy data.

{scout_json}

Risk Agent's current assessment:
{risk_json}

Your task:
1. Critically evaluate whether the threat level is accurate.
2. First check scene_category in the Scout data:
   - If scene_category is "vehicular" and there is no direct evidence of a life-threatening
     incident (active fire, structural collapse, trapped ambulance, visible injury-causing
     collision), your escalation instinct does NOT apply here. Ordinary traffic congestion,
     however visually dense, should generally stay at LOW unless direct hazard evidence exists.
     Do not escalate a normal traffic jam just because it looks chaotic.
   - If scene_category is "pedestrian" or "mixed" with real pedestrian presence, apply full
     scrutiny below as normal.
3. For pedestrian/mixed scenes, weigh evidence in this order of authority:
   a. Occupancy/capacity/exit data in "evidence" (if available): compare
      occupancy_pct and exits_available/exits_total against the Risk Agent's
      threat level. High occupancy_pct with few exits available should push
      the threat level UP even if the visual density looked moderate. Low
      occupancy_pct with exits available and no active_incident_flag is a
      reason to NOT escalate further on visuals alone.
   b. Environment type: stairs, corridors, and narrow paths dramatically increase
      crush risk at the SAME density as open areas.
   c. Hazard factors: each additional hazard factor should push threat level UP,
      not be averaged away.
   d. Weather (secondary only): high wind speed near elevated/exposed areas, or
      high temperature increasing crowd agitation/medical risk, can reinforce a
      conclusion already reached from (a)-(c), but must not drive the decision
      by itself.
4. If ANY of the pedestrian-relevant factors above were under-weighted by the Risk Agent, you
   MUST elevate the threat level and set agrees_with_risk_level to false.
5. Set evidence_classification based ONLY on the "evidence" (occupancy/capacity/exits) data,
   not weather:
   - "supporting" if it backs the (possibly adjusted) threat level
   - "contradicting" if it conflicts with the Risk Agent's assessment
   - "insufficient" if it neither clearly confirms nor denies the assessment
   - "unavailable" if "evidence" is missing or its mcp_status shows failure
6. Provide a specific, evidence-based reason citing the exact factor(s) you are responding to,
   distinguishing what came from "evidence" vs. visual data vs. weather.

There is no tier above CRITICAL in this system. If a scene feels more severe than CRITICAL
already conveys, CRITICAL remains the correct final answer -- put the added severity into
your reasoning text, not into a new invented label.

Important: In a genuine pedestrian crowd-safety scenario, under-reporting risk costs lives --
when in doubt about a PEDESTRIAN scene, escalate. That bias does not extend to scenes that
are not pedestrian crowd-crush scenarios in the first place."""

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
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
