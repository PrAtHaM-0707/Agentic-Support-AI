from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from sentence_transformers import SentenceTransformer
from typing import List, Dict
import uuid
import os
from dotenv import load_dotenv

load_dotenv()

# Read from environment, fallback to memory
qdrant_url = os.getenv("QDRANT_URL")
qdrant_api_key = os.getenv("QDRANT_API_KEY")

if qdrant_url and qdrant_api_key:
    client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
else:
    client = QdrantClient(":memory:")  # ":memory:" for local testing


encoder = SentenceTransformer("all-MiniLM-L6-v2")

COLLECTION_NAME = "knowledge_base"
VECTOR_SIZE = 384


def init_collection():
    """Initialize Qdrant collection if it doesn't exist"""
    try:
        client.get_collection(COLLECTION_NAME)
    except Exception:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=VECTOR_SIZE, distance=Distance.COSINE),
        )


def add_documents(documents: List[Dict[str, str]]):
    """
    Add documents to the vector database

    Args:
        documents: List of dicts with 'text' and optional 'metadata'

    Returns:
        Number of documents successfully added
    """
    init_collection()

    points = []
    for doc in documents:
        text = doc.get("text", "")
        metadata = doc.get("metadata", {})

        vector = encoder.encode(text).tolist()

        point = PointStruct(
            id=str(uuid.uuid4()), vector=vector, payload={"text": text, **metadata}
        )
        points.append(point)

    client.upsert(collection_name=COLLECTION_NAME, points=points)
    return len(points)


def search_knowledge_base(query: str, limit: int = 3) -> List[Dict]:
    """
    Search the knowledge base with semantic similarity

    Args:
        query: Search query text
        limit: Number of results to return

    Returns:
        List of relevant documents with scores and metadata
    """
    init_collection()

    query_vector = encoder.encode(query).tolist()

    search_result = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_vector,
        limit=limit,
        with_payload=True,
        with_vectors=False,
    )

    return [
        {
            "text": point.payload.get("text", ""),
            "score": point.score,
            "metadata": {k: v for k, v in point.payload.items() if k != "text"},
        }
        for point in search_result.points
    ]


def get_collection_stats():
    """Get statistics about the knowledge base"""
    try:
        init_collection()
        collection_info = client.get_collection(COLLECTION_NAME)
        return {
            "total_documents": collection_info.points_count,
            "vector_size": VECTOR_SIZE,
            "collection_name": COLLECTION_NAME,
        }
    except Exception:
        return {
            "total_documents": 0,
            "vector_size": VECTOR_SIZE,
            "collection_name": COLLECTION_NAME,
        }
