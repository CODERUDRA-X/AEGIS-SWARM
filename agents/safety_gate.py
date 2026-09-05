"""
AEGIS-SWARM :: Deterministic Evidence/Safety Gate
====================================================
ROLE: Sits between the Critic and the Commander. Decides whether an
autonomous action plan may be generated/executed, or whether the
situation must instead be routed to a human, or sent back for
re-evaluation -- using plain, deterministic Python logic with NO LLM
call and NO network access.

WHY THIS EXISTS (design decision):
Before this gate, the Critic (an LLM) could produce an adjusted_threat_level
and the very next step (Commander, another LLM) would immediately turn
that into an "actionable" plan and, for HIGH/CRITICAL, trigger a real
Telegram/email dispatch. Nothing forced the pipeline to check whether the
independent MCP evidence actually backed that threat level before
authorizing action. That means an LLM's own assessment was, in effect,
the final safety authority.

This module is the deterministic checkpoint that fixes that: it only
reads structured fields (`adjusted_threat_level`, `evidence_classification`)
already produced by the Critic and applies fixed if/else rules -- it is
NOT itself an agent, has no prompt, and cannot be argued with by an LLM.
Because it's pure Python, its behavior is exhaustively testable and its
reasoning is always fully explainable (see `gate_reason` in the output).

DECISION RULES (in priority order):
1. evidence_classification == "contradicting"
     -> REQUIRES_REEVALUATION. Independent evidence conflicts with the
        Critic's assessment. We must not blindly execute the original
        threat response; the case needs to be re-run or reviewed rather
        than acted on as-is. This applies regardless of threat level,
        because a contradiction is itself a data-quality red flag.
2. threat_level in {HIGH, CRITICAL} AND evidence_classification in
   {"insufficient", "unavailable"}
     -> HUMAN_REVIEW_REQUIRED. This is the fail-closed rule: for
        genuinely high-stakes situations, the system refuses to let an
        LLM-authored action plan go out the door on visual/debate
        reasoning alone when the independent evidence channel could not
        confirm it. No autonomous action plan is generated.
3. evidence_classification == "supporting" (any threat level)
     -> AUTONOMOUS_ACTION_AUTHORIZED. Evidence backs the assessment;
        the Commander may generate the operational action plan.
4. Anything else (i.e. LOW/MEDIUM threat with insufficient/unavailable
   evidence)
     -> AUTONOMOUS_ACTION_AUTHORIZED, but the evidence gap is recorded
        in `gate_reason`. Fail-closed is reserved for high-stakes cases
        per the stated design goal -- it is not applied indiscriminately
        to low-stakes ones, which would just make the demo unusable
        without adding real safety value.

WHY NOT A NEW THREAT LEVEL:
The gate does not invent or alter LOW/MEDIUM/HIGH/CRITICAL. It produces
a SEPARATE `gate_decision` field alongside the existing threat level, so
downstream consumers keep both pieces of information distinct: "how bad
is it" (threat level, from Risk/Critic) vs. "are we allowed to act on
that autonomously" (gate_decision, from this module).
"""

from typing import Literal, TypedDict

HIGH_RISK_LEVELS = {"HIGH", "CRITICAL"}
VALID_EVIDENCE_CLASSIFICATIONS = {"supporting", "contradicting", "insufficient", "unavailable"}

GateDecision = Literal[
    "AUTONOMOUS_ACTION_AUTHORIZED",
    "REQUIRES_REEVALUATION",
    "HUMAN_REVIEW_REQUIRED",
]


class SafetyGateResult(TypedDict):
    gate_decision: GateDecision
    gate_reason: str
    threat_level_evaluated: str
    evidence_classification_evaluated: str
    commander_authorized: bool  # deterministic flag callers must check
    human_review_required: bool


def evaluate_safety_gate(critic_json: dict) -> SafetyGateResult:
    """
    Deterministically decide whether the Commander may generate an
    autonomous action plan, given the Critic's final output.

    Args:
        critic_json: dict conforming to (or approximating, on parse
                     fallback) the Critic's CriticReview schema. Must be
                     read defensively since it may be a safe_json_parse
                     fallback dict rather than a validated model.

    Returns:
        SafetyGateResult -- never raises; unknown/missing fields are
        treated as the least-trusted case (fail closed for high-stakes,
        i.e. missing evidence_classification is treated as "unavailable").
    """
    threat_level = critic_json.get("adjusted_threat_level", "STANDBY")

    evidence_classification = critic_json.get("evidence_classification", "unavailable")
    if evidence_classification not in VALID_EVIDENCE_CLASSIFICATIONS:
        # Defensive: an LLM parse fallback or malformed field must not be
        # silently treated as "supporting" -- fail closed on the label too.
        evidence_classification = "unavailable"

    is_high_risk = threat_level in HIGH_RISK_LEVELS

    if evidence_classification == "contradicting":
        decision: GateDecision = "REQUIRES_REEVALUATION"
        reason = (
            f"Independent MCP evidence CONTRADICTS the Critic's '{threat_level}' assessment. "
            "The original threat response cannot be blindly executed. Routing for "
            "re-evaluation/review instead of authorizing an autonomous action plan."
        )

    elif is_high_risk and evidence_classification in ("insufficient", "unavailable"):
        decision = "HUMAN_REVIEW_REQUIRED"
        reason = (
            f"Threat level is '{threat_level}' (high-stakes) but independent evidence is "
            f"'{evidence_classification}'. Fail-closed policy: autonomous action is refused "
            "for high-stakes situations without evidence sufficient to confirm the assessment. "
            "Routed to human review."
        )

    elif evidence_classification == "supporting":
        decision = "AUTONOMOUS_ACTION_AUTHORIZED"
        reason = (
            f"Independent MCP evidence SUPPORTS the '{threat_level}' assessment. "
            "Sufficient grounds exist to authorize the Commander's action plan."
        )

    else:
        # LOW/MEDIUM threat level with insufficient/unavailable evidence.
        # Not high-stakes, so the gate does not fail closed here.
        decision = "AUTONOMOUS_ACTION_AUTHORIZED"
        reason = (
            f"Threat level is '{threat_level}' (not high-stakes) with '{evidence_classification}' "
            "independent evidence. Gate permits autonomous action for non-critical threat levels "
            "even without confirming evidence; this evidence gap is logged for auditability."
        )

    return {
        "gate_decision": decision,
        "gate_reason": reason,
        "threat_level_evaluated": threat_level,
        "evidence_classification_evaluated": evidence_classification,
        "commander_authorized": decision == "AUTONOMOUS_ACTION_AUTHORIZED",
        "human_review_required": decision in ("HUMAN_REVIEW_REQUIRED", "REQUIRES_REEVALUATION"),
    }