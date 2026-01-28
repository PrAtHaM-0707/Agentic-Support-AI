"""
Planning agent that breaks down complex tasks into steps
"""
from app.core.llm import client
from typing import List, Dict
import json

SYSTEM_PROMPT = """
You are a planning agent for customer support.

Given a ticket, create a step-by-step action plan to resolve it.

Return ONLY valid JSON with this structure:
{
  "requires_planning": true/false,
  "complexity": "simple | moderate | complex",
  "steps": [
    {
      "step": 1,
      "action": "search_knowledge | check_payment | create_refund | escalate | auto_respond",
      "description": "What to do in this step",
      "tool": "tool_name or null",
      "parameters": {}
    }
  ],
  "estimated_resolution": "immediate | hours | days"
}

For simple tickets (account questions, general info), set requires_planning=false.
For complex tickets (payment issues, bugs, refunds), create detailed steps.
"""


def plan_resolution(ticket_content: str, analysis: dict) -> dict:
    """
    Create a resolution plan based on ticket analysis
    
    Args:
        ticket_content: The original ticket text
        analysis: Analysis results (category, urgency, sentiment)
        
    Returns:
        Plan with steps to resolve the ticket
    """
    
    prompt = f"""
Ticket: {ticket_content}

Analysis:
- Category: {analysis.get('category')}
- Urgency: {analysis.get('urgency')}
- Sentiment: {analysis.get('sentiment')}

Create a resolution plan.
"""
    
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )
    
    plan = json.loads(completion.choices[0].message.content)
    return plan


def should_use_tools(plan: dict) -> bool:
    """Check if the plan requires tool usage"""
    if not plan.get("requires_planning"):
        return False
    
    steps = plan.get("steps", [])
    for step in steps:
        if step.get("tool"):
            return True
    
    return False


def get_next_step(plan: dict, completed_steps: List[int]) -> Dict | None:
    """
    Get the next step to execute from the plan
    
    Args:
        plan: The resolution plan
        completed_steps: List of completed step numbers
        
    Returns:
        Next step dict or None if all complete
    """
    steps = plan.get("steps", [])
    
    for step in steps:
        step_num = step.get("step")
        if step_num not in completed_steps:
            return step
    
    return None
