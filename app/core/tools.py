"""
Tool definitions for agent function calling
"""

from typing import List, Dict, Any
import json
from app.core.qdrant_client import search_knowledge_base

# Global registry of tool definitions
TOOLS = []


def tool(description: str):
    """Decorator to register tools and auto-generate OpenAI-style tool schema"""

    def decorator(func):
        tool_def = {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": description,
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        }

        import inspect

        sig = inspect.signature(func)
        for param_name, param in sig.parameters.items():
            if param_name != "self":
                tool_def["function"]["parameters"]["properties"][param_name] = {
                    "type": "string",
                    "description": f"The {param_name} parameter",
                }
                if param.default == inspect.Parameter.empty:
                    tool_def["function"]["parameters"]["required"].append(param_name)

        TOOLS.append(tool_def)
        func._tool_definition = tool_def
        return func

    return decorator


@tool("Search the knowledge base for relevant support documentation and FAQs")
def search_knowledge(query: str) -> str:
    """Search knowledge base with semantic similarity"""
    results = search_knowledge_base(query, limit=3)

    if not results:
        return "No relevant information found in knowledge base."

    context = "Found relevant information:\n\n"
    for i, result in enumerate(results, 1):
        context += f"{i}. {result['text']} (relevance: {result['score']:.2f})\n\n"

    return context


@tool("Check if a payment transaction exists and its status")
def check_payment_status(transaction_id: str) -> str:
    """
    Mock payment status check.
    For testing: if transaction_id starts with 'TXN-', always returns duplicate charge.
    """
    if transaction_id.startswith("TXN-"):
        status = "duplicate"
    else:
        import random

        statuses = ["pending", "completed", "failed", "duplicate"]
        status = random.choice(statuses)

    messages = {
        "pending": "Payment is still being processed by the bank.",
        "completed": "Payment completed successfully.",
        "failed": "Payment failed — please update your payment method and try again.",
        "duplicate": "A duplicate charge has been detected. This is often a temporary authorization hold and should disappear within 3-5 business days. If it persists, contact support to request a refund.",
    }

    return json.dumps(
        {
            "transaction_id": transaction_id,
            "status": status,
            "message": messages.get(status, "Unknown status"),
            "amount": 99.99,
            "timestamp": "2026-01-28T10:30:00Z",
        }
    )


@tool("Create a refund request for a transaction")
def create_refund(transaction_id: str, reason: str) -> str:
    """Mock function to create refund (replace with real payment gateway API call)"""
    return json.dumps(
        {
            "refund_id": f"REF-{transaction_id}",
            "status": "initiated",
            "message": "Refund request successfully created. Expected processing time: 3-5 business days.",
            "reason": reason,
            "transaction_id": transaction_id,
        }
    )


@tool("Escalate ticket to human agent")
def escalate_to_human(reason: str, priority: str = "medium") -> str:
    """Escalate ticket to human support team"""
    return json.dumps(
        {
            "escalated": True,
            "priority": priority,
            "reason": reason,
            "estimated_response_time": "2-4 hours",
            "ticket_queue": "human_review",
        }
    )


@tool("Check user account status and details")
def check_account_status(user_email: str) -> str:
    """Mock function to check account details"""
    return json.dumps(
        {
            "email": user_email,
            "account_status": "active",
            "subscription_tier": "premium",
            "member_since": "2024-06-15",
            "support_tier": "priority",
        }
    )


def execute_tool(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Execute a registered tool by name with given arguments"""
    tool_map = {
        "search_knowledge": search_knowledge,
        "check_payment_status": check_payment_status,
        "create_refund": create_refund,
        "escalate_to_human": escalate_to_human,
        "check_account_status": check_account_status,
    }

    if tool_name not in tool_map:
        return f"Error: Tool '{tool_name}' not found"

    try:
        result = tool_map[tool_name](**arguments)
        return result
    except Exception as e:
        return f"Error executing tool '{tool_name}': {str(e)}"


def get_tool_definitions() -> List[Dict]:
    """Return list of all registered tool schemas for LLM function calling"""
    return TOOLS
