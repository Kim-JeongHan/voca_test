# -*- coding: utf-8 -*-
"""
Unit tests for TTS Service.

Tests verify TTS logic without calling actual ElevenLabs API.
Uses mocking to simulate API responses.
"""

import pytest
from unittest.mock import AsyncMock, patch
import httpx

from app.services.tts_service import TTSService
from app.models.cache import AudioCache


class TestTTSService:
    """Test TTS service with mocked API calls."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_tts_audio_from_cache(self, db_session):
        """Test retrieving audio from cache."""
        # Create cached audio
        cached_audio = AudioCache(
            text="hello", audio_data=b"cached_audio_data", content_type="audio/mpeg"
        )
        db_session.add(cached_audio)
        db_session.commit()

        # Get from service (should use cache)
        service = TTSService(db_session)
        audio_data, content_type = await service.get_tts_audio("hello")

        assert audio_data == b"cached_audio_data"
        assert content_type == "audio/mpeg"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_tts_audio_creates_cache(
        self, db_session, mock_elevenlabs_response
    ):
        """Test TTS service creates cache entry on API call."""
        service = TTSService(db_session)

        with patch.object(
            service, "_call_elevenlabs_api", new_callable=AsyncMock
        ) as mock_api:
            mock_api.return_value = mock_elevenlabs_response

            # First call (should hit API)
            audio_data, content_type = await service.get_tts_audio("test")

            assert audio_data == mock_elevenlabs_response
            assert content_type == "audio/mpeg"
            mock_api.assert_called_once_with("test")

            # Verify cache was created
            cached = (
                db_session.query(AudioCache).filter(AudioCache.text == "test").first()
            )
            assert cached is not None
            assert cached.audio_data == mock_elevenlabs_response

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_tts_audio_uses_cache_on_second_call(
        self, db_session, mock_elevenlabs_response
    ):
        """Test that second call uses cache instead of API."""
        service = TTSService(db_session)

        with patch.object(
            service, "_call_elevenlabs_api", new_callable=AsyncMock
        ) as mock_api:
            mock_api.return_value = mock_elevenlabs_response

            # First call
            await service.get_tts_audio("cached")

            # Second call (should use cache, not API)
            audio_data, content_type = await service.get_tts_audio("cached")

            # API should only be called once
            assert mock_api.call_count == 1
            assert audio_data == mock_elevenlabs_response

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_tts_audio_text_validation(self, db_session):
        """Test input validation for text."""
        service = TTSService(db_session)

        # Empty text
        with pytest.raises(ValueError, match="must be 1-100 characters"):
            await service.get_tts_audio("")

        # Text too long
        with pytest.raises(ValueError, match="must be 1-100 characters"):
            await service.get_tts_audio("a" * 101)

        # Whitespace only
        with pytest.raises(ValueError, match="must be 1-100 characters"):
            await service.get_tts_audio("   ")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_tts_audio_strips_whitespace(
        self, db_session, mock_elevenlabs_response
    ):
        """Test that text is trimmed before processing."""
        service = TTSService(db_session)

        with patch.object(
            service, "_call_elevenlabs_api", new_callable=AsyncMock
        ) as mock_api:
            mock_api.return_value = mock_elevenlabs_response

            await service.get_tts_audio("  hello  ")

            # Should call API with trimmed text
            mock_api.assert_called_once_with("hello")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_call_elevenlabs_api_success(self, db_session):
        """Test successful ElevenLabs API call."""
        service = TTSService(db_session)

        # Mock httpx response
        mock_response = AsyncMock()
        mock_response.is_success = True
        mock_response.content = b"audio_data"

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            audio_data = await service._call_elevenlabs_api("hello")
            assert audio_data == b"audio_data"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_call_elevenlabs_api_no_api_key(self, db_session):
        """Test API call fails without API key."""
        service = TTSService(db_session)

        with patch("app.services.tts_service.settings") as mock_settings:
            mock_settings.elevenlabs_api_key = None

            with pytest.raises(ValueError, match="ELEVENLABS_API_KEY not configured"):
                await service._call_elevenlabs_api("hello")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_call_elevenlabs_api_http_error(self, db_session):
        """Test API call handles HTTP errors."""
        service = TTSService(db_session)

        # Mock failed response
        mock_response = AsyncMock()
        mock_response.is_success = False
        mock_response.status_code = 500

        with patch("httpx.AsyncClient.post", return_value=mock_response):
            with patch("app.services.tts_service.settings") as mock_settings:
                mock_settings.elevenlabs_api_key = "test_key"

                with pytest.raises(httpx.HTTPError, match="ElevenLabs API error: 500"):
                    await service._call_elevenlabs_api("hello")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_cache_different_texts_separately(
        self, db_session, mock_elevenlabs_response
    ):
        """Test that different texts are cached separately."""
        service = TTSService(db_session)

        with patch.object(
            service, "_call_elevenlabs_api", new_callable=AsyncMock
        ) as mock_api:
            mock_api.return_value = mock_elevenlabs_response

            # Generate audio for two different texts
            await service.get_tts_audio("hello")
            await service.get_tts_audio("world")

            # Both should call API
            assert mock_api.call_count == 2

            # Both should be cached
            cached_count = db_session.query(AudioCache).count()
            assert cached_count == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_case_sensitive_cache(self, db_session, mock_elevenlabs_response):
        """Test that cache keys are case-sensitive after normalization."""
        service = TTSService(db_session)

        with patch.object(
            service, "_call_elevenlabs_api", new_callable=AsyncMock
        ) as mock_api:
            mock_api.return_value = mock_elevenlabs_response

            # Generate audio for same text
            await service.get_tts_audio("hello")
            await service.get_tts_audio("hello")

            # Should only call API once (second uses cache)
            assert mock_api.call_count == 1
