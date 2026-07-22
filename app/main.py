from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
from app.api.auth import router as auth_router
from app.api.tickets import router as ticket_router
from app.core.init_kb import initialize_knowledge_base
from contextlib import asynccontextmanager
from app.core.logger import app_logger
from app.db.session import engine, Base
import threading


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup"""
    app_logger.info("🚀 Starting Agentic Support AI...")

    app_logger.info("🗄️ Initializing database tables...")
    Base.metadata.create_all(bind=engine)

    # Initialize knowledge base with support documents
    app_logger.info("📚 Initializing knowledge base...")
    initialize_knowledge_base()

    # Preload ML model to prevent cold-starts on first request
    app_logger.info("🧠 Spawning background thread to warmup AI Model...")
    from app.core.qdrant_client import get_encoder
    threading.Thread(target=get_encoder, daemon=True).start()

    app_logger.info("✅ System ready!")
    yield

    # Cleanup on shutdown
    app_logger.info("👋 Shutting down...")


app = FastAPI(
    title="Agentic Support AI",
    description="""
    Advanced AI-powered customer support system with:
    - Multi-agent orchestration using LangGraph
    - RAG with Qdrant vector database
    - Tool execution (payment checks, refunds, escalations)
    - Planning and self-correction capabilities
    - Quality evaluation and guardrails
    - LangChain integration for memory and chains
    """,
    version="2.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(ticket_router)

# Mount static files directory
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
async def serve_frontend():
    return FileResponse("static/index.html")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "version": "2.0.0",
        "features": [
            "multi_agent_orchestration",
            "rag_retrieval",
            "tool_execution",
            "planning",
            "self_correction",
            "evaluation_pipeline",
            "guardrails",
        ],
    }


@app.get("/system/info")
def system_info():
    """Get system capabilities and statistics"""
    from app.core.qdrant_client import get_collection_stats
    from app.core.tools import get_tool_definitions

    kb_stats = get_collection_stats()
    tools = get_tool_definitions()

    return {
        "knowledge_base": kb_stats,
        "available_tools": [t["function"]["name"] for t in tools],
        "agents": [
            "analyzer",
            "planner",
            "retriever",
            "decision",
            "responder",
            "supervisor",
            "evaluator",
        ],
        "features": {
            "rag": True,
            "tool_calling": True,
            "planning": True,
            "self_correction": True,
            "evaluation": True,
            "guardrails": True,
            "async_processing": True,
            "langchain_integration": True,
        },
    }
