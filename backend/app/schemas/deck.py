# -*- coding: utf-8 -*-
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class WordBase(BaseModel):
    word: str
    meaning: str
    index_in_deck: int


class WordCreate(WordBase):
    pass


class WordResponse(WordBase):
    id: int
    deck_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class DeckBase(BaseModel):
    name: str
    description: Optional[str] = None


class DeckCreate(DeckBase):
    csv_path: Optional[str] = None


class DeckResponse(DeckBase):
    id: int
    csv_path: Optional[str]
    user_id: Optional[int]
    is_public: bool = False
    created_at: datetime
    updated_at: Optional[datetime]
    word_count: Optional[int] = Field(None, description="Number of words in deck")

    class Config:
        from_attributes = True


class DeckWithWords(DeckResponse):
    words: list[WordResponse]

    class Config:
        from_attributes = True
