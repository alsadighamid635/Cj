"""
RAG pipeline: the main brain of CJ-AI Web.
Handles a user query end-to-end.
"""

import json
from dataclasses import dataclass, field
from core import vectorstore
from core.generator import build_response
from core.security_filter import is_cybersecurity_related, out_of_scope_reply
from utils.text import is_arabic
from utils.logger import get_logger
from database.db import Database

# Shell command reference (re-used from cj-ai logic, inline check)
from core import shell_ref

logger = get_logger()


@dataclass
class ChatResponse:
    text: str
    confidence: str = "high"
    sources: list[str] = field(default_factory=list)
    in_scope: bool = True


class RAGPipeline:
    def __init__(self, db: Database):
        self.db = db

    def query(self, user_input: str, session_id: str) -> ChatResponse:
        text = user_input.strip()

        # 1. Shell command reference — always answer tool questions first
        cmd_resp = shell_ref.get_response(text)
        if cmd_resp:
            self.db.save_message(session_id, "user", text)
            self.db.save_message(session_id, "assistant", cmd_resp, confidence="high")
            return ChatResponse(text=cmd_resp, confidence="high")

        # 2. Search all vector collections
        hits = vectorstore.search_all(text)

        # 3. Fetch recent conversation history for LLM context
        recent = self.db.get_messages(session_id, limit=6)
        history = [{"role": m["role"], "content": m["content"]} for m in recent]

        # 4. Generate response (LLM + RAG context)
        response_text, confidence, sources = build_response(text, hits, history)

        # 5. If no answer AND not cybersecurity → politely decline
        if confidence == "low" and not is_cybersecurity_related(text):
            reply = out_of_scope_reply(text)
            self.db.save_message(session_id, "user", text)
            self.db.save_message(session_id, "assistant", reply, confidence="low")
            return ChatResponse(text=reply, confidence="low", in_scope=False)

        # 6. Record unanswered cybersecurity questions for future learning
        if confidence == "low":
            self.db.save_unanswered(session_id, text)

        # 7. Persist to DB
        self.db.save_message(session_id, "user", text)
        self.db.save_message(session_id, "assistant", response_text,
                             confidence=confidence,
                             sources=json.dumps(sources))

        # 8. Store this Q&A turn in chat memory for future context
        if confidence == "high":
            _store_chat_memory(session_id, text, response_text)

        return ChatResponse(text=response_text, confidence=confidence, sources=sources)


def _store_chat_memory(session_id: str, question: str, answer: str):
    import hashlib
    doc_id = "chat_" + hashlib.md5(f"{session_id}{question}".encode()).hexdigest()[:12]
    vectorstore.add_documents(
        "chat_memory",
        ids=[doc_id],
        documents=[f"{question}\n{answer[:400]}"],
        metadatas=[{"type": "chat", "session_id": session_id,
                    "question": question[:200]}],
    )
