from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router as auth_router
from app.api.tickets import router as ticket_router
from app.core.init_kb import initialize_knowledge_base
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize resources on startup"""
    print("🚀 Starting Agentic Support AI...")
    
    # Initialize knowledge base with support documents
    print("📚 Initializing knowledge base...")
    initialize_knowledge_base()
    
    print("✅ System ready!")
    yield
    
    # Cleanup on shutdown
    print("👋 Shutting down...")

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
    lifespan=lifespan
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

@app.get("/")
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
            "guardrails"
        ]
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
            "evaluator"
        ],
        "features": {
            "rag": True,
            "tool_calling": True,
            "planning": True,
            "self_correction": True,
            "evaluation": True,
            "guardrails": True,
            "async_processing": True,
            "langchain_integration": True
        }
    }
