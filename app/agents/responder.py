from app.core.llm import client
from app.agents.retriever import retrieve_context
from app.core.tools import execute_tool
from app.core.logger import app_logger
import json

SYSTEM_PROMPT = """\
You are a customer support agent. You MUST ONLY use information from:\
1. The provided knowledge base articles\
2. The ACTUAL results returned by tools (if any)

Rules you MUST follow:\
- NEVER invent or assume payment status, refund success/failure, reasons, amounts, or outcomes.\
- If tool results do NOT confirm a specific claim (e.g. refund status, failure reason), do NOT state it.\
- If information is missing or unclear, say: "I'll need to check this further and will escalate if necessary."\
- Be empathetic, professional, concise (3-5 sentences max).\
- Acknowledge tool results explicitly when they exist.\
- Do NOT mention you are an AI, your limitations, or training data.\
- Match the customer's tone (empathetic for negative sentiment).\
"""


def generate_response(
    ticket_text: str,
    analysis: dict = None,
    tool_results: list = None,
    context: str = None,
) -> str:
    if context is None:
        try:
            context = retrieve_context(ticket_text, top_k=3)
        except Exception:
            context = ""

    prompt_parts = [f"Customer Ticket:\n{ticket_text}"]

    if context:
        prompt_parts.append(f"\nRelevant Knowledge Base:\n{context}")

    if analysis:
        prompt_parts.append(f"\nAnalysis:\n{json.dumps(analysis, indent=2)}")

    if tool_results:
        prompt_parts.append(
            f"\nTool Results (use ONLY this information):\n{json.dumps(tool_results, indent=2)}"
        )
    else:
        prompt_parts.append(
            "\nNo tools were used. Base your answer only on the ticket and knowledge base."
        )

    prompt = "\n".join(prompt_parts)

    app_logger.info("\n" + "-"*40 + "\n[LLM Request] Raw Prompt:\n" + prompt + "\n" + "-"*40)

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0.45,
        max_tokens=350,
    )
    
    response_text = completion.choices[0].message.content.strip()
    app_logger.info("\n" + "-"*40 + "\n[LLM Response] Raw Output:\n" + response_text + "\n" + "-"*40)
    
    return response_text


def generate_with_tools(ticket_text: str, analysis: dict) -> dict:
    tools_prompt = f"""
Ticket: {ticket_text}
Analysis: {json.dumps(analysis, indent=2)}

Available tools:
- search_knowledge: only if KB info is likely helpful
- check_payment_status: ONLY if transaction ID is mentioned
- create_refund: ONLY if customer explicitly requests refund AND payment status is confirmed
- escalate_to_human: if complex, high urgency, or multiple failed attempts
- check_account_status: if account/login issue is suspected

Decide carefully. Return ONLY JSON:
{{
  "needs_tools": true/false,
  "tools_to_use": [
    {{"tool": "tool_name", "args": {{"param1": "value1", ...}}}}
  ]
}}
Only include tools that are clearly necessary based on the ticket.
"""

    tool_decision = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {
                "role": "system",
                "content": "You are a careful tool selector. Return only valid JSON.",
            },
            {"role": "user", "content": tools_prompt},
        ],
        temperature=0.0,
        response_format={"type": "json_object"},
    )

    decision = json.loads(tool_decision.choices[0].message.content)

    tool_results = []
    if decision.get("needs_tools", False):
        for tool_call in decision.get("tools_to_use", []):
            tool_name = tool_call.get("tool")
            args = tool_call.get("args", {})
            result = execute_tool(tool_name, args)
            tool_results.append({"tool": tool_name, "result": result})

    response = generate_response(ticket_text, analysis, tool_results)

    return {
        "response": response,
        "tools_used": [t["tool"] for t in tool_results],
        "tool_results": tool_results,
    }
