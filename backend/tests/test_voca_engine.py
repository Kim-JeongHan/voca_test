"""
Unit tests for VocaTestEngine (C++ wrapper with Python fallback).

These tests verify the core scoring logic without any external dependencies.
"""

import pytest
from app.core.voca_engine import VocaTestEngine, VocaRepository


class TestVocaTestEngine:
    """Test VocaTestEngine scoring logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.engine = VocaTestEngine()

    @pytest.mark.unit
    def test_normalize_basic(self):
        """Test basic text normalization."""
        assert self.engine.normalize("hello") == "hello"
        assert self.engine.normalize("HELLO") == "hello"
        assert self.engine.normalize("HeLLo") == "hello"

    @pytest.mark.unit
    def test_normalize_with_spaces(self):
        """Test normalization removes spaces."""
        assert self.engine.normalize("hello world") == "helloworld"
        assert self.engine.normalize("  hello  ") == "hello"
        assert self.engine.normalize("h e l l o") == "hello"

    @pytest.mark.unit
    def test_normalize_with_quotes(self):
        """Test normalization removes quotes."""
        assert self.engine.normalize("'hello'") == "hello"
        assert self.engine.normalize('"hello"') == "hello"
        assert self.engine.normalize("'hello") == "hello"
        assert self.engine.normalize("hello'") == "hello"

    @pytest.mark.unit
    def test_is_correct_exact_match(self):
        """Test exact match answers."""
        assert self.engine.is_correct("탈출하다", "탈출하다") is True
        assert self.engine.is_correct("escape", "escape") is True

    @pytest.mark.unit
    def test_is_correct_case_insensitive(self):
        """Test case-insensitive matching."""
        assert self.engine.is_correct("ESCAPE", "escape") is True
        assert self.engine.is_correct("escape", "ESCAPE") is True
        assert self.engine.is_correct("EsCaPe", "escape") is True

    @pytest.mark.unit
    def test_is_correct_with_spaces(self):
        """Test matching ignores spaces."""
        assert self.engine.is_correct("탈출 하다", "탈출하다") is True
        assert self.engine.is_correct("탈출하다", "탈출 하다") is True
        assert self.engine.is_correct(" 탈출하다 ", "탈출하다") is True

    @pytest.mark.unit
    def test_is_correct_with_quotes(self):
        """Test matching ignores quotes."""
        assert self.engine.is_correct("'탈출하다'", "탈출하다") is True
        assert self.engine.is_correct('"탈출하다"', "탈출하다") is True

    @pytest.mark.unit
    def test_is_correct_multiple_answers(self):
        """Test comma-separated multiple correct answers."""
        # Single match in list
        assert self.engine.is_correct("탈출하다", "탈출하다,도망가다") is True
        assert self.engine.is_correct("도망가다", "탈출하다,도망가다") is True

        # Case insensitive with multiple
        assert self.engine.is_correct("ESCAPE", "escape,flee") is True
        assert self.engine.is_correct("flee", "escape,FLEE") is True

    @pytest.mark.unit
    def test_is_correct_multiple_with_spaces(self):
        """Test multiple answers with spaces in list."""
        assert self.engine.is_correct("탈출하다", "탈출하다, 도망가다") is True
        assert self.engine.is_correct("도망가다", "탈출하다 , 도망가다") is True

    @pytest.mark.unit
    def test_is_correct_wrong_answer(self):
        """Test wrong answers return False."""
        assert self.engine.is_correct("wrong", "correct") is False
        assert self.engine.is_correct("버리다", "탈출하다") is False
        assert self.engine.is_correct("abc", "def,ghi,jkl") is False

    @pytest.mark.unit
    def test_is_correct_partial_match_fails(self):
        """Test partial matches don't count as correct."""
        assert self.engine.is_correct("탈출", "탈출하다") is False
        assert self.engine.is_correct("esca", "escape") is False

    @pytest.mark.unit
    def test_is_correct_empty_strings(self):
        """Test behavior with empty strings."""
        assert self.engine.is_correct("", "answer") is False
        assert self.engine.is_correct("answer", "") is False
        assert self.engine.is_correct("", "") is True

    @pytest.mark.unit
    def test_is_correct_unicode_normalization(self):
        """Test Korean text normalization."""
        # Same meaning, different spacing
        assert self.engine.is_correct("버리다", "버 리 다") is True
        assert self.engine.is_correct("성취하다", "성 취 하 다") is True


class TestVocaRepository:
    """Test VocaRepository (simple word storage)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.repo = VocaRepository()

    @pytest.mark.unit
    def test_add_word(self):
        """Test adding words to repository."""
        self.repo.add_word("escape", "탈출하다")
        words = self.repo.get_all_words()

        assert len(words) == 1
        assert words[0]["word"] == "escape"
        assert words[0]["meaning"] == "탈출하다"

    @pytest.mark.unit
    def test_add_multiple_words(self):
        """Test adding multiple words."""
        self.repo.add_word("escape", "탈출하다")
        self.repo.add_word("abandon", "버리다")
        self.repo.add_word("achieve", "성취하다")

        words = self.repo.get_all_words()
        assert len(words) == 3

    @pytest.mark.unit
    def test_clear(self):
        """Test clearing repository."""
        self.repo.add_word("escape", "탈출하다")
        self.repo.add_word("abandon", "버리다")
        assert len(self.repo.get_all_words()) == 2

        self.repo.clear()
        assert len(self.repo.get_all_words()) == 0

    @pytest.mark.unit
    def test_get_all_words_empty(self):
        """Test get_all_words on empty repository."""
        words = self.repo.get_all_words()
        assert words == []
        assert len(words) == 0


class TestVocaEngineIntegration:
    """Integration tests combining engine and repository."""

    @pytest.mark.unit
    def test_engine_with_repo_words(self):
        """Test engine validates answers against repo words."""
        repo = VocaRepository()
        engine = VocaTestEngine()

        # Add words to repo
        repo.add_word("escape", "탈출하다,도망가다")
        repo.add_word("abandon", "버리다")

        words = repo.get_all_words()

        # Test first word
        assert engine.is_correct("탈출하다", words[0]["meaning"]) is True
        assert engine.is_correct("도망가다", words[0]["meaning"]) is True
        assert engine.is_correct("wrong", words[0]["meaning"]) is False

        # Test second word
        assert engine.is_correct("버리다", words[1]["meaning"]) is True
        assert engine.is_correct("wrong", words[1]["meaning"]) is False
