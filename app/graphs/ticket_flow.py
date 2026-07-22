from langgraph.graph import StateGraph, END
from typing import TypedDict
import json
import time
from app.agents.analyzer import analyze_ticket
from app.agents.decision import decide_action
from app.agents.responder import generate_response, generate_with_tools
from app.agents.planner import plan_resolution, should_use_tools
from app.agents.retriever import retrieve_context
from app.agents.supervisor import (
    supervise_workflow,
    validate_and_reflect,
    should_escalate,
)
from app.core.evaluation import evaluate_response_quality, check_guardrails
from app.core.logger import app_logger


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
    start_time = time.time()
    app_logger.info("🤖 [Node: Analyzer] Analyzing sentiment, urgency, and category...")
    analysis_str = analyze_ticket(state["content"], use_rag=True)
    try:
        analysis = json.loads(analysis_str)
        app_logger.info(f"   -> Result: Category={analysis.get('category')}, Urgency={analysis.get('urgency')}, Sentiment={analysis.get('sentiment')}")
    except Exception:
        analysis = {"category": "other", "error": "analysis parse failed"}
    app_logger.info(f"   -> ⏱️ Analyzer completed in {time.time() - start_time:.2f}s")
    return {"analysis": analysis, "iteration_count": state.get("iteration_count", 0)}


def planning_node(state: TicketState):
    """Create resolution plan"""
    start_time = time.time()
    app_logger.info("🤖 [Node: Planner] Formulating a resolution strategy...")
    plan = plan_resolution(state["content"], state["analysis"])
    app_logger.info(f"   -> Strategy created (Complexity: {plan.get('complexity')})")
    app_logger.info(f"   -> ⏱️ Planner completed in {time.time() - start_time:.2f}s")
    return {"plan": plan}


def supervisor_node(state: TicketState):
    """Supervisor decides initial workflow"""
    start_time = time.time()
    app_logger.info("🤖 [Node: Supervisor] Reviewing plan and delegating tasks...")
    decision = supervise_workflow(
        state["content"], state["analysis"], state.get("plan")
    )
    app_logger.info(f"   -> ⏱️ Supervisor completed in {time.time() - start_time:.2f}s")
    return {"supervisor_decision": decision}


def retrieval_node(state: TicketState):
    """Fetch relevant knowledge base context"""
    start_time = time.time()
    app_logger.info("🤖 [Node: Retriever] Searching Qdrant Vector Database for knowledge...")
    context = retrieve_context(state["content"], top_k=3)
    app_logger.info(f"   -> ⏱️ Retriever completed in {time.time() - start_time:.2f}s")
    return {"context": context}


def decision_node(state: TicketState):
    """Decide action: escalate / use tools / auto-resolve"""
    start_time = time.time()
    app_logger.info("🤖 [Node: Decision] Deciding next action...")
    escalation = should_escalate(
        state["content"], state["analysis"], state.get("iteration_count", 0)
    )

    if escalation.get("should_escalate"):
        app_logger.info("   -> Decision: ESCALATE TO HUMAN")
        app_logger.info(f"   -> ⏱️ Decision completed in {time.time() - start_time:.2f}s")
        return {"action": "escalate", "final_decision": "human_escalation"}

    plan = state.get("plan", {})
    if should_use_tools(plan):
        app_logger.info("   -> Decision: EXECUTE TOOLS")
        app_logger.info(f"   -> ⏱️ Decision completed in {time.time() - start_time:.2f}s")
        return {"action": "use_tools"}

    # Fallback to simple decision
    try:
        decision = json.loads(decide_action(state["analysis"]))
        action = decision.get("action", "auto_resolve")
        app_logger.info(f"   -> Decision: {action.upper()}")
        app_logger.info(f"   -> ⏱️ Decision completed in {time.time() - start_time:.2f}s")
        return {"action": action}
    except Exception:
        app_logger.info("   -> Decision: AUTO RESOLVE")
        app_logger.info(f"   -> ⏱️ Decision completed in {time.time() - start_time:.2f}s")
        return {"action": "auto_resolve"}


def tool_execution_node(state: TicketState):
    """Run tools and generate response using tool results"""
    start_time = time.time()
    app_logger.info("🤖 [Node: Tool Execution] Calling necessary external APIs...")
    result = generate_with_tools(state["content"], state["analysis"])
    app_logger.info(f"   -> Tools used: {result['tools_used']}")
    app_logger.info(f"   -> ⏱️ Tool Execution completed in {time.time() - start_time:.2f}s")
    return {
        "response": result["response"],
        "tools_used": result["tools_used"],
        "tool_results": result["tool_results"],
    }


def responder_node(state: TicketState):
    """Generate response (when no tools needed)"""
    start_time = time.time()
    app_logger.info("🤖 [Node: Responder] Drafting customer response...")
    response = generate_response(
        state["content"],
        state["analysis"],
        state.get("tool_results"),
        state.get("context"),
    )
    app_logger.info("   -> Response drafted successfully.")
    app_logger.info(f"   -> ⏱️ Responder completed in {time.time() - start_time:.2f}s")
    return {"response": response}


def evaluation_node(state: TicketState):
    """Evaluate quality + guardrails"""
    start_time = time.time()
    app_logger.info("🤖 [Node: Evaluator] Checking quality and guardrails...")
    quality = evaluate_response_quality(
        state["content"], state["response"], state["analysis"]
    )
    guardrails = check_guardrails(state["response"], state["content"])

    evaluation = {
        "quality": quality,
        "guardrails": guardrails,
        "overall_pass": quality.get("passes", False)
        and guardrails.get("passed", False),
    }
    app_logger.info(f"   -> Passed Quality: {quality.get('passes', False)}, Passed Guardrails: {guardrails.get('passed', False)}")
    app_logger.info(f"   -> ⏱️ Evaluator completed in {time.time() - start_time:.2f}s")
    return {"evaluation": evaluation}


def reflection_node(state: TicketState):
    """Reflect → decide approve or iterate"""
    start_time = time.time()
    app_logger.info("🤖 [Node: Reflection] Reviewing evaluation results...")
    reflection = validate_and_reflect(
        state["content"], state["response"], state["evaluation"]
    )

    iteration_count = state.get("iteration_count", 0)

    if iteration_count >= 2:
        reflection["needs_iteration"] = False
        reflection["reason"] = "Maximum iterations reached (2)"
        reflection["approve"] = False

    final_decision = "approve" if reflection.get("approve", False) else "iterate"
    app_logger.info(f"   -> Reflection Decision: {final_decision.upper()}")
    app_logger.info(f"   -> ⏱️ Reflection completed in {time.time() - start_time:.2f}s")
    
    return {
        "reflection": reflection,
        "final_decision": final_decision,
    }


def iteration_node(state: TicketState):
    """Prepare for next iteration: increment counter + re-analyze"""
    start_time = time.time()
    new_count = state.get("iteration_count", 0) + 1
    app_logger.info(f"🤖 [Node: Iteration] Triggering iteration #{new_count} to fix response...")

    reason = state.get("reflection", {}).get("reason", "No reason provided")
    enhanced_content = f"{state['content']}\n\nPrevious attempt feedback: {reason}"

    analysis_str = analyze_ticket(enhanced_content, use_rag=True)
    try:
        analysis = json.loads(analysis_str)
    except Exception:
        analysis = state["analysis"]  # fallback

    app_logger.info(f"   -> ⏱️ Iteration completed in {time.time() - start_time:.2f}s")
    return {"iteration_count": new_count, "analysis": analysis}


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
    },
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
    },
)

graph.add_edge("iterate", "plan")

ticket_graph = graph.compile()
