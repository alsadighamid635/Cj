import json
from pathlib import Path
from dataclasses import dataclass, field
from utils.logger import get_logger

logger = get_logger()


@dataclass
class KnowledgeEntry:
    id: int
    question: str
    answer: str
    tags: list[str] = field(default_factory=list)


def load_knowledge(path: Path) -> list[KnowledgeEntry]:
    if not path.exists():
        logger.warning("Knowledge file not found: %s", path)
        return []
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        entries = []
        for item in data.get("entries", []):
            entries.append(
                KnowledgeEntry(
                    id=item.get("id", 0),
                    question=item.get("question", ""),
                    answer=item.get("answer", ""),
                    tags=item.get("tags", []),
                )
            )
        logger.info("Loaded %d knowledge entries from %s", len(entries), path)
        return entries
    except (json.JSONDecodeError, KeyError) as e:
        logger.error("Failed to load knowledge file: %s", e)
        return []


def append_entry(path: Path, question: str, answer: str, tags: list[str] = None):
    """Add a new entry to the knowledge JSON file (developer use only)."""
    if tags is None:
        tags = []
    if path.exists():
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {"entries": []}

    existing_ids = [e.get("id", 0) for e in data["entries"]]
    new_id = max(existing_ids, default=0) + 1

    data["entries"].append({
        "id": new_id,
        "question": question,
        "answer": answer,
        "tags": tags,
    })

    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    logger.info("Appended entry #%d to %s", new_id, path)
    return new_id
