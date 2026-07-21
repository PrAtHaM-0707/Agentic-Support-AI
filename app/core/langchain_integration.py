"""
LangChain integration for conversation memory and chains
"""

from typing import Dict, List


class TicketMemoryManager:
    """Manage conversation history for tickets using simple in-memory storage"""

    def __init__(self):
        self.memories = {}

    def get_memory(self, ticket_id: int) -> List[Dict]:
        """Get or create memory for a ticket"""
        if ticket_id not in self.memories:
            self.memories[ticket_id] = []
        return self.memories[ticket_id]

    def add_exchange(self, ticket_id: int, user_message: str, ai_response: str):
        """Add a conversation exchange to memory"""
        memory = self.get_memory(ticket_id)
        memory.append({"role": "user", "content": user_message, "timestamp": None})
        memory.append({"role": "assistant", "content": ai_response, "timestamp": None})

    def get_history(self, ticket_id: int) -> List[Dict]:
        """Get conversation history for a ticket"""
        return self.get_memory(ticket_id)

    def clear_memory(self, ticket_id: int):
        """Clear memory for a ticket"""
        if ticket_id in self.memories:
            self.memories[ticket_id] = []


# Global memory manager
memory_manager = TicketMemoryManager()


def get_ticket_memory(ticket_id: int) -> List[Dict]:
    """Get memory for a specific ticket"""
    return memory_manager.get_memory(ticket_id)


def save_ticket_exchange(ticket_id: int, user_msg: str, ai_msg: str):
    """Save a conversation exchange"""
    memory_manager.add_exchange(ticket_id, user_msg, ai_msg)


def get_conversation_context(ticket_id: int) -> str:
    """Get formatted conversation history"""
    history = memory_manager.get_history(ticket_id)

    if not history:
        return "No previous conversation."

    context = "Previous conversation:\n"
    for msg in history:
        role = "User" if msg["role"] == "user" else "Agent"
        context += f"{role}: {msg['content']}\n"

    return context


def create_contextual_response(
    ticket_id: int, user_input: str, kb_context: str = ""
) -> str:
    """
    Create response with conversation memory

    This uses our custom memory manager instead of LangChain
    """

    conversation_context = get_conversation_context(ticket_id)

    context = f"Knowledge Base Context:\n{kb_context}" if kb_context else ""

    prompt = f"""
You are a helpful customer support agent with access to knowledge base.

{context}

{conversation_context}

Customer: {user_input}

Provide a helpful, empathetic response based on the context and conversation history.
Agent:"""

    from app.core.llm import client

    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a helpful customer support agent."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    response = completion.choices[0].message.content

    save_ticket_exchange(ticket_id, user_input, response)

    return response
