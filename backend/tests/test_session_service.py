"""
Unit tests for Session Service.

Tests verify session management logic without external dependencies.
"""

import pytest
from datetime import datetime

from app.services.session_service import SessionService
from app.models.deck import Deck, Word
from app.models.session import Session, Answer
from app.models.wrong_stats import WrongStats
from app.schemas.session import SessionStartRequest, SubmitRequest


class TestSessionService:
    """Test Session service business logic."""

    @pytest.mark.unit
    def test_start_session_all_words(self, db_session, create_test_deck):
        """Test starting session with all words."""
        service = SessionService(db_session)
        request = SessionStartRequest(
            deck_id=create_test_deck.id,
            word_indices=None,
            is_wrong_only=False
        )

        response = service.start_session(request)

        assert response.deck_id == create_test_deck.id
        assert response.current_index == 0
        assert response.score == 0
        assert response.total_questions == 3  # All words
        assert response.is_completed is False
        assert response.is_wrong_only is False

    @pytest.mark.unit
    def test_start_session_specific_words(self, db_session, create_test_deck):
        """Test starting session with specific word indices."""
        service = SessionService(db_session)
        request = SessionStartRequest(
            deck_id=create_test_deck.id,
            word_indices=[0, 2],  # First and third words
            is_wrong_only=False
        )

        response = service.start_session(request)

        assert response.total_questions == 2
        # Verify session in database
        session = db_session.query(Session).filter(Session.id == response.id).first()
        assert session.word_indices == [0, 2]

    @pytest.mark.unit
    def test_start_session_wrong_only(self, db_session, create_test_deck):
        """Test starting wrong-only session."""
        service = SessionService(db_session)
        request = SessionStartRequest(
            deck_id=create_test_deck.id,
            word_indices=[1],
            is_wrong_only=True
        )

        response = service.start_session(request)

        assert response.is_wrong_only is True

    @pytest.mark.unit
    def test_start_session_invalid_deck(self, db_session):
        """Test starting session with non-existent deck."""
        service = SessionService(db_session)
        request = SessionStartRequest(
            deck_id=999,  # Non-existent
            word_indices=None,
            is_wrong_only=False
        )

        with pytest.raises(ValueError, match="Deck 999 not found"):
            service.start_session(request)

    @pytest.mark.unit
    def test_get_prompt_first_question(self, db_session, create_test_deck):
        """Test getting first question prompt."""
        service = SessionService(db_session)

        # Start session
        request = SessionStartRequest(
            deck_id=create_test_deck.id,
            word_indices=None,
            is_wrong_only=False
        )
        session_response = service.start_session(request)

        # Get prompt
        prompt = service.get_prompt(session_response.id)

        assert prompt.word == "escape"  # First word
        assert prompt.index == 0
        assert prompt.current == 1
        assert prompt.total == 3
        assert prompt.progress == "1/3"

    @pytest.mark.unit
    def test_get_prompt_invalid_session(self, db_session):
        """Test getting prompt for non-existent session."""
        service = SessionService(db_session)

        with pytest.raises(ValueError, match="Session 999 not found"):
            service.get_prompt(999)

    @pytest.mark.unit
    def test_get_prompt_completed_session(self, db_session, create_test_deck):
        """Test getting prompt for completed session fails."""
        service = SessionService(db_session)

        # Create completed session
        session = Session(
            deck_id=create_test_deck.id,
            word_indices=[0],
            current_index=1,  # Past the end
            score=0,
            total_questions=1,
            is_completed=True,
            completed_at=datetime.utcnow()
        )
        db_session.add(session)
        db_session.commit()

        with pytest.raises(ValueError, match="already completed"):
            service.get_prompt(session.id)

    @pytest.mark.unit
    def test_submit_answer_correct(self, db_session, create_test_deck):
        """Test submitting correct answer."""
        service = SessionService(db_session)

        # Start session
        request = SessionStartRequest(
            deck_id=create_test_deck.id,
            word_indices=None,
            is_wrong_only=False
        )
        session_response = service.start_session(request)

        # Submit correct answer
        submit_request = SubmitRequest(
            answer="탈출하다",
            hint_used=0
        )
        result = service.submit_answer(session_response.id, submit_request)

        assert result.is_correct is True
        assert result.correct_answer == "탈출하다"
        assert result.score == 1
        assert result.progress == "1/3"

        # Verify answer was saved
        answer = db_session.query(Answer).filter(
            Answer.session_id == session_response.id
        ).first()
        assert answer is not None
        assert answer.is_correct is True
        assert answer.user_answer == "탈출하다"

    @pytest.mark.unit
    def test_submit_answer_wrong(self, db_session, create_test_deck):
        """Test submitting wrong answer."""
        service = SessionService(db_session)

        # Start session
        request = SessionStartRequest(
            deck_id=create_test_deck.id,
            word_indices=None,
            is_wrong_only=False
        )
        session_response = service.start_session(request)

        # Submit wrong answer
        submit_request = SubmitRequest(
            answer="wrong_answer",
            hint_used=0
        )
        result = service.submit_answer(session_response.id, submit_request)

        assert result.is_correct is False
        assert result.score == 0

        # Verify wrong stats were updated
        stats = db_session.query(WrongStats).filter(
            WrongStats.word == "escape",
            WrongStats.deck_id == create_test_deck.id
        ).first()
        assert stats is not None
        assert stats.wrong_count == 1

    @pytest.mark.unit
    def test_submit_answer_with_hints(self, db_session, create_test_deck):
        """Test that using 2+ hints marks answer as wrong."""
        service = SessionService(db_session)

        # Start session
        request = SessionStartRequest(
            deck_id=create_test_deck.id,
            word_indices=None,
            is_wrong_only=False
        )
        session_response = service.start_session(request)

        # Submit correct answer but with 2 hints
        submit_request = SubmitRequest(
            answer="탈출하다",  # Correct answer
            hint_used=2  # But used hints
        )
        result = service.submit_answer(session_response.id, submit_request)

        assert result.is_correct is False  # Marked wrong due to hints
        assert result.score == 0

    @pytest.mark.unit
    def test_submit_answer_advances_session(self, db_session, create_test_deck):
        """Test that submitting answer advances to next question."""
        service = SessionService(db_session)

        # Start session
        request = SessionStartRequest(
            deck_id=create_test_deck.id,
            word_indices=None,
            is_wrong_only=False
        )
        session_response = service.start_session(request)

        # Submit answer
        submit_request = SubmitRequest(answer="탈출하다", hint_used=0)
        service.submit_answer(session_response.id, submit_request)

        # Get next prompt
        next_prompt = service.get_prompt(session_response.id)

        assert next_prompt.word == "abandon"  # Second word
        assert next_prompt.current == 2
        assert next_prompt.progress == "2/3"

    @pytest.mark.unit
    def test_submit_answer_completes_session(self, db_session, create_test_deck):
        """Test that last answer completes the session."""
        service = SessionService(db_session)

        # Start session with only one word
        request = SessionStartRequest(
            deck_id=create_test_deck.id,
            word_indices=[0],
            is_wrong_only=False
        )
        session_response = service.start_session(request)

        # Submit answer
        submit_request = SubmitRequest(answer="탈출하다", hint_used=0)
        service.submit_answer(session_response.id, submit_request)

        # Verify session is completed
        session = db_session.query(Session).filter(Session.id == session_response.id).first()
        assert session.is_completed is True
        assert session.completed_at is not None

    @pytest.mark.unit
    def test_get_summary(self, db_session, create_test_deck):
        """Test getting session summary."""
        service = SessionService(db_session)

        # Create completed session
        request = SessionStartRequest(
            deck_id=create_test_deck.id,
            word_indices=[0, 1],
            is_wrong_only=False
        )
        session_response = service.start_session(request)

        # Submit answers
        service.submit_answer(session_response.id, SubmitRequest(answer="탈출하다", hint_used=0))  # Correct
        service.submit_answer(session_response.id, SubmitRequest(answer="wrong", hint_used=0))  # Wrong

        # Get summary
        summary = service.get_summary(session_response.id)

        assert summary.session_id == session_response.id
        assert summary.deck_name == "Test Deck"
        assert summary.score == 1
        assert summary.total_questions == 2
        assert summary.percentage == 50.0
        assert "abandon" in summary.wrong_words

    @pytest.mark.unit
    def test_get_wrong_words(self, db_session, create_test_deck):
        """Test getting wrong words for a deck."""
        service = SessionService(db_session)

        # Create wrong stats
        stats1 = WrongStats(
            word="escape",
            deck_id=create_test_deck.id,
            wrong_count=2
        )
        stats2 = WrongStats(
            word="abandon",
            deck_id=create_test_deck.id,
            wrong_count=1
        )
        db_session.add_all([stats1, stats2])
        db_session.commit()

        # Get wrong words
        wrong_words = service.get_wrong_words(create_test_deck.id, min_wrong_count=1)

        assert len(wrong_words) == 2
        assert "escape" in wrong_words
        assert "abandon" in wrong_words

    @pytest.mark.unit
    def test_get_wrong_words_with_min_count(self, db_session, create_test_deck):
        """Test filtering wrong words by minimum count."""
        service = SessionService(db_session)

        # Create wrong stats
        stats1 = WrongStats(
            word="escape",
            deck_id=create_test_deck.id,
            wrong_count=3
        )
        stats2 = WrongStats(
            word="abandon",
            deck_id=create_test_deck.id,
            wrong_count=1
        )
        db_session.add_all([stats1, stats2])
        db_session.commit()

        # Get words with at least 2 wrong answers
        wrong_words = service.get_wrong_words(create_test_deck.id, min_wrong_count=2)

        assert len(wrong_words) == 1
        assert "escape" in wrong_words
        assert "abandon" not in wrong_words

    @pytest.mark.unit
    def test_update_wrong_stats_creates_new(self, db_session, create_test_deck):
        """Test that wrong stats are created if not exist."""
        service = SessionService(db_session)

        # Update stats (should create new)
        service._update_wrong_stats("escape", create_test_deck.id)

        # Verify created
        stats = db_session.query(WrongStats).filter(
            WrongStats.word == "escape",
            WrongStats.deck_id == create_test_deck.id
        ).first()
        assert stats is not None
        assert stats.wrong_count == 1

    @pytest.mark.unit
    def test_update_wrong_stats_increments_existing(self, db_session, create_test_deck):
        """Test that wrong stats are incremented if exist."""
        service = SessionService(db_session)

        # Create initial stats
        stats = WrongStats(
            word="escape",
            deck_id=create_test_deck.id,
            wrong_count=1
        )
        db_session.add(stats)
        db_session.commit()

        # Update again
        service._update_wrong_stats("escape", create_test_deck.id)

        # Verify incremented
        updated = db_session.query(WrongStats).filter(
            WrongStats.word == "escape",
            WrongStats.deck_id == create_test_deck.id
        ).first()
        assert updated.wrong_count == 2
