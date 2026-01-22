from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Session(Base):
    __tablename__ = "sessions"

    id = Column(Integer, primary_key=True, index=True)
    deck_id = Column(Integer, ForeignKey("decks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Session state
    word_indices = Column(JSON, nullable=False)  # List of word indices to quiz
    current_index = Column(Integer, default=0)
    score = Column(Integer, default=0)
    total_questions = Column(Integer, nullable=False)

    # Session status
    is_completed = Column(Boolean, default=False)
    is_wrong_only = Column(Boolean, default=False)  # True if this is a "wrong only" session

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    deck = relationship("Deck")
    user = relationship("User")
    answers = relationship("Answer", back_populates="session", cascade="all, delete-orphan")


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), nullable=False)
    word_id = Column(Integer, ForeignKey("words.id"), nullable=False)

    # Answer data
    user_answer = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    hint_used = Column(Integer, default=0)  # Number of hints used

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session", back_populates="answers")
    word = relationship("Word")
