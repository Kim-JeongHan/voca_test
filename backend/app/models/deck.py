from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class Deck(Base):
    __tablename__ = "decks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(Text, nullable=True)
    csv_path = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    words = relationship("Word", back_populates="deck", cascade="all, delete-orphan")
    user = relationship("User")


class Word(Base):
    __tablename__ = "words"

    id = Column(Integer, primary_key=True, index=True)
    deck_id = Column(Integer, ForeignKey("decks.id"), nullable=False)
    word = Column(String, nullable=False, index=True)
    meaning = Column(Text, nullable=False)
    index_in_deck = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    deck = relationship("Deck", back_populates="words")
