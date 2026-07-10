"""
Tests for core/memory.py and utils/helpers.py
Run with: python -m pytest tests/ -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
from core.memory import SessionMemory, Message
from utils.helpers import clean_whitespace, truncate, is_arabic, normalize_arabic


# --- SessionMemory Tests ---

class TestSessionMemory:
    def setup_method(self):
        self.memory = SessionMemory(max_size=5)

    def test_add_and_retrieve(self):
        self.memory.add("user", "Hello")
        history = self.memory.get_history()
        assert len(history) == 1
        assert history[0].role == "user"
        assert history[0].content == "Hello"

    def test_max_size_enforced(self):
        for i in range(10):
            self.memory.add("user", f"Message {i}")
        assert len(self.memory) == 5

    def test_oldest_message_dropped(self):
        for i in range(6):
            self.memory.add("user", f"Message {i}")
        history = self.memory.get_history()
        # First message (index 0) should be Message 1, not Message 0
        assert history[0].content == "Message 1"

    def test_last_user_message(self):
        self.memory.add("user", "First question")
        self.memory.add("assistant", "First answer")
        self.memory.add("user", "Second question")
        assert self.memory.last_user_message() == "Second question"

    def test_last_user_message_empty(self):
        assert self.memory.last_user_message() is None

    def test_clear(self):
        self.memory.add("user", "Hello")
        self.memory.clear()
        assert len(self.memory) == 0

    def test_roles_are_stored_correctly(self):
        self.memory.add("user", "Hi")
        self.memory.add("assistant", "Hello!")
        history = self.memory.get_history()
        assert history[0].role == "user"
        assert history[1].role == "assistant"

    def test_empty_memory_returns_empty_list(self):
        assert self.memory.get_history() == []


# --- Helper Function Tests ---

class TestHelpers:
    def test_clean_whitespace(self):
        result = clean_whitespace("  hello   world  ")
        assert result == "hello world"

    def test_clean_whitespace_newlines(self):
        result = clean_whitespace("hello\n\nworld")
        assert result == "hello world"

    def test_truncate_short_string(self):
        result = truncate("Hello", 100)
        assert result == "Hello"

    def test_truncate_long_string(self):
        long_text = "A" * 300
        result = truncate(long_text, 100)
        assert len(result) <= 104  # 100 + ellipsis

    def test_truncate_adds_ellipsis(self):
        result = truncate("A" * 50, 20)
        assert result.endswith("…")

    def test_is_arabic_true(self):
        assert is_arabic("ما هو أمن المعلومات؟") is True

    def test_is_arabic_false_english(self):
        assert is_arabic("What is cybersecurity?") is False

    def test_is_arabic_mixed_false(self):
        # Mostly English
        assert is_arabic("What is SQL injection? قليل عربي") is False

    def test_normalize_arabic_removes_diacritics(self):
        text_with_diacritics = "مُحَمَّدٌ"
        normalized = normalize_arabic(text_with_diacritics)
        assert "ُ" not in normalized
        assert "َ" not in normalized
        assert "م" in normalized
