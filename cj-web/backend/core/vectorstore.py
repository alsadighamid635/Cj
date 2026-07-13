"""
Thin wrapper around Qdrant Cloud (replaces local ChromaDB).
Three collections:
  cybersec_knowledge  — seeded Q&A from knowledge.json
  cybersec_sources    — articles scraped from RSS / web
  chat_memory         — past conversation turns (for context)

Embeddings: fastembed all-MiniLM-L6-v2 (ONNX runtime — ~100MB RAM vs
~400MB for sentence-transformers/PyTorch).
"""

import os
import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance, VectorParams, PointStruct,
    Filter, FieldCondition, MatchValue,
    FilterSelector,
)
from utils.logger import get_logger
import config

logger = get_logger()

# Vector dimension for all-MiniLM-L6-v2
VECTOR_DIM  = 384
DISTANCE    = Distance.COSINE

_client: QdrantClient | None = None


def _get_client() -> QdrantClient:
    global _client
    if _client is None:
        url = config.QDRANT_URL
        api_key = config.QDRANT_API_KEY
        if not url:
            raise RuntimeError("QDRANT_URL is not set.")
        _client = QdrantClient(url=url, api_key=api_key or None)
        logger.info("Qdrant client initialised → %s", url)
    return _client


def _ensure_collection(name: str):
    """Create collection if it doesn't exist."""
    client = _get_client()
    existing = {c.name for c in client.get_collections().collections}
    if name not in existing:
        client.create_collection(
            collection_name=name,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=DISTANCE),
        )
        logger.info("Created Qdrant collection '%s'", name)


# ── Embedding (fastembed — ONNX, low RAM) ────────────────────────────────────

_embedder = None

def _get_embedder():
    global _embedder
    if _embedder is None:
        from fastembed import TextEmbedding
        _embedder = TextEmbedding("sentence-transformers/all-MiniLM-L6-v2")
        logger.info("Embedding model loaded: all-MiniLM-L6-v2 (fastembed/ONNX)")
    return _embedder


def warm_up() -> None:
    """
    Pre-load the embedding model and Qdrant client at startup.
    Call this once during the FastAPI lifespan so the first user request
    is not delayed by model initialisation.
    """
    logger.info("Warming up embedding model...")
    _get_embedder()
    logger.info("Embedding model ready.")


def _embed(texts: list[str]) -> list[list[float]]:
    model = _get_embedder()
    embeddings = list(model.embed(texts))
    return [e.tolist() for e in embeddings]


# ── Stable ID helper ──────────────────────────────────────────────────────────

def _str_to_uuid(s: str) -> str:
    """Derive a deterministic UUID v5 from an arbitrary string ID."""
    return str(uuid.uuid5(uuid.NAMESPACE_DNS, s))


# ── Public helpers ────────────────────────────────────────────────────────────

def add_documents(collection_name: str, ids: list[str],
                  documents: list[str], metadatas: list[dict]):
    _ensure_collection(collection_name)
    client = _get_client()
    vectors = _embed(documents)
    batch = 100
    for i in range(0, len(ids), batch):
        points = [
            PointStruct(
                id=_str_to_uuid(ids[i + j]),
                vector=vectors[i + j],
                payload={**metadatas[i + j], "_orig_id": ids[i + j],
                         "_document": documents[i + j]},
            )
            for j in range(min(batch, len(ids) - i))
        ]
        client.upsert(collection_name=collection_name, points=points)
    logger.debug("Upserted %d docs into '%s'", len(ids), collection_name)


def search(collection_name: str, query: str,
           n: int = config.MAX_RESULTS) -> list[dict]:
    _ensure_collection(collection_name)
    client = _get_client()
    total = count(collection_name)
    if total == 0:
        return []
    query_vec = _embed([query])[0]
    response = client.query_points(
        collection_name=collection_name,
        query=query_vec,
        limit=min(n, total),
        with_payload=True,
    )
    hits = []
    for r in response.points:
        payload  = dict(r.payload or {})
        document = payload.pop("_document", "")
        payload.pop("_orig_id", None)
        # Qdrant score is cosine similarity (1=identical); convert to distance
        hits.append({
            "document": document,
            "metadata": payload,
            "distance": 1.0 - r.score,   # cosine distance compatible with old API
        })
    return hits


def search_all(query: str, n: int = config.MAX_RESULTS) -> list[dict]:
    """Search knowledge + sources + chat_memory and merge by distance."""
    hits = []
    for col in (config.COLLECTION_KNOWLEDGE, config.COLLECTION_SOURCES,
                config.COLLECTION_CHAT):
        hits.extend(search(col, query, n))
    hits.sort(key=lambda h: h["distance"])
    return hits[:n]


def count(collection_name: str) -> int:
    _ensure_collection(collection_name)
    info = _get_client().get_collection(collection_name)
    return info.points_count or 0


def total_knowledge() -> int:
    return sum(count(c) for c in (
        config.COLLECTION_KNOWLEDGE, config.COLLECTION_SOURCES
    ))


def delete_by_source(source_id: int):
    """Remove all scraped documents belonging to a source."""
    client = _get_client()
    _ensure_collection(config.COLLECTION_SOURCES)
    client.delete(
        collection_name=config.COLLECTION_SOURCES,
        points_selector=FilterSelector(
            filter=Filter(
                must=[FieldCondition(key="source_id",
                                     match=MatchValue(value=source_id))]
            )
        ),
    )
    logger.info("Deleted docs for source_id=%d from Qdrant", source_id)
