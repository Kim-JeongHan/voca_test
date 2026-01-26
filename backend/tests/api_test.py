# -*- coding: utf-8 -*-
"""
API endpoint integration tests.

Tests verify API behavior with real database but mocked external services.
"""

import pytest
import io
from unittest.mock import patch, AsyncMock

from app.models.deck import Deck, Word


class TestHealthEndpoints:
    """Test health check endpoints."""

    @pytest.mark.api
    def test_root_endpoint(self, client):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Voca Test API"
        assert "version" in data

    @pytest.mark.api
    def test_health_check(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestDecksAPI:
    """Test decks API endpoints."""

    @pytest.mark.api
    def test_list_decks_empty(self, client):
        """Test listing decks when database is empty."""
        response = client.get("/api/v1/decks")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.api
    def test_list_decks(self, client, create_test_deck):
        """Test listing decks."""
        response = client.get("/api/v1/decks")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Deck"
        assert data[0]["word_count"] == 3

    @pytest.mark.api
    def test_get_deck_by_id(self, client, create_test_deck):
        """Test getting specific deck with words."""
        response = client.get(f"/api/v1/decks/{create_test_deck.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Deck"
        assert len(data["words"]) == 3
        assert data["words"][0]["word"] == "escape"

    @pytest.mark.api
    def test_get_deck_not_found(self, client):
        """Test getting non-existent deck."""
        response = client.get("/api/v1/decks/999")
        assert response.status_code == 404

    @pytest.mark.api
    def test_upload_deck_csv(self, client, auth_headers):
        """Test uploading deck via CSV file (requires auth)."""
        csv_content = "escape,탈출하다\nabandon,버리다\n"
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}
        data = {"name": "Uploaded Deck", "description": "Test upload"}

        response = client.post(
            "/api/v1/decks/upload", files=files, data=data, headers=auth_headers
        )
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "Uploaded Deck"
        assert result["word_count"] == 2

    @pytest.mark.api
    def test_upload_deck_unauthorized(self, client):
        """Test uploading deck without auth returns 403."""
        csv_content = "escape,탈출하다\n"
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}

        response = client.post("/api/v1/decks/upload", files=files)
        # HTTPBearer returns 403 when no credentials provided
        assert response.status_code == 403

    @pytest.mark.api
    def test_upload_deck_invalid_csv(self, client, auth_headers):
        """Test uploading invalid CSV."""
        csv_content = "invalid,csv,too,many,columns\n"
        files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}

        response = client.post(
            "/api/v1/decks/upload", files=files, headers=auth_headers
        )
        # Should still succeed but ignore invalid rows
        assert response.status_code in [200, 400]

    @pytest.mark.api
    def test_delete_deck(self, client, create_user_deck, auth_headers):
        """Test deleting own deck (requires auth)."""
        response = client.delete(
            f"/api/v1/decks/{create_user_deck.id}", headers=auth_headers
        )
        assert response.status_code == 200

        # Verify deleted
        get_response = client.get(f"/api/v1/decks/{create_user_deck.id}")
        assert get_response.status_code == 404

    @pytest.mark.api
    def test_delete_deck_unauthorized(self, client, create_test_deck):
        """Test deleting deck without auth returns 403."""
        response = client.delete(f"/api/v1/decks/{create_test_deck.id}")
        # HTTPBearer returns 403 when no credentials provided
        assert response.status_code == 403

    @pytest.mark.api
    def test_delete_deck_forbidden(self, client, create_test_deck, auth_headers):
        """Test deleting other user's deck returns 403."""
        # create_test_deck has no user_id (public deck), user can't delete it
        response = client.delete(
            f"/api/v1/decks/{create_test_deck.id}", headers=auth_headers
        )
        assert response.status_code == 403

    @pytest.mark.api
    def test_get_deck_words(self, client, create_test_deck):
        """Test getting words from a deck."""
        response = client.get(f"/api/v1/decks/{create_test_deck.id}/words")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert data[0]["word"] == "escape"
        assert data[1]["word"] == "abandon"


