from sqlalchemy import Column, Integer, String, LargeBinary, DateTime, UniqueConstraint
from sqlalchemy.sql import func
from app.database import Base


class AudioCache(Base):
    __tablename__ = "audio_cache"
    __table_args__ = (
        UniqueConstraint('text', name='unique_audio_text'),
    )

    id = Column(Integer, primary_key=True, index=True)
    text = Column(String, nullable=False, index=True, unique=True)
    audio_data = Column(LargeBinary, nullable=False)
    content_type = Column(String, default="audio/mpeg")

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class ImageCache(Base):
    __tablename__ = "image_cache"
    __table_args__ = (
        UniqueConstraint('word', name='unique_image_word'),
    )

    id = Column(Integer, primary_key=True, index=True)
    word = Column(String, nullable=False, index=True, unique=True)
    image_data = Column(LargeBinary, nullable=False)
    content_type = Column(String, default="image/png")
    github_url = Column(String, nullable=True)  # URL to image on GitHub

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
