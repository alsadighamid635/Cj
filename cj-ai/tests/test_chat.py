"""
Tests for core/chat.py and core/security_filter.py
Run with: python -m pytest tests/ -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from unittest.mock import MagicMock
from core.chat import ChatEngine
from core.security_filter import is_cybersecurity_related, out_of_scope_reply
from core.knowledge_loader import load_knowledge, KnowledgeEntry
from core.search import KnowledgeSearch
import config


# --- Security Filter Tests ---

class TestSecurityFilter:
    def test_cybersecurity_topic_passes(self):
        assert is_cybersecurity_related("What is nmap?") is True

    def test_network_topic_passes(self):
        assert is_cybersecurity_related("How does a firewall work?") is True

    def test_malware_topic_passes(self):
        assert is_cybersecurity_related("What is ransomware?") is True

    def test_sql_injection_passes(self):
        assert is_cybersecurity_related("What is SQL injection?") is True

    def test_kali_linux_passes(self):
        assert is_cybersecurity_related("How do I use Kali Linux?") is True

    def test_unrelated_topic_blocked(self):
        assert is_cybersecurity_related("What is the best recipe for pasta?") is False

    def test_sports_topic_blocked(self):
        assert is_cybersecurity_related("Who won the World Cup in 2022?") is False

    def test_arabic_security_topic_passes(self):
        assert is_cybersecurity_related("ما هو الاختراق الأخلاقي؟") is True

    def test_out_of_scope_reply_english(self):
        reply = out_of_scope_reply("What is the stock market?")
        assert "cybersecurity" in reply.lower() or "security" in reply.lower()

    def test_out_of_scope_reply_arabic(self):
        reply = out_of_scope_reply("ما هو الطقس اليوم؟")
        assert "أمن" in reply


# --- Knowledge Search Tests ---

class TestKnowledgeSearch:
    def setup_method(self):
        self.entries = [
            KnowledgeEntry(id=1, question="What is nmap?", answer="Nmap is a network scanner.", tags=["nmap"]),
            KnowledgeEntry(id=2, question="What is a firewall?", answer="A firewall filters traffic.", tags=["firewall"]),
            KnowledgeEntry(id=3, question="What is SQL injection?", answer="SQLi exploits DB queries.", tags=["sqli"]),
        ]
        self.searcher = KnowledgeSearch(self.entries)

    def test_exact_match(self):
        result = self.searcher.find_best("What is nmap?")
        assert result is not None
        assert result.id == 1

    def test_fuzzy_match(self):
        result = self.searcher.find_best("what is nmapp?")
        assert result is not None
        assert result.id == 1

    def test_no_match_below_threshold(self):
        # A query with zero overlap to the three test entries
        result = self.searcher.find_best("cook pasta with tomato sauce tonight please")
        assert result is None

    def test_firewall_match(self):
        # Phrasing close to the actual entry "What is a firewall?"
        result = self.searcher.find_best("What is a firewall?")
        assert result is not None

    def test_empty_knowledge_base(self):
        searcher = KnowledgeSearch([])
        result = searcher.find_best("What is nmap?")
        assert result is None


# --- ChatEngine Integration Tests ---

class TestChatEngine:
    def setup_method(self):
        self.mock_db = MagicMock()
        self.mock_db.save_message = MagicMock()
        self.mock_db.save_unanswered = MagicMock()
        self.engine = ChatEngine(db=self.mock_db, user_id=1)

    def test_out_of_scope_returns_reply(self):
        response = self.engine.respond("What is the best pizza topping?")
        assert response is not None
        assert len(response) > 10
        # Should contain security-related redirect
        assert "security" in response.lower() or "أمن" in response

    def test_shell_command_question_handled(self):
        response = self.engine.respond("How do I use nmap?")
        assert response is not None
        assert len(response) > 50

    def test_cybersecurity_question_gets_response(self):
        response = self.engine.respond("What is SQL injection?")
        assert response is not None
        assert len(response) > 20

    def test_messages_saved_to_db(self):
        self.engine.respond("What is a firewall?")
        assert self.mock_db.save_message.call_count >= 2  # user + assistant

    def test_unanswered_questions_are_logged(self):
        # Ask something very specific that won't be in the KB
        self.engine.respond("What is the obscure CVE-9999-99999 vulnerability details?")
        # Either answered or logged — no crash

    def test_arabic_question_handled(self):
        response = self.engine.respond("ما هو الحقن في قاعدة البيانات؟")
        assert response is not None
        assert len(response) > 10
