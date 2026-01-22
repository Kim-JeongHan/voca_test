from pydantic import BaseModel, Field
from typing import Optional


class TTSRequest(BaseModel):
    text: str = Field(..., max_length=100, description="Text to convert to speech")


class TTSResponse(BaseModel):
    audio_url: Optional[str] = Field(None, description="URL to audio file if cached")
    error: Optional[str] = Field(None, description="Error message if any")
