from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.deps import get_db
from app.models.ticket import Ticket
from app.schemas.ticket import TicketCreate
from app.core.deps import get_current_user
from app.graphs.ticket_flow import ticket_graph
from app.core.logger import app_logger

router = APIRouter(prefix="/tickets", tags=["tickets"])


async def process_ticket_async(ticket_id: int, content: str, db: Session):
    """Background task to process ticket asynchronously"""
    try:
        result = ticket_graph.invoke({"content": content})
        
        ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
        if ticket:
            analysis = result.get("analysis", {})
            evaluation = result.get("evaluation", {})
            
            ticket.category = analysis.get("category")
            ticket.priority = analysis.get("urgency")
            ticket.sentiment = analysis.get("sentiment")
            
            if evaluation and "quality" in evaluation:
                quality = evaluation["quality"]
                ticket.ai_confidence = int(quality.get("overall_score", 0) * 10)
            
            db.commit()
    except Exception as e:
        app_logger.error(f"Error processing ticket {ticket_id}: {e}")


@router.post("/")
async def create_ticket(
    data: TicketCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Create and process a support ticket with advanced agentic workflow
    
    Features:
    - Multi-agent orchestration with LangGraph
    - RAG-based context retrieval
    - Tool execution (payment checks, refunds, etc.)
    - Planning and self-correction
    - Quality evaluation and guardrails
    - Async processing for better performance
    """
    
    ticket = Ticket(
        user_id=current_user.id,
        content=data.content,
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)
    
    background_tasks.add_task(
        process_ticket_async,
        ticket.id,
        data.content,
        db
    )
    
    result = ticket_graph.invoke({"content": data.content})
    
    analysis = result.get("analysis", {})
    action = result.get("action")
    response = result.get("response")
    plan = result.get("plan", {})
    tools_used = result.get("tools_used", [])
    evaluation = result.get("evaluation", {})
    
    ticket.category = analysis.get("category")
    ticket.priority = analysis.get("urgency")
    ticket.sentiment = analysis.get("sentiment")
    
    if evaluation and "quality" in evaluation:
        quality = evaluation["quality"]
        ticket.ai_confidence = int(quality.get("overall_score", 0) * 10)
    
    db.commit()
    
    return {
        "id": ticket.id,
        "content": ticket.content,
        "analysis": analysis,
        "plan": {
            "complexity": plan.get("complexity"),
            "steps_count": len(plan.get("steps", [])),
            "estimated_resolution": plan.get("estimated_resolution")
        },
        "action": action,
        "response": response,
        "tools_used": tools_used,
        "evaluation": {
            "quality_score": evaluation.get("quality", {}).get("overall_score"),
            "guardrails_passed": evaluation.get("guardrails", {}).get("passed"),
            "iteration_count": result.get("iteration_count", 0)
        },
        "metadata": {
            "category": ticket.category,
            "priority": ticket.priority,
            "sentiment": ticket.sentiment,
            "ai_confidence": ticket.ai_confidence
        }
    }


@router.get("/me")
def my_profile(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "role": current_user.role,
    }


@router.get("/{ticket_id}")
def get_ticket(
    ticket_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get ticket details"""
    ticket = db.query(Ticket).filter(
        Ticket.id == ticket_id,
        Ticket.user_id == current_user.id
    ).first()
    
    if not ticket:
        return {"error": "Ticket not found"}
    
    return {
        "id": ticket.id,
        "content": ticket.content,
        "category": ticket.category,
        "priority": ticket.priority,
        "sentiment": ticket.sentiment,
        "ai_confidence": ticket.ai_confidence,
        "created_at": ticket.created_at
    }
