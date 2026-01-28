from app.core.llm import client

SYSTEM_PROMPT = """
You are a support decision agent.

Given ticket analysis, decide:
- action: auto_resolve or escalate

Return ONLY JSON:
{
  "action": "auto_resolve | escalate"
}
"""

def decide_action(analysis: dict) -> dict:
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": str(analysis)},
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    return completion.choices[0].message.content
