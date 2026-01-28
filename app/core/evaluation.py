"""
Evaluation and guardrails for agent responses
"""
from app.core.llm import client
from typing import Dict, List
import json
import re

def evaluate_response_quality(
    ticket: str,
    response: str,
    analysis: dict
) -> Dict:
    prompt = f"""
Evaluate this customer support response carefully:
TICKET: {ticket}
RESPONSE: {response}
CATEGORY: {analysis.get('category')}

Rate each on 1-10:
- relevance: fully addresses the ticket?
- helpfulness: gives clear, actionable next steps?
- tone: empathetic, professional, matches sentiment?
- completeness: covers all key concerns?
- factual_accuracy: no invented facts or unsupported claims?

Return JSON only:
{{
  "relevance": 8,
  "helpfulness": 7,
  "tone": 9,
  "completeness": 8,
  "factual_accuracy": 6,
  "overall_score": 7.6,
  "passes": true,
  "issues": ["any problems found"]
}}
"""

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a strict quality evaluator. Return only JSON."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.0,
        response_format={"type": "json_object"}
    )

    eval_result = json.loads(completion.choices[0].message.content)

    # Raised threshold to 7.5 for stricter approval
    eval_result["passes"] = eval_result.get("overall_score", 0) >= 7.5

    return eval_result


def check_guardrails(response: str, ticket: str) -> Dict:
    issues = []

    response_lower = response.lower()

    prohibited_terms = [
        "guarantee", "promise", "definitely will", "100%", "for sure",
        "sue", "legal action", "lawyer", "court", "compensation"
    ]
    for term in prohibited_terms:
        if term in response_lower:
            issues.append(f"Prohibited term: '{term}'")

    hallucination_markers = [
        "failed due to", "insufficient funds", "card declined", "bank issue",
        "refund failed", "refund unsuccessful", "could not process", "technical issue",
        "appears that", "it seems", "likely", "probably", "I believe"
    ]
    for marker in hallucination_markers:
        if marker in response_lower:
            issues.append(f"Potential hallucination: '{marker}'")

    if re.search(r'\b\d{3}-\d{2}-\d{4}\b', response):
        issues.append("Possible SSN pattern")
    if re.search(r'\b\d{16}\b|\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b', response):
        issues.append("Possible credit card pattern")

    if len(response) < 40:
        issues.append("Response too short")
    if len(response) > 1200:
        issues.append("Response too long")

    empathy_words = ["sorry", "apologize", "understand", "help", "appreciate", "frustrating", "inconvenience"]
    has_empathy = any(word in response_lower for word in empathy_words)
    if not has_empathy and "negative" in str(ticket).lower():
        issues.append("Lacks empathy for negative sentiment")

    ai_disclosure = [
        "as an ai", "i'm not human", "i don't have access", "i cannot access",
        "as a language model", "according to my training"
    ]
    for phrase in ai_disclosure:
        if phrase in response_lower:
            issues.append(f"AI disclosure: '{phrase}'")

    return {
        "passed": len(issues) == 0,
        "issues": issues,
        "checks_performed": [
            "prohibited_terms", "hallucination_markers", "pii_leakage",
            "length_limits", "empathy_check", "ai_disclosure"
        ]
    }


def validate_tool_usage(tool_name: str, arguments: dict) -> Dict:
    issues = []
    valid_tools = [
        "search_knowledge", "check_payment_status", "create_refund",
        "escalate_to_human", "check_account_status"
    ]
    if tool_name not in valid_tools:
        issues.append(f"Invalid tool: {tool_name}")

    required_params = {
        "check_payment_status": ["transaction_id"],
        "create_refund": ["transaction_id", "reason"],
        "escalate_to_human": ["reason"],
        "check_account_status": ["user_email"],
        "search_knowledge": ["query"]
    }

    if tool_name in required_params:
        for param in required_params[tool_name]:
            if param not in arguments:
                issues.append(f"Missing required parameter: {param}")

    return {"valid": len(issues) == 0, "issues": issues}


def evaluation(
    ticket: str,
    response: str,
    analysis: dict,
    tools_used: List[str] = None
) -> Dict:
    quality = evaluate_response_quality(ticket, response, analysis)
    guardrails = check_guardrails(response, ticket)

    overall_pass = quality.get("passes", False) and guardrails.get("passed", False)

    return {
        "overall_pass": overall_pass,
        "quality_metrics": quality,
        "guardrail_checks": guardrails,
        "tools_used": tools_used or [],
        "recommendation": "approve" if overall_pass else "needs_revision"
    }