"""
Unit tests for Image Service.

Tests verify image generation logic without calling actual HuggingFace API.
Uses mocking to simulate API responses.
"""

import pytest
from unittest.mock import AsyncMock, patch
import httpx
import base64

from app.services.image_service import ImageService
from app.models.cache import ImageCache


class TestImageService:
    """Test Image service with mocked API calls."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_image_from_cache(self, db_session):
        """Test retrieving image from cache."""
        # Create cached image
        cached_image = ImageCache(
            word="escape",
            image_data=b"cached_image_data",
            content_type="image/png",
            github_url="https://github.com/test/image.png"
        )
        db_session.add(cached_image)
        db_session.commit()

        # Get from service (should use cache)
        service = ImageService(db_session)
        image_data, content_type, github_url = await service.get_image("escape")

        assert image_data == b"cached_image_data"
        assert content_type == "image/png"
        assert github_url == "https://github.com/test/image.png"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_image_creates_cache(self, db_session, mock_huggingface_response):
        """Test image service creates cache entry on API call."""
        service = ImageService(db_session)

        with patch.object(service, '_call_huggingface_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_huggingface_response

            # First call (should hit API)
            image_data, content_type, github_url = await service.get_image("test")

            assert image_data == mock_huggingface_response
            assert content_type == "image/png"
            assert github_url is None  # Not committed yet
            mock_api.assert_called_once_with("test")

            # Verify cache was created
            cached = db_session.query(ImageCache).filter(ImageCache.word == "test").first()
            assert cached is not None
            assert cached.image_data == mock_huggingface_response

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_image_word_validation(self, db_session):
        """Test input validation for word."""
        service = ImageService(db_session)

        # Empty word
        with pytest.raises(ValueError, match="must be 1-50 characters"):
            await service.get_image("")

        # Word too long
        with pytest.raises(ValueError, match="must be 1-50 characters"):
            await service.get_image("a" * 51)

        # Whitespace only
        with pytest.raises(ValueError, match="must be 1-50 characters"):
            await service.get_image("   ")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_get_image_normalizes_word(self, db_session, mock_huggingface_response):
        """Test that word is normalized (lowercase, trimmed)."""
        service = ImageService(db_session)

        with patch.object(service, '_call_huggingface_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_huggingface_response

            # Test with uppercase and spaces
            await service.get_image("  ESCAPE  ")

            # Should cache with normalized word
            cached = db_session.query(ImageCache).filter(ImageCache.word == "escape").first()
            assert cached is not None

    @pytest.mark.unit
    def test_build_prompt(self, db_session):
        """Test prompt building for image generation."""
        service = ImageService(db_session)
        prompt = service._build_prompt("escape")

        assert "escape" in prompt
        assert "Surreal" in prompt
        assert "No text" in prompt

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_call_huggingface_api_success(self, db_session):
        """Test successful HuggingFace API call."""
        service = ImageService(db_session)

        # Mock httpx response
        mock_response = AsyncMock()
        mock_response.is_success = True
        mock_response.status_code = 200
        mock_response.content = b"image_data"

        with patch('httpx.AsyncClient.post', return_value=mock_response):
            image_data = await service._call_huggingface_api("escape")
            assert image_data == b"image_data"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_call_huggingface_api_no_api_key(self, db_session):
        """Test API call fails without API key."""
        service = ImageService(db_session)

        with patch('app.services.image_service.settings') as mock_settings:
            mock_settings.huggingface_api_key = None

            with pytest.raises(ValueError, match="HUGGINGFACE_API_KEY not configured"):
                await service._call_huggingface_api("escape")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_call_huggingface_api_model_loading(self, db_session):
        """Test handling of 503 model loading response."""
        service = ImageService(db_session)

        # Mock 503 response
        mock_response = AsyncMock()
        mock_response.is_success = False
        mock_response.status_code = 503

        with patch('httpx.AsyncClient.post', return_value=mock_response):
            with patch('app.services.image_service.settings') as mock_settings:
                mock_settings.huggingface_api_key = "test_key"

                with pytest.raises(httpx.HTTPError, match="Model is loading"):
                    await service._call_huggingface_api("escape")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_call_huggingface_api_http_error(self, db_session):
        """Test API call handles HTTP errors."""
        service = ImageService(db_session)

        # Mock failed response
        mock_response = AsyncMock()
        mock_response.is_success = False
        mock_response.status_code = 500

        with patch('httpx.AsyncClient.post', return_value=mock_response):
            with patch('app.services.image_service.settings') as mock_settings:
                mock_settings.huggingface_api_key = "test_key"

                with pytest.raises(httpx.HTTPError, match="HuggingFace API error: 500"):
                    await service._call_huggingface_api("escape")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_commit_to_github_success(self, db_session):
        """Test successful GitHub commit."""
        service = ImageService(db_session)
        test_image = b"test_image_data"

        # Mock GitHub API responses
        mock_check_response = AsyncMock()
        mock_check_response.status_code = 404  # File doesn't exist

        mock_put_response = AsyncMock()
        mock_put_response.is_success = True
        mock_put_response.json.return_value = {
            'content': {
                'html_url': 'https://github.com/user/repo/blob/master/docs/images/test.png'
            }
        }

        with patch('httpx.AsyncClient.get', return_value=mock_check_response):
            with patch('httpx.AsyncClient.put', return_value=mock_put_response):
                with patch('app.services.image_service.settings') as mock_settings:
                    mock_settings.github_token = "test_token"
                    mock_settings.github_owner = "user"
                    mock_settings.github_repo = "repo"
                    mock_settings.github_branch = "master"

                    url = await service.commit_to_github("test", test_image)

                    assert url == 'https://github.com/user/repo/blob/master/docs/images/test.png'

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_commit_to_github_no_token(self, db_session):
        """Test GitHub commit fails without token."""
        service = ImageService(db_session)

        with patch('app.services.image_service.settings') as mock_settings:
            mock_settings.github_token = None

            with pytest.raises(ValueError, match="GITHUB_TOKEN not configured"):
                await service.commit_to_github("test", b"data")

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_commit_to_github_updates_cache(self, db_session):
        """Test GitHub commit updates cache with URL."""
        service = ImageService(db_session)

        # Create cached image
        cached_image = ImageCache(
            word="test",
            image_data=b"test_data",
            content_type="image/png"
        )
        db_session.add(cached_image)
        db_session.commit()

        # Mock responses
        mock_check_response = AsyncMock()
        mock_check_response.status_code = 404

        mock_put_response = AsyncMock()
        mock_put_response.is_success = True
        mock_put_response.json.return_value = {
            'content': {
                'html_url': 'https://github.com/test/url.png'
            }
        }

        with patch('httpx.AsyncClient.get', return_value=mock_check_response):
            with patch('httpx.AsyncClient.put', return_value=mock_put_response):
                with patch('app.services.image_service.settings') as mock_settings:
                    mock_settings.github_token = "test_token"
                    mock_settings.github_owner = "user"
                    mock_settings.github_repo = "repo"

                    await service.commit_to_github("test", b"test_data")

                    # Verify cache was updated
                    updated = db_session.query(ImageCache).filter(ImageCache.word == "test").first()
                    assert updated.github_url == 'https://github.com/test/url.png'

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_different_words_cached_separately(self, db_session, mock_huggingface_response):
        """Test that different words are cached separately."""
        service = ImageService(db_session)

        with patch.object(service, '_call_huggingface_api', new_callable=AsyncMock) as mock_api:
            mock_api.return_value = mock_huggingface_response

            # Generate images for two different words
            await service.get_image("escape")
            await service.get_image("abandon")

            # Both should call API
            assert mock_api.call_count == 2

            # Both should be cached
            cached_count = db_session.query(ImageCache).count()
            assert cached_count == 2