class TestSessionAPI:
    """Test session API endpoints."""

    @pytest.mark.api
    def test_start_session(self, client, create_test_deck):
        """Test starting a new session."""
        request_data = {
            "deck_id": create_test_deck.id,
            "word_indices": None,
            "is_wrong_only": False,
        }

        response = client.post("/api/v1/session/start", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["deck_id"] == create_test_deck.id
        assert data["total_questions"] == 3
        assert data["current_index"] == 0
        assert data["score"] == 0
        assert data["is_completed"] is False

    @pytest.mark.api
    def test_start_session_with_indices(self, client, create_test_deck):
        """Test starting session with specific word indices."""
        request_data = {
            "deck_id": create_test_deck.id,
            "word_indices": [0, 2],
            "is_wrong_only": False,
        }

        response = client.post("/api/v1/session/start", json=request_data)
        assert response.status_code == 200
        data = response.json()
        assert data["total_questions"] == 2

    @pytest.mark.api
    def test_start_session_invalid_deck(self, client):
        """Test starting session with non-existent deck."""
        request_data = {"deck_id": 999, "word_indices": None, "is_wrong_only": False}

        response = client.post("/api/v1/session/start", json=request_data)
        assert response.status_code == 404

    @pytest.mark.api
    def test_get_prompt(self, client, create_test_deck):
        """Test getting question prompt."""
        # Start session
        session_response = client.post(
            "/api/v1/session/start",
            json={
                "deck_id": create_test_deck.id,
                "word_indices": None,
                "is_wrong_only": False,
            },
        )
        session_id = session_response.json()["id"]

        # Get prompt
        response = client.get(f"/api/v1/session/{session_id}/prompt")
        assert response.status_code == 200
        data = response.json()
        assert data["word"] == "escape"
        assert data["current"] == 1
        assert data["total"] == 3
        assert data["progress"] == "1/3"

    @pytest.mark.api
    def test_submit_answer(self, client, create_test_deck):
        """Test submitting an answer."""
        # Start session
        session_response = client.post(
            "/api/v1/session/start",
            json={
                "deck_id": create_test_deck.id,
                "word_indices": None,
                "is_wrong_only": False,
            },
        )
        session_id = session_response.json()["id"]

        # Submit correct answer
        submit_data = {"answer": "탈출하다", "hint_used": 0}
        response = client.post(f"/api/v1/session/{session_id}/submit", json=submit_data)
        assert response.status_code == 200
        data = response.json()
        assert data["is_correct"] is True
        assert data["score"] == 1

    @pytest.mark.api
    def test_submit_wrong_answer(self, client, create_test_deck):
        """Test submitting wrong answer."""
        # Start session
        session_response = client.post(
            "/api/v1/session/start",
            json={
                "deck_id": create_test_deck.id,
                "word_indices": None,
                "is_wrong_only": False,
            },
        )
        session_id = session_response.json()["id"]

        # Submit wrong answer
        submit_data = {"answer": "wrong_answer", "hint_used": 0}
        response = client.post(f"/api/v1/session/{session_id}/submit", json=submit_data)
        assert response.status_code == 200
        data = response.json()
        assert data["is_correct"] is False
        assert data["score"] == 0

    @pytest.mark.api
    def test_complete_session_flow(self, client, create_test_deck):
        """Test complete session from start to summary."""
        # Start session
        session_response = client.post(
            "/api/v1/session/start",
            json={
                "deck_id": create_test_deck.id,
                "word_indices": [0],  # Only one word
                "is_wrong_only": False,
            },
        )
        session_id = session_response.json()["id"]

        # Submit answer
        client.post(
            f"/api/v1/session/{session_id}/submit",
            json={"answer": "탈출하다", "hint_used": 0},
        )

        # Get summary
        response = client.get(f"/api/v1/session/{session_id}/summary")
        assert response.status_code == 200
        data = response.json()
        assert data["score"] == 1
        assert data["total_questions"] == 1
        assert data["percentage"] == 100.0

    @pytest.mark.api
    def test_get_wrong_words(self, client, create_test_deck):
        """Test getting wrong words from session."""
        # Start and complete session with wrong answer
        session_response = client.post(
            "/api/v1/session/start",
            json={
                "deck_id": create_test_deck.id,
                "word_indices": [0],
                "is_wrong_only": False,
            },
        )
        session_id = session_response.json()["id"]

        # Submit wrong answer
        client.post(
            f"/api/v1/session/{session_id}/submit",
            json={"answer": "wrong", "hint_used": 0},
        )

        # Get wrong words
        response = client.get(f"/api/v1/session/{session_id}/wrong")
        assert response.status_code == 200
        data = response.json()
        assert "escape" in data["wrong_words"]


class TestTTSAPI:
    """Test TTS API endpoints."""

    @pytest.mark.api
    @pytest.mark.external
    def test_tts_endpoint_mocked(self, client, mock_elevenlabs_response):
        """Test TTS endpoint with mocked API."""
        with patch(
            "app.services.tts_service.TTSService._call_elevenlabs_api",
            new_callable=AsyncMock,
        ) as mock_api:
            mock_api.return_value = mock_elevenlabs_response

            request_data = {"text": "hello"}
            response = client.post("/api/v1/tts", json=request_data)

            assert response.status_code == 200
            assert response.headers["content-type"] == "audio/mpeg"

    @pytest.mark.api
    def test_tts_endpoint_validation(self, client):
        """Test TTS endpoint input validation."""
        # Empty text - raises ValueError in service, returns 400
        response = client.post("/api/v1/tts", json={"text": ""})
        assert response.status_code == 400

        # Too long text - Pydantic validation returns 422
        response = client.post("/api/v1/tts", json={"text": "a" * 101})
        assert response.status_code == 422


class TestImageAPI:
    """Test Image API endpoints."""

    @pytest.mark.api
    def test_image_endpoint_disabled(self, client):
        """Test image endpoint is currently disabled (501 Not Implemented)."""
        # Image generation is disabled - returns 501
        request_data = {"word": "escape"}
        response = client.post("/api/v1/image", json=request_data)
        assert response.status_code == 501

    @pytest.mark.api
    def test_image_github_endpoint_disabled(self, client):
        """Test image GitHub commit endpoint is disabled (501 Not Implemented)."""
        response = client.post("/api/v1/image/github", json={"word": "escape"})
        assert response.status_code == 501
