"""
Pytest fixtures for testing.

This file provides common fixtures used across all tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app


# In-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="function")
def db_engine():
    """Create a fresh database engine for each test."""
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def db_session(db_engine):
    """Create a fresh database session for each test."""
    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=db_engine
    )
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with dependency overrides."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_deck_data():
    """Sample deck data for testing."""
    return {
        "name": "Test Deck",
        "description": "Test deck for unit tests",
        "words": [
            {"word": "escape", "meaning": "탈출하다"},
            {"word": "abandon", "meaning": "버리다"},
            {"word": "achieve", "meaning": "성취하다"},
        ]
    }


@pytest.fixture
def create_test_deck(db_session, sample_deck_data):
    """Create a test deck with words in the database."""
    from app.models.deck import Deck, Word

    deck = Deck(
        name=sample_deck_data["name"],
        description=sample_deck_data["description"]
    )
    db_session.add(deck)
    db_session.commit()
    db_session.refresh(deck)

    for idx, word_data in enumerate(sample_deck_data["words"]):
        word = Word(
            deck_id=deck.id,
            word=word_data["word"],
            meaning=word_data["meaning"],
            index_in_deck=idx
        )
        db_session.add(word)

    db_session.commit()
    db_session.refresh(deck)
    return deck


@pytest.fixture
def mock_elevenlabs_response():
    """Mock successful ElevenLabs API response."""
    return b"fake_audio_data_mp3"


@pytest.fixture
def mock_huggingface_response():
    """Mock successful HuggingFace API response."""
    return b"fake_image_data_png"
