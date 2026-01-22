"""
Database Initialization Script

Creates database tables and optionally loads sample data.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import Base, engine
from app.models import Deck, Word, User


def init_db():
    """Initialize database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")


def load_sample_data():
    """Load sample deck for testing."""
    from sqlalchemy.orm import Session

    print("\nLoading sample data...")

    db = Session(bind=engine)

    try:
        # Check if sample deck already exists
        existing = db.query(Deck).filter(Deck.name == "Sample Deck").first()
        if existing:
            print("⚠️  Sample deck already exists, skipping...")
            return

        # Create sample deck
        deck = Deck(
            name="Sample Deck",
            description="Sample vocabulary deck for testing",
            csv_path="sample.csv"
        )
        db.add(deck)
        db.commit()
        db.refresh(deck)

        # Add sample words
        sample_words = [
            ("escape", "탈출하다"),
            ("abandon", "버리다"),
            ("achieve", "성취하다"),
            ("acquire", "얻다"),
            ("adapt", "적응하다"),
        ]

        for index, (word, meaning) in enumerate(sample_words):
            w = Word(
                deck_id=deck.id,
                word=word,
                meaning=meaning,
                index_in_deck=index
            )
            db.add(w)

        db.commit()
        print(f"✅ Sample deck created with {len(sample_words)} words!")

    except Exception as e:
        db.rollback()
        print(f"❌ Error loading sample data: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    init_db()

    # Ask if user wants sample data
    if "--sample" in sys.argv or "-s" in sys.argv:
        load_sample_data()
    else:
        response = input("\nLoad sample data? (y/n): ")
        if response.lower() in ['y', 'yes']:
            load_sample_data()

    print("\n✨ Database initialization complete!")
    print("\nNext steps:")
    print("  1. Start the server: uvicorn app.main:app --reload")
    print("  2. Visit: http://localhost:8000/docs")
    print("  3. Try the API endpoints!")
