"""
Image Service - HuggingFace Stable Diffusion Proxy

Handles image generation using HuggingFace Stable Diffusion API.
Implements caching and optional GitHub storage.
"""

import httpx
import base64
from sqlalchemy.orm import Session
from app.config import settings
from app.models.cache import ImageCache


# HuggingFace Configuration
MODEL_ID = 'runwayml/stable-diffusion-v1-5'
API_URL = f'https://router.huggingface.co/models/{MODEL_ID}'
MAX_WORD_LENGTH = 50
API_TIMEOUT_MS = 30000  # 30 seconds


class ImageService:
    """Image generation service using HuggingFace Stable Diffusion."""

    def __init__(self, db: Session):
        self.db = db

    async def get_image(self, word: str) -> tuple[bytes, str, str | None]:
        """
        Get association image for the given word.
        Checks cache first, then calls HuggingFace API if needed.

        Args:
            word: Word to generate image for

        Returns:
            Tuple of (image_data: bytes, content_type: str, github_url: str | None)

        Raises:
            ValueError: If word is invalid
            httpx.HTTPError: If API call fails
        """
        # Validate input
        trimmed_word = word.strip().lower()
        if not trimmed_word or len(trimmed_word) > MAX_WORD_LENGTH:
            raise ValueError(f"Word must be 1-{MAX_WORD_LENGTH} characters")

        # Check cache
        cached = self.db.query(ImageCache).filter(
            ImageCache.word == trimmed_word
        ).first()

        if cached:
            return cached.image_data, cached.content_type, cached.github_url

        # Call HuggingFace API
        image_data = await self._call_huggingface_api(trimmed_word)

        # Save to cache
        cache_entry = ImageCache(
            word=trimmed_word,
            image_data=image_data,
            content_type="image/png",
            github_url=None
        )
        self.db.add(cache_entry)
        self.db.commit()

        return image_data, "image/png", None

    async def _call_huggingface_api(self, word: str) -> bytes:
        """
        Call HuggingFace API to generate image.

        Args:
            word: Word to generate image for

        Returns:
            Image data as bytes

        Raises:
            httpx.HTTPError: If API call fails
        """
        if not settings.huggingface_api_key:
            raise ValueError("HUGGINGFACE_API_KEY not configured")

        prompt = self._build_prompt(word)

        async with httpx.AsyncClient(timeout=API_TIMEOUT_MS / 1000) as client:
            response = await client.post(
                API_URL,
                headers={
                    'Authorization': f'Bearer {settings.huggingface_api_key}',
                    'Content-Type': 'application/json',
                },
                json={
                    'inputs': prompt,
                    'parameters': {
                        'negative_prompt': 'text, letters, words, writing, numbers, watermark, signature, logo, blurry, low quality',
                        'num_inference_steps': 25,
                        'guidance_scale': 7.5,
                        'width': 512,
                        'height': 512,
                    },
                    'options': {
                        'wait_for_model': True,
                    },
                }
            )

            if response.status_code == 503:
                # Model is loading
                raise httpx.HTTPError("Model is loading, please retry in a few seconds")

            if not response.is_success:
                raise httpx.HTTPError(f"HuggingFace API error: {response.status_code}")

            return response.content

    def _build_prompt(self, word: str) -> str:
        """
        Build prompt for Stable Diffusion image generation.

        Args:
            word: Word to build prompt for

        Returns:
            Prompt string
        """
        return (
            f"Surreal educational illustration representing '{word}', "
            f"vibrant colors, conceptual art, symbolic imagery, "
            f"high quality, detailed. No text, no letters, no words."
        )

    async def commit_to_github(self, word: str, image_data: bytes) -> str:
        """
        Commit image to GitHub repository.

        Args:
            word: Word identifier
            image_data: Image binary data

        Returns:
            URL to committed file

        Raises:
            httpx.HTTPError: If GitHub API call fails
        """
        if not settings.github_token:
            raise ValueError("GITHUB_TOKEN not configured")

        # Encode image to base64
        image_base64 = base64.b64encode(image_data).decode('utf-8')

        # Prepare file path
        file_path = f"docs/images/{word}.png"

        # GitHub API URL
        url = f"https://api.github.com/repos/{settings.github_owner}/{settings.github_repo}/contents/{file_path}"

        # Check if file exists
        async with httpx.AsyncClient() as client:
            check_response = await client.get(
                url,
                headers={
                    'Authorization': f'token {settings.github_token}',
                    'Accept': 'application/vnd.github.v3+json',
                }
            )

            sha = None
            if check_response.status_code == 200:
                sha = check_response.json()['sha']

            # Create or update file
            commit_message = f"Add association image: {word}"

            payload = {
                'message': commit_message,
                'content': image_base64,
                'branch': settings.github_branch,
            }

            if sha:
                payload['sha'] = sha

            response = await client.put(
                url,
                headers={
                    'Authorization': f'token {settings.github_token}',
                    'Accept': 'application/vnd.github.v3+json',
                },
                json=payload
            )

            if not response.is_success:
                raise httpx.HTTPError(f"GitHub API error: {response.status_code}")

            result = response.json()
            github_url = result['content']['html_url']

            # Update cache with GitHub URL
            cached = self.db.query(ImageCache).filter(
                ImageCache.word == word
            ).first()
            if cached:
                cached.github_url = github_url
                self.db.commit()

            return github_url
