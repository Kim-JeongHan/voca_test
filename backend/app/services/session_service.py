"""
Session Service - Vocabulary Quiz Session Management

Manages quiz sessions using C++ engine for scoring logic.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session as DBSession
from sqlalchemy.sql import func

from app.core.voca_engine import VocaTestEngine
from app.models.session import Session, Answer
from app.models.deck import Deck, Word
from app.models.wrong_stats import WrongStats
from app.schemas.session import (
    SessionStartRequest,
    SessionResponse,
    PromptResponse,
    SubmitRequest,
    SubmitResponse,
    SummaryResponse,
)


class SessionService:
    """Service for managing vocabulary quiz sessions."""

    def __init__(self, db: DBSession):
        self.db = db
        self.engine = VocaTestEngine()

    def start_session(self, request: SessionStartRequest) -> SessionResponse:
        """
        Start a new quiz session.

        Args:
            request: Session start request with deck_id and word_indices

        Returns:
            Session response with session info

        Raises:
            ValueError: If deck not found
        """
        # Verify deck exists
        deck = self.db.query(Deck).filter(Deck.id == request.deck_id).first()
        if not deck:
            raise ValueError(f"Deck {request.deck_id} not found")

        # Get word indices
        if request.word_indices:
            word_indices = request.word_indices
        else:
            # Get all word indices
            word_count = self.db.query(Word).filter(Word.deck_id == request.deck_id).count()
            word_indices = list(range(word_count))

        # Create session
        session = Session(
            deck_id=request.deck_id,
            word_indices=word_indices,
            current_index=0,
            score=0,
            total_questions=len(word_indices),
            is_completed=False,
            is_wrong_only=request.is_wrong_only,
        )

        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)

        return SessionResponse.from_orm(session)

    def get_prompt(self, session_id: int) -> PromptResponse:
        """
        Get current question for the session.

        Args:
            session_id: Session ID

        Returns:
            Prompt response with word and progress

        Raises:
            ValueError: If session not found or completed
        """
        session = self.db.query(Session).filter(Session.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if session.is_completed:
            raise ValueError("Session is already completed")

        if session.current_index >= len(session.word_indices):
            raise ValueError("No more questions")

        # Get current word
        word_index = session.word_indices[session.current_index]
        word = self.db.query(Word).filter(
            Word.deck_id == session.deck_id,
            Word.index_in_deck == word_index
        ).first()

        if not word:
            raise ValueError(f"Word at index {word_index} not found")

        return PromptResponse(
            word=word.word,
            index=session.current_index,
            progress=f"{session.current_index + 1}/{session.total_questions}",
            total=session.total_questions,
            current=session.current_index + 1,
        )

    def submit_answer(self, session_id: int, request: SubmitRequest) -> SubmitResponse:
        """
        Submit answer for current question.

        Args:
            session_id: Session ID
            request: Submit request with answer and hint usage

        Returns:
            Submit response with result and updated score

        Raises:
            ValueError: If session not found or completed
        """
        session = self.db.query(Session).filter(Session.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")

        if session.is_completed:
            raise ValueError("Session is already completed")

        # Get current word
        word_index = session.word_indices[session.current_index]
        word = self.db.query(Word).filter(
            Word.deck_id == session.deck_id,
            Word.index_in_deck == word_index
        ).first()

        if not word:
            raise ValueError(f"Word at index {word_index} not found")

        # Check answer using C++ engine
        is_correct = self.engine.is_correct(request.answer, word.meaning)

        # If hint was used 2+ times, mark as incorrect
        if request.hint_used >= 2:
            is_correct = False

        # Update score
        if is_correct:
            session.score += 1
        else:
            # Update wrong stats
            self._update_wrong_stats(word.word, session.deck_id)

        # Save answer
        answer = Answer(
            session_id=session_id,
            word_id=word.id,
            user_answer=request.answer,
            is_correct=is_correct,
            hint_used=request.hint_used,
        )
        self.db.add(answer)

        # Move to next question
        session.current_index += 1

        # Check if session is completed
        if session.current_index >= session.total_questions:
            session.is_completed = True
            session.completed_at = datetime.utcnow()

        self.db.commit()

        return SubmitResponse(
            is_correct=is_correct,
            correct_answer=word.meaning,
            score=session.score,
            progress=f"{session.current_index}/{session.total_questions}",
        )

    def get_summary(self, session_id: int) -> SummaryResponse:
        """
        Get summary of completed session.

        Args:
            session_id: Session ID

        Returns:
            Summary response with score and wrong words

        Raises:
            ValueError: If session not found
        """
        session = self.db.query(Session).filter(Session.id == session_id).first()
        if not session:
            raise ValueError(f"Session {session_id} not found")

        deck = self.db.query(Deck).filter(Deck.id == session.deck_id).first()

        # Get wrong answers
        wrong_answers = self.db.query(Answer).filter(
            Answer.session_id == session_id,
            Answer.is_correct == False
        ).all()

        wrong_words = []
        for answer in wrong_answers:
            word = self.db.query(Word).filter(Word.id == answer.word_id).first()
            if word:
                wrong_words.append(word.word)

        percentage = (session.score / session.total_questions * 100) if session.total_questions > 0 else 0

        return SummaryResponse(
            session_id=session_id,
            deck_name=deck.name if deck else "Unknown",
            score=session.score,
            total_questions=session.total_questions,
            percentage=round(percentage, 2),
            wrong_words=wrong_words,
            created_at=session.created_at,
            completed_at=session.completed_at,
        )

    def _update_wrong_stats(self, word: str, deck_id: int):
        """
        Update wrong statistics for a word.

        Args:
            word: Word that was answered incorrectly
            deck_id: Deck ID
        """
        stats = self.db.query(WrongStats).filter(
            WrongStats.word == word,
            WrongStats.deck_id == deck_id
        ).first()

        if stats:
            stats.wrong_count += 1
            stats.last_wrong_at = datetime.utcnow()
        else:
            stats = WrongStats(
                word=word,
                deck_id=deck_id,
                wrong_count=1,
                last_wrong_at=datetime.utcnow(),
            )
            self.db.add(stats)

        self.db.commit()

    def get_wrong_words(self, deck_id: int, min_wrong_count: int = 1) -> list[str]:
        """
        Get words that were answered incorrectly.

        Args:
            deck_id: Deck ID
            min_wrong_count: Minimum wrong count to include

        Returns:
            List of wrong words
        """
        stats = self.db.query(WrongStats).filter(
            WrongStats.deck_id == deck_id,
            WrongStats.wrong_count >= min_wrong_count
        ).all()

        return [s.word for s in stats]
