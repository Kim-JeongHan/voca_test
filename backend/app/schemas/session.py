from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class SessionStartRequest(BaseModel):
    deck_id: int
    word_indices: Optional[List[int]] = Field(None, description="Specific word indices to quiz, or None for all")
    is_wrong_only: bool = Field(False, description="True if this is a wrong-only session")


class SessionResponse(BaseModel):
    id: int
    deck_id: int
    current_index: int
    score: int
    total_questions: int
    is_completed: bool
    is_wrong_only: bool
    created_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


class PromptResponse(BaseModel):
    word: str
    index: int
    progress: str  # e.g., "1/10"
    total: int
    current: int


class SubmitRequest(BaseModel):
    answer: str
    hint_used: int = Field(0, description="Number of hints used for this question")


class SubmitResponse(BaseModel):
    is_correct: bool
    correct_answer: str
    score: int
    progress: str


class SummaryResponse(BaseModel):
    session_id: int
    deck_name: str
    score: int
    total_questions: int
    percentage: float
    wrong_words: List[str]
    created_at: datetime
    completed_at: Optional[datetime]
