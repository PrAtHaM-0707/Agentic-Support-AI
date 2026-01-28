from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict
import json
from app.agents.analyzer import analyze_ticket
from app.agents.decision import decide_action
from app.agents.responder import generate_response, generate_with_tools
from app.agents.planner import plan_resolution, should_use_tools
from app.agents.retriever import retrieve_context
from app.agents.supervisor import supervise_workflow, validate_and_reflect, should_escalate
from app.core.evaluation import evaluate_response_quality, check_guardrails


class TicketState(TypedDict):
    content: str
    analysis: dict
    plan: dict
    supervisor_decision: dict
    action: str
    context: str
    response: str
    tools_used: list
    tool_results: list
    evaluation: dict
    reflection: dict
    iteration_count: int
    final_decision: str


def analyzer_node(state: TicketState):
    """First step: analyze ticket (with RAG if enabled)"""
    analysis_str = analyze_ticket(state["content"], use_rag=True)
    try:
        analysis = json.loads(analysis_str)
    except:
        analysis = {"category": "other", "error": "analysis parse failed"}
    return {"analysis": analysis, "iteration_count": state.get("iteration_count", 0)}


def planning_node(state: TicketState):
    """Create resolution plan"""
    plan = plan_resolution(state["content"], state["analysis"])
    return {"plan": plan}


def supervisor_node(state: TicketState):
    """Supervisor decides initial workflow"""
    decision = supervise_workflow(
        state["content"],
        state["analysis"],
        state.get("plan")
    )
    return {"supervisor_decision": decision}


def retrieval_node(state: TicketState):
    """Fetch relevant knowledge base context"""
    context = retrieve_context(state["content"], top_k=3)
    return {"context": context}


def decision_node(state: TicketState):
    """Decide action: escalate / use tools / auto-resolve"""
    escalation = should_escalate(
        state["content"],
        state["analysis"],
        state.get("iteration_count", 0)
    )

    if escalation.get("should_escalate"):
        return {"action": "escalate", "final_decision": "human_escalation"}

    plan = state.get("plan", {})
    if should_use_tools(plan):
        return {"action": "use_tools"}

    # Fallback to simple decision
    try:
        decision = json.loads(decide_action(state["analysis"]))
        return {"action": decision.get("action", "auto_resolve")}
    except:
        return {"action": "auto_resolve"}


def tool_execution_node(state: TicketState):
    """Run tools and generate response using tool results"""
    result = generate_with_tools(state["content"], state["analysis"])
    return {
        "response": result["response"],
        "tools_used": result["tools_used"],
        "tool_results": result["tool_results"]
    }


def responder_node(state: TicketState):
    """Generate response (when no tools needed)"""
    response = generate_response(
        state["content"],
        state["analysis"],
        state.get("tool_results"),
        state.get("context")
    )
    return {"response": response}


def evaluation_node(state: TicketState):
    """Evaluate quality + guardrails"""
    quality = evaluate_response_quality(
        state["content"],
        state["response"],
        state["analysis"]
    )
    guardrails = check_guardrails(state["response"], state["content"])

    evaluation = {
        "quality": quality,
        "guardrails": guardrails,
        "overall_pass": quality.get("passes", False) and guardrails.get("passed", False)
    }
    return {"evaluation": evaluation}


def reflection_node(state: TicketState):
    """Reflect → decide approve or iterate"""
    reflection = validate_and_reflect(
        state["content"],
        state["response"],
        state["evaluation"]
    )

    iteration_count = state.get("iteration_count", 0)

    if iteration_count >= 2:
        reflection["needs_iteration"] = False
        reflection["reason"] = "Maximum iterations reached (2)"
        reflection["approve"] = False  

    return {
        "reflection": reflection,
        "final_decision": "approve" if reflection.get("approve", False) else "iterate"
    }


def iteration_node(state: TicketState):
    """Prepare for next iteration: increment counter + re-analyze"""
    new_count = state.get("iteration_count", 0) + 1

    reason = state.get("reflection", {}).get("reason", "No reason provided")
    enhanced_content = f"{state['content']}\n\nPrevious attempt feedback: {reason}"

    analysis_str = analyze_ticket(enhanced_content, use_rag=True)
    try:
        analysis = json.loads(analysis_str)
    except:
        analysis = state["analysis"]  # fallback

    return {
        "iteration_count": new_count,
        "analysis": analysis
    }


graph = StateGraph(TicketState)

graph.add_node("analyze", analyzer_node)
graph.add_node("plan", planning_node)
graph.add_node("supervise", supervisor_node)
graph.add_node("retrieve", retrieval_node)
graph.add_node("decide", decision_node)
graph.add_node("execute_tools", tool_execution_node)
graph.add_node("respond", responder_node)
graph.add_node("evaluate", evaluation_node)
graph.add_node("reflect", reflection_node)
graph.add_node("iterate", iteration_node)

graph.set_entry_point("analyze")

graph.add_edge("analyze", "plan")
graph.add_edge("plan", "supervise")
graph.add_edge("supervise", "retrieve")
graph.add_edge("retrieve", "decide")

graph.add_conditional_edges(
    "decide",
    lambda s: s["action"],
    {
        "use_tools": "execute_tools",
        "auto_resolve": "respond",
        "escalate": END,
    }
)

graph.add_edge("execute_tools", "evaluate")
graph.add_edge("respond", "evaluate")

graph.add_edge("evaluate", "reflect")

graph.add_conditional_edges(
    "reflect",
    lambda s: s.get("final_decision", "iterate"),
    {
        "approve": END,
        "iterate": "iterate",
    }
)

graph.add_edge("iterate", "plan")

ticket_graph = graph.compile()