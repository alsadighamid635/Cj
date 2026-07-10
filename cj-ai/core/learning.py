"""
Learning module — records questions CJ-AI could not answer.
Developers can later review these via the database and add them
to knowledge.json using knowledge_loader.append_entry().
"""

from database.database import Database
from utils.logger import get_logger

logger = get_logger()


class LearningModule:
    def __init__(self, db: Database):
        self.db = db

    def record_unanswered(self, user_id: int, question: str):
        """Save a question that had no match to the unanswered table."""
        self.db.save_unanswered(user_id, question)
        logger.info("Recorded unanswered question for review.")

    def get_pending_review(self) -> list[dict]:
        """Return all questions not yet reviewed by a developer."""
        return self.db.get_unreviewed()

    def mark_as_reviewed(self, question_id: int):
        self.db.mark_reviewed(question_id)
