from app.core.qdrant_client import search_knowledge_base
from typing import List, Dict


def retrieve_context(query: str, top_k: int = 3) -> str:
    """
    Retrieve relevant context from knowledge base using semantic search
    
    Args:
        query: User query or ticket content
        top_k: Number of relevant documents to retrieve
        
    Returns:
        Formatted context string with relevant information
    """
    results = search_knowledge_base(query, limit=top_k)
    
    if not results:
        return "No relevant information found in knowledge base."
    
    context = "### Relevant Knowledge Base Information:\n\n"
    
    for i, result in enumerate(results, 1):
        score = result.get('score', 0)
        text = result.get('text', '')
        metadata = result.get('metadata', {})
        
        if score > 0.3:
            context += f"{i}. {text}\n"
            if metadata:
                context += f"   (Category: {metadata.get('category', 'general')})\n"
            context += "\n"
    
    return context.strip()


def get_relevant_docs(query: str) -> List[Dict]:
    """
    Get raw relevant documents without formatting
    
    Args:
        query: Search query
        
    Returns:
        List of document dictionaries with text, score, and metadata
    """
    return search_knowledge_base(query, limit=3)
