"""
Supervisor agent for orchestrating multiple agents and workflows
"""
from app.core.llm import client
from typing import Dict, List
import json

SYSTEM_PROMPT = """
You are a strict supervisor agent coordinating customer support workflows.
Your responsibilities:
1. Review ticket analysis and plan
2. Choose the most appropriate workflow
3. Validate final outputs
4. Decide whether to approve, iterate or escalate

Available workflows:
- simple_auto_reply     → very simple, no tools needed
- rag_assisted          → needs knowledge base only
- tool_execution        → needs to call tools
- human_escalation      → should go to human

Return ONLY valid JSON:
{
  "workflow": "simple_auto_reply | rag_assisted | tool_execution | human_escalation",
  "reasoning": "short explanation why this workflow",
  "requires_iteration": false,
  "confidence": 0.0-1.0
}
"""

def supervise_workflow(ticket: str, analysis: dict, plan: dict = None) -> Dict:
    """
    Decide the best workflow route for this ticket.
    """
    prompt = f"""
Ticket: {ticket}

Analysis:
{json.dumps(analysis, indent=2)}

Plan (if available):
{json.dumps(plan, indent=2) if plan else "No plan provided"}

Choose the most appropriate workflow.
Be conservative: escalate when uncertain or high risk.
"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
            max_tokens=300
        )
        return json.loads(completion.choices[0].message.content)
    except Exception as e:
        return {
            "workflow": "human_escalation",
            "reasoning": f"Supervisor failed to decide due to error: {str(e)}",
            "requires_iteration": False,
            "confidence": 0.0
        }


def validate_and_reflect(
    original_ticket: str,
    response: str,
    evaluation: dict
) -> Dict:
    """
    Reflect on the final response quality and decide next step.
    """
    prompt = f"""
Review this final customer support interaction:

TICKET: {original_ticket}
RESPONSE: {response}
EVALUATION: {json.dumps(evaluation, indent=2)}

Strict approval criteria:
- overall_score >= 8.0
- guardrails passed = true
- no hallucinated facts
- empathetic tone present
- answer is complete and accurate

If ANY criterion fails → needs_iteration = true
Only approve if ALL criteria are clearly met.

Return ONLY JSON:
{{
  "needs_iteration": true/false,
  "reason": "one sentence explanation",
  "suggested_improvements": ["item1", "item2"] or [],
  "approve": true/false
}}
"""

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a strict quality supervisor. Return only JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.0,
            response_format={"type": "json_object"},
            max_tokens=250
        )
        result = json.loads(completion.choices[0].message.content)
        if "approve" not in result:
            result["approve"] = False
            result["needs_iteration"] = True
            result["reason"] = "Invalid reflection format → force iteration"
        return result
    except Exception:
        return {
            "needs_iteration": True,
            "reason": "Reflection LLM call failed",
            "suggested_improvements": [],
            "approve": False
        }


def should_escalate(
    ticket: str,
    analysis: dict,
    attempts: int = 0
) -> Dict:
    """
    Decide if the ticket should be escalated to human.
    """
    auto_escalate = False
    reasons = []

    if analysis.get("urgency") == "high" and analysis.get("sentiment") == "negative":
        auto_escalate = True
        reasons.append("High urgency + negative sentiment")

    if attempts >= 3:
        auto_escalate = True
        reasons.append("Reached maximum AI attempts")

    ticket_lower = ticket.lower()
    if analysis.get("category") == "billing":
        if any(word in ticket_lower for word in ["refund", "chargeback", "dispute", "reversal"]):
            reasons.append("Explicit refund request detected")
        elif "cancel" in ticket_lower or "subscription" in ticket_lower:
            reasons.append("Subscription/cancellation case — prefer tool or KB")

    return {
        "should_escalate": auto_escalate,
        "reason": " | ".join(reasons) if reasons else "No immediate escalation needed",
        "escalation_priority": analysis.get("urgency", "medium"),
        "suggested_queue": "billing" if analysis.get("category") == "billing" else "general"
    }