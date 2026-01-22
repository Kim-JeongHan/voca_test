from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class WrongStats(Base):
    __tablename__ = "wrong_stats"
    __table_args__ = (
        UniqueConstraint('word', 'deck_id', name='unique_word_deck'),
    )

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, nullable=False, index=True)
    deck_id = Column(Integer, ForeignKey("decks.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    # Statistics
    wrong_count = Column(Integer, default=0)
    last_wrong_at = Column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    deck = relationship("Deck")
    user = relationship("User")
