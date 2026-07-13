"""
RAG (Retrieval-Augmented Generation) pipeline — the core of CJ-AI Web.

Query flow:
  1. Shell-reference lookup  — instant answers for known security tool commands
  2. Vector search           — retrieve relevant chunks from Qdrant
  3. LLM generation          — Groq Llama produces the final answer with context
  4. Scope guard             — out-of-scope questions are politely declined
  5. Persistence             — Q&A saved to SQLite; high-confidence turns stored in Qdrant
"""

import hashlib
import json
from dataclasses import dataclass, field

from core import vectorstore
from core.generator import build_response
from core.security_filter import is_cybersecurity_related, out_of_scope_reply
from core import shell_ref
from database.db import Database
from utils.logger import get_logger

logger = get_logger()


@dataclass
class ChatResponse:
    text: str
    confidence: str = "high"
    sources: list[str] = field(default_factory=list)
    in_scope: bool = True


class RAGPipeline:
    """Orchestrates shell-ref lookup → vector retrieval → LLM generation → persistence."""

    def __init__(self, db: Database) -> None:
        self.db = db

    def query(
        self,
        user_input: str,
        session_id: str,
        attachment=None,   # core.file_processor.ProcessedFile | None
    ) -> ChatResponse:
        """
        Process a user message and return a structured ChatResponse.
        Side effects: persists messages to SQLite and high-confidence turns to Qdrant.

        attachment: optional ProcessedFile (image or document).  When present:
          • image    → forwarded to the Groq Vision model via build_response()
          • document → extracted text injected into the LLM context
        Skip the shell-ref shortcut when a file is attached so the LLM always sees it.
        """
        text = user_input.strip()

        # 1. Instant answer for known security tool questions (no LLM needed)
        #    Skip when a file is attached — the user wants file analysis, not a shell snippet.
        if not attachment:
            cmd_resp = shell_ref.get_response(text)
            if cmd_resp:
                self.db.save_message(session_id, "user", text)
                self.db.save_message(session_id, "assistant", cmd_resp, confidence="high")
                return ChatResponse(text=cmd_resp, confidence="high")

        # 2. Retrieve semantically relevant chunks from all Qdrant collections
        hits = vectorstore.search_all(text)

        # 3. Fetch recent conversation turns to give the LLM short-term memory
        recent  = self.db.get_messages(session_id, limit=6)
        history = [{"role": m["role"], "content": m["content"]} for m in recent]

        # 4. Generate response via Groq LLM (falls back to chunk formatting if unavailable)
        response_text, confidence, sources = build_response(
            text, hits, history, attachment=attachment
        )

        # 5. Scope guard — only decline if the LLM also has no answer (skip for file uploads)
        if not attachment and confidence == "low" and not is_cybersecurity_related(text):
            reply = out_of_scope_reply(text)
            self.db.save_message(session_id, "user", text)
            self.db.save_message(session_id, "assistant", reply, confidence="low")
            return ChatResponse(text=reply, confidence="low", in_scope=False)

        # 6. Log unanswered cybersecurity questions for future learning
        if confidence == "low":
            self.db.save_unanswered(session_id, text)

        # 7. Persist the Q&A exchange to SQLite
        display_text = text
        if attachment:
            display_text = f"[{attachment.filename}] {text}"
        self.db.save_message(session_id, "user", display_text)
        self.db.save_message(
            session_id, "assistant", response_text,
            confidence=confidence,
            sources=json.dumps(sources),
        )

        # 8. Index high-confidence turns in Qdrant for future context retrieval
        if confidence == "high":
            self._store_chat_memory(session_id, text, response_text)

        return ChatResponse(text=response_text, confidence=confidence, sources=sources)

    def _store_chat_memory(self, session_id: str, question: str, answer: str) -> None:
        """
        Store a Q&A turn in the chat_memory Qdrant collection so the RAG pipeline
        can retrieve it as context in future turns of the same (or related) sessions.
        """
        doc_id = "chat_" + hashlib.md5(f"{session_id}{question}".encode()).hexdigest()[:12]
        vectorstore.add_documents(
            collection_name="chat_memory",
            ids=[doc_id],
            documents=[f"{question}\n{answer[:400]}"],
            metadatas=[{
                "type":       "chat",
                "session_id": session_id,
                "question":   question[:200],
            }],
        )
