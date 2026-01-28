from app.core.llm import client
from app.agents.retriever import retrieve_context

SYSTEM_PROMPT = """
You are a support ticket analyzer with access to knowledge base context.

Analyze the ticket and relevant context to provide accurate categorization.

Return ONLY valid JSON.
No explanation. No markdown.

Schema:
{
  "category": "billing | technical | account | other",
  "urgency": "low | medium | high",
  "sentiment": "positive | neutral | negative",
  "key_issues": ["list of main issues"],
  "requires_tools": true/false,
  "confidence": 0.0-1.0
}
"""

def analyze_ticket(text: str, use_rag: bool = True) -> dict:
    """
    Analyze ticket with optional RAG context
    
    Args:
        text: Ticket content
        use_rag: Whether to use knowledge base retrieval
        
    Returns:
        JSON string with analysis
    """
    
    context = ""
    if use_rag:
        try:
            context = retrieve_context(text, top_k=2)
        except:
            context = ""
    
    prompt = f"{text}"
    if context:
        prompt = f"Context from knowledge base:\n{context}\n\nTicket:\n{text}"
    
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )

    return completion.choices[0].message.content
