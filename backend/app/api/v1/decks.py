"""
Decks API Router
"""

import csv
import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.deck import DeckCreate, DeckResponse, DeckWithWords, WordResponse
from app.models.deck import Deck, Word

router = APIRouter()


@router.get("/decks", response_model=list[DeckResponse])
async def list_decks(
    db: Session = Depends(get_db)
):
    """
    List all available decks.
    """
    decks = db.query(Deck).all()

    # Add word count to each deck
    result = []
    for deck in decks:
        word_count = db.query(Word).filter(Word.deck_id == deck.id).count()
        deck_dict = DeckResponse.from_orm(deck).model_dump()
        deck_dict['word_count'] = word_count
        result.append(DeckResponse(**deck_dict))

    return result


@router.get("/decks/{deck_id}", response_model=DeckWithWords)
async def get_deck(
    deck_id: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific deck with all its words.
    """
    deck = db.query(Deck).filter(Deck.id == deck_id).first()
    if not deck:
        raise HTTPException(status_code=404, detail=f"Deck {deck_id} not found")

    return deck


@router.post("/decks/upload", response_model=DeckResponse)
async def upload_deck(
    file: UploadFile = File(...),
    name: str = None,
    description: str = None,
    db: Session = Depends(get_db)
):
    """
    Upload a CSV file to create a new deck.

    CSV format: word,meaning
    Example:
        escape,탈출하다
        abandon,버리다
    """
    try:
        # Read CSV content
        content = await file.read()
        text = content.decode('utf-8')

        # Parse CSV
        csv_reader = csv.reader(io.StringIO(text))
        words_data = []

        for index, row in enumerate(csv_reader):
            if len(row) < 2:
                continue

            word = row[0].strip()
            meaning = row[1].strip()

            if word and meaning:
                words_data.append({
                    'word': word,
                    'meaning': meaning,
                    'index_in_deck': index
                })

        if not words_data:
            raise HTTPException(status_code=400, detail="No valid words found in CSV")

        # Create deck
        deck_name = name or file.filename.replace('.csv', '')
        deck = Deck(
            name=deck_name,
            description=description,
            csv_path=file.filename
        )

        db.add(deck)
        db.commit()
        db.refresh(deck)

        # Add words
        for word_data in words_data:
            word = Word(
                deck_id=deck.id,
                word=word_data['word'],
                meaning=word_data['meaning'],
                index_in_deck=word_data['index_in_deck']
            )
            db.add(word)

        db.commit()
        db.refresh(deck)

        # Return deck with word count
        deck_dict = DeckResponse.from_orm(deck).model_dump()
        deck_dict['word_count'] = len(words_data)

        return DeckResponse(**deck_dict)

    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="Invalid CSV encoding. Please use UTF-8.")
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to upload deck: {str(e)}")


@router.delete("/decks/{deck_id}")
async def delete_deck(
    deck_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete a deck and all its words.
    """
    deck = db.query(Deck).filter(Deck.id == deck_id).first()
    if not deck:
        raise HTTPException(status_code=404, detail=f"Deck {deck_id} not found")

    db.delete(deck)
    db.commit()

    return {"message": f"Deck {deck_id} deleted successfully"}


@router.get("/decks/{deck_id}/words", response_model=list[WordResponse])
async def get_deck_words(
    deck_id: int,
    db: Session = Depends(get_db)
):
    """
    Get all words in a deck.
    """
    deck = db.query(Deck).filter(Deck.id == deck_id).first()
    if not deck:
        raise HTTPException(status_code=404, detail=f"Deck {deck_id} not found")

    words = db.query(Word).filter(Word.deck_id == deck_id).order_by(Word.index_in_deck).all()
    return words
