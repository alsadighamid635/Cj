"""
Seeds Qdrant with the Q&A knowledge base from cj-ai/knowledge/knowledge.json.
Called once at startup; skips silently if the collection is already populated.
"""

import json
from pathlib import Path
from core import vectorstore
from utils.logger import get_logger
import config

logger = get_logger()


def seed_knowledge(path: Path = config.KNOWLEDGE_FILE):
    if vectorstore.count(config.COLLECTION_KNOWLEDGE) > 0:
        logger.info("Knowledge collection already seeded (%d docs).",
                    vectorstore.count(config.COLLECTION_KNOWLEDGE))
        return

    if not path.exists():
        logger.warning("Knowledge file not found: %s — skipping seed.", path)
        return

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    entries = data.get("entries", [])
    ids, docs, metas = [], [], []

    for entry in entries:
        entry_id = f"qa_{entry['id']}"
        question = entry.get("question", "")
        answer   = entry.get("answer", "")
        tags     = entry.get("tags", [])

        # Index both question and a short combined version so search finds both
        ids.append(entry_id)
        docs.append(f"{question}\n{answer[:300]}")
        metas.append({
            "type":     "qa",
            "question": question,
            "answer":   answer,
            "tags":     ",".join(tags),
            "source":   "knowledge_base",
        })

    vectorstore.add_documents(config.COLLECTION_KNOWLEDGE, ids, docs, metas)
    logger.info("Seeded %d Q&A entries into Qdrant.", len(ids))
