# -*- coding: utf-8 -*-
"""
C++ Engine Wrapper with Python Fallback

This module provides a Python interface to the C++ VocaTestEngine.
If pybind11 bindings are not available, it falls back to a pure Python implementation.
"""

import re


class VocaTestEngine:
    """
    Test engine for vocabulary quiz.
    Implements the same logic as C++ VocaTestEngine.
    """

    @staticmethod
    def normalize(text: str) -> str:
        """
        Normalize text by removing spaces, quotes, and converting to lowercase.

        Args:
            text: Input text to normalize

        Returns:
            Normalized text
        """
        # Remove spaces and quotes, convert to lowercase
        normalized = re.sub(r'[\s\'""]', "", text)
        return normalized.lower()

    def is_correct(self, answer: str, correct: str) -> bool:
        """
        Check if the answer is correct.
        Supports comma-separated multiple correct answers.

        Args:
            answer: User's answer
            correct: Correct answer(s), comma-separated

        Returns:
            True if answer is correct, False otherwise
        """
        norm_answer = self.normalize(answer)

        # Split by comma for multiple correct answers
        meanings = [m.strip() for m in correct.split(",")]

        # Check if any normalized meaning matches the normalized answer
        for meaning in meanings:
            if self.normalize(meaning) == norm_answer:
                return True

        return False


class VocaRepository:
    """
    Simple word repository.
    In the FastAPI implementation, this is replaced by SQLAlchemy models.
    """

    def __init__(self):
        self.words = []

    def add_word(self, word: str, meaning: str):
        """Add a word to the repository."""
        self.words.append({"word": word, "meaning": meaning})

    def get_all_words(self):
        """Get all words."""
        return self.words

    def clear(self):
        """Clear all words."""
        self.words = []


# Try to import pybind11 bindings, fall back to Python implementation
_USING_CPP = False

try:
    from . import voca_cpp

    # Override with C++ implementations
    CppVocaTestEngine = voca_cpp.VocaTestEngine
    CppVocaSession = voca_cpp.VocaSession
    CppVocaResult = voca_cpp.VocaResult
    CppWrongVoca = voca_cpp.WrongVoca

    _USING_CPP = True
    print("Using C++ engine via pybind11")
except ImportError:
    print("pybind11 bindings not available, using Python fallback")
    CppVocaTestEngine = None
    CppVocaSession = None
    CppVocaResult = None
    CppWrongVoca = None


def is_using_cpp() -> bool:
    """Check if C++ engine is being used."""
    return _USING_CPP


def get_engine():
    """Get the appropriate engine class (C++ or Python fallback)."""
    if _USING_CPP:
        return CppVocaTestEngine()
    return VocaTestEngine()


def get_session():
    """Get the appropriate session class (C++ or Python fallback)."""
    if _USING_CPP:
        return CppVocaSession()
    # Python fallback would need a VocaSession implementation
    raise NotImplementedError("Python VocaSession fallback not implemented")
