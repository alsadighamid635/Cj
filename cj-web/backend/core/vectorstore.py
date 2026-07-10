"""
Thin wrapper around ChromaDB.
Three collections:
  cybersec_knowledge  — seeded Q&A from knowledge.json
  cybersec_sources    — articles scraped from RSS / web
  chat_memory         — past conversation turns (for context)
"""

import chromadb
from chromadb.utils.embedding_functions import DefaultEmbeddingFunction
from pathlib import Path
from utils.logger import get_logger
import config

logger = get_logger()
_client: chromadb.ClientAPI | None = None
_ef = DefaultEmbeddingFunction()


def _get_client() -> chromadb.ClientAPI:
    global _client
    if _client is None:
        config.CHROMA_DIR.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(config.CHROMA_DIR))
        logger.info("ChromaDB initialised at %s", config.CHROMA_DIR)
    return _client


def _col(name: str):
    return _get_client().get_or_create_collection(
        name=name,
        embedding_function=_ef,
        metadata={"hnsw:space": "cosine"},
    )


# ── Public helpers ────────────────────────────────────────────────────────────

def add_documents(collection_name: str, ids: list[str],
                  documents: list[str], metadatas: list[dict]):
    col = _col(collection_name)
    # Upsert in batches of 100 to stay within ChromaDB limits
    batch = 100
    for i in range(0, len(ids), batch):
        col.upsert(
            ids=ids[i:i+batch],
            documents=documents[i:i+batch],
            metadatas=metadatas[i:i+batch],
        )
    logger.debug("Upserted %d docs into '%s'", len(ids), collection_name)


def search(collection_name: str, query: str,
           n: int = config.MAX_RESULTS) -> list[dict]:
    col = _col(collection_name)
    if col.count() == 0:
        return []
    results = col.query(
        query_texts=[query],
        n_results=min(n, col.count()),
        include=["documents", "metadatas", "distances"],
    )
    hits = []
    for doc, meta, dist in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        hits.append({"document": doc, "metadata": meta, "distance": dist})
    return hits


def search_all(query: str, n: int = config.MAX_RESULTS) -> list[dict]:
    """Search knowledge + sources + chat_memory and merge by distance."""
    hits = []
    for col in (config.COLLECTION_KNOWLEDGE, config.COLLECTION_SOURCES, config.COLLECTION_CHAT):
        hits.extend(search(col, query, n))
    hits.sort(key=lambda h: h["distance"])
    return hits[:n]


def count(collection_name: str) -> int:
    return _col(collection_name).count()


def total_knowledge() -> int:
    return sum(count(c) for c in (
        config.COLLECTION_KNOWLEDGE, config.COLLECTION_SOURCES
    ))


def delete_by_source(source_id: int):
    """Remove all scraped documents belonging to a source."""
    col = _col(config.COLLECTION_SOURCES)
    results = col.get(where={"source_id": source_id})
    if results["ids"]:
        col.delete(ids=results["ids"])
        logger.info("Deleted %d docs for source_id=%d", len(results["ids"]), source_id)
