from rapidfuzz import fuzz, process
from core.knowledge_loader import KnowledgeEntry
from utils.text import normalize
from utils.logger import get_logger
from config import MATCH_THRESHOLD

logger = get_logger()


class KnowledgeSearch:
    def __init__(self, entries: list[KnowledgeEntry]):
        self.entries = entries
        # Pre-build normalized question index for fast lookup
        self._index: list[tuple[str, int]] = [
            (normalize(e.question), i) for i, e in enumerate(entries)
        ]

    def reload(self, entries: list[KnowledgeEntry]):
        self.entries = entries
        self._index = [
            (normalize(e.question), i) for i, e in enumerate(entries)
        ]

    def find_best(self, query: str) -> KnowledgeEntry | None:
        if not self._index:
            return None

        normalized_query = normalize(query)
        questions = [q for q, _ in self._index]

        result = process.extractOne(
            normalized_query,
            questions,
            scorer=fuzz.WRatio,
        )

        if result is None:
            return None

        matched_question, score, idx = result

        if score < MATCH_THRESHOLD:
            logger.debug(
                "No match above threshold: best='%s' score=%.1f",
                matched_question[:60],
                score,
            )
            return None

        original_idx = self._index[idx][1]
        entry = self.entries[original_idx]
        logger.debug(
            "Match found: score=%.1f question='%s'",
            score,
            entry.question[:60],
        )
        return entry

    def find_top(self, query: str, limit: int = 3) -> list[tuple[KnowledgeEntry, float]]:
        """Return top N matches with their scores."""
        if not self._index:
            return []

        normalized_query = normalize(query)
        questions = [q for q, _ in self._index]

        results = process.extract(
            normalized_query,
            questions,
            scorer=fuzz.WRatio,
            limit=limit,
        )

        matches = []
        for matched_q, score, idx in results:
            if score >= MATCH_THRESHOLD:
                original_idx = self._index[idx][1]
                matches.append((self.entries[original_idx], score))

        return matches
