"""
TTS Service - ElevenLabs API Proxy

Handles text-to-speech conversion using ElevenLabs API.
Implements caching to reduce API costs.
"""

import httpx
from sqlalchemy.orm import Session
from app.config import settings
from app.models.cache import AudioCache


# ElevenLabs Configuration
VOICE_ID = 'JBFqnCBsd6RMkjVDRZzb'  # George - English
MODEL_ID = 'eleven_multilingual_v2'
MAX_TEXT_LENGTH = 100
API_TIMEOUT_MS = 8000


class TTSService:
    """TTS service for converting text to speech."""

    def __init__(self, db: Session):
        self.db = db

    async def get_tts_audio(self, text: str) -> tuple[bytes, str]:
        """
        Get TTS audio for the given text.
        Checks cache first, then calls ElevenLabs API if needed.

        Args:
            text: Text to convert to speech

        Returns:
            Tuple of (audio_data: bytes, content_type: str)

        Raises:
            ValueError: If text is invalid
            httpx.HTTPError: If API call fails
        """
        # Validate input
        trimmed_text = text.strip()
        if not trimmed_text or len(trimmed_text) > MAX_TEXT_LENGTH:
            raise ValueError(f"Text must be 1-{MAX_TEXT_LENGTH} characters")

        # Check cache
        cached = self.db.query(AudioCache).filter(
            AudioCache.text == trimmed_text
        ).first()

        if cached:
            return cached.audio_data, cached.content_type

        # Call ElevenLabs API
        audio_data = await self._call_elevenlabs_api(trimmed_text)

        # Save to cache
        cache_entry = AudioCache(
            text=trimmed_text,
            audio_data=audio_data,
            content_type="audio/mpeg"
        )
        self.db.add(cache_entry)
        self.db.commit()

        return audio_data, "audio/mpeg"

    async def _call_elevenlabs_api(self, text: str) -> bytes:
        """
        Call ElevenLabs API to generate speech.

        Args:
            text: Text to convert

        Returns:
            Audio data as bytes

        Raises:
            httpx.HTTPError: If API call fails
        """
        if not settings.elevenlabs_api_key:
            raise ValueError("ELEVENLABS_API_KEY not configured")

        url = f"https://api.elevenlabs.io/v1/text-to-speech/{VOICE_ID}"

        async with httpx.AsyncClient(timeout=API_TIMEOUT_MS / 1000) as client:
            response = await client.post(
                url,
                headers={
                    'Accept': 'audio/mpeg',
                    'Content-Type': 'application/json',
                    'xi-api-key': settings.elevenlabs_api_key,
                },
                json={
                    'text': text,
                    'model_id': MODEL_ID,
                    'voice_settings': {
                        'stability': 0.5,
                        'similarity_boost': 0.75,
                    },
                }
            )

            if not response.is_success:
                raise httpx.HTTPError(f"ElevenLabs API error: {response.status_code}")

            return response.content
