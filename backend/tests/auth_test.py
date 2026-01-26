# -*- coding: utf-8 -*-
"""
Authentication API tests.

Tests for user registration, login, and JWT token handling.
"""

import pytest
from unittest.mock import patch

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token,
)
from app.models.user import User


class TestPasswordHashing:
    """Test password hashing functions."""

    def test_hash_password(self):
        """Test password hashing produces valid hash."""
        password = "test_password_123"
        hashed = hash_password(password)

        assert hashed is not None
        assert hashed != password
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """Test verifying correct password."""
        password = "test_password_123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying incorrect password."""
        password = "test_password_123"
        hashed = hash_password(password)

        assert verify_password("wrong_password", hashed) is False

    def test_hash_password_different_each_time(self):
        """Test that same password produces different hashes (due to salt)."""
        password = "test_password_123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2
        # But both should verify correctly
        assert verify_password(password, hash1) is True
        assert verify_password(password, hash2) is True


class TestJWTToken:
    """Test JWT token functions."""

    def test_create_access_token(self):
        """Test creating JWT token."""
        user_id = 123
        token = create_access_token(user_id)

        assert token is not None
        assert len(token) > 0
        assert isinstance(token, str)

    def test_decode_access_token_valid(self):
        """Test decoding valid JWT token."""
        user_id = 123
        token = create_access_token(user_id)
        decoded_id = decode_access_token(token)

        assert decoded_id == user_id

    def test_decode_access_token_invalid(self):
        """Test decoding invalid JWT token."""
        decoded_id = decode_access_token("invalid_token")
        assert decoded_id is None

    def test_decode_access_token_empty(self):
        """Test decoding empty token."""
        decoded_id = decode_access_token("")
        assert decoded_id is None


class TestAuthRegister:
    """Test user registration endpoint."""

    @pytest.mark.api
    def test_register_success(self, client):
        """Test successful user registration."""
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
        }

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201

        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"
        assert "id" in data
        assert "password" not in data
        assert "password_hash" not in data

    @pytest.mark.api
    def test_register_duplicate_username(self, client):
        """Test registration with duplicate username."""
        user_data = {
            "username": "testuser",
            "email": "test1@example.com",
            "password": "password123",
        }

        # First registration
        response1 = client.post("/api/v1/auth/register", json=user_data)
        assert response1.status_code == 201

        # Duplicate registration
        user_data["email"] = "test2@example.com"
        response2 = client.post("/api/v1/auth/register", json=user_data)
        assert response2.status_code == 400
        assert "Username already registered" in response2.json()["detail"]

    @pytest.mark.api
    def test_register_duplicate_email(self, client):
        """Test registration with duplicate email."""
        user_data1 = {
            "username": "testuser1",
            "email": "test@example.com",
            "password": "password123",
        }
        user_data2 = {
            "username": "testuser2",
            "email": "test@example.com",
            "password": "password123",
        }

        # First registration
        response1 = client.post("/api/v1/auth/register", json=user_data1)
        assert response1.status_code == 201

        # Duplicate email
        response2 = client.post("/api/v1/auth/register", json=user_data2)
        assert response2.status_code == 400
        assert "Email already registered" in response2.json()["detail"]

    @pytest.mark.api
    def test_register_without_email(self, client):
        """Test registration without email (optional)."""
        user_data = {"username": "testuser", "password": "password123"}

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 201

        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] is None

    @pytest.mark.api
    def test_register_missing_username(self, client):
        """Test registration without username."""
        user_data = {"email": "test@example.com", "password": "password123"}

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error

    @pytest.mark.api
    def test_register_missing_password(self, client):
        """Test registration without password."""
        user_data = {"username": "testuser", "email": "test@example.com"}

        response = client.post("/api/v1/auth/register", json=user_data)
        assert response.status_code == 422  # Validation error


class TestAuthLogin:
    """Test user login endpoint."""

    @pytest.mark.api
    def test_login_success(self, client):
        """Test successful login."""
        # Register first
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
        }
        client.post("/api/v1/auth/register", json=user_data)

        # Login
        login_data = {"username": "testuser", "password": "password123"}
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 200

        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "expires_in" in data

    @pytest.mark.api
    def test_login_wrong_password(self, client):
        """Test login with wrong password."""
        # Register first
        user_data = {"username": "testuser", "password": "password123"}
        client.post("/api/v1/auth/register", json=user_data)

        # Login with wrong password
        login_data = {"username": "testuser", "password": "wrongpassword"}
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

    @pytest.mark.api
    def test_login_nonexistent_user(self, client):
        """Test login with nonexistent user."""
        login_data = {"username": "nonexistent", "password": "password123"}
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 401
        assert "Invalid username or password" in response.json()["detail"]

    @pytest.mark.api
    def test_login_inactive_user(self, client, db_session):
        """Test login with inactive user."""
        # Create inactive user directly in DB
        user = User(
            username="inactiveuser",
            email="inactive@example.com",
            password_hash=hash_password("password123"),
            is_active=False,
        )
        db_session.add(user)
        db_session.commit()

        # Try to login
        login_data = {"username": "inactiveuser", "password": "password123"}
        response = client.post("/api/v1/auth/login", json=login_data)
        assert response.status_code == 403
        assert "inactive" in response.json()["detail"].lower()


class TestAuthMe:
    """Test current user endpoint."""

    @pytest.mark.api
    def test_me_authenticated(self, client):
        """Test getting current user when authenticated."""
        # Register and login
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
        }
        client.post("/api/v1/auth/register", json=user_data)

        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "password123"},
        )
        token = login_response.json()["access_token"]

        # Get me
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200

        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    @pytest.mark.api
    def test_me_unauthenticated(self, client):
        """Test getting current user without authentication."""
        response = client.get("/api/v1/auth/me")
        # HTTPBearer returns 403 when no credentials provided
        assert response.status_code == 403

    @pytest.mark.api
    def test_me_invalid_token(self, client):
        """Test getting current user with invalid token."""
        response = client.get(
            "/api/v1/auth/me", headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


class TestPasswordReset:
    """Test password reset endpoints."""

    @pytest.mark.api
    def test_request_password_reset(self, client):
        """Test requesting password reset."""
        # Register first
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password": "password123",
        }
        client.post("/api/v1/auth/register", json=user_data)

        # Request reset
        response = client.post(
            "/api/v1/auth/password-reset", json={"email": "test@example.com"}
        )
        assert response.status_code == 200
        assert "message" in response.json()

    @pytest.mark.api
    def test_request_password_reset_nonexistent_email(self, client):
        """Test requesting password reset for nonexistent email."""
        # Should still return 200 (don't reveal if email exists)
        response = client.post(
            "/api/v1/auth/password-reset", json={"email": "nonexistent@example.com"}
        )
        assert response.status_code == 200
        assert "message" in response.json()

    @pytest.mark.api
    def test_confirm_password_reset(self, client, db_session):
        """Test confirming password reset."""
        from datetime import datetime, timedelta, timezone
        import secrets

        # Create user with reset token
        reset_token = secrets.token_urlsafe(32)
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("oldpassword"),
            reset_token=reset_token,
            reset_token_expires=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        db_session.add(user)
        db_session.commit()

        # Confirm reset
        response = client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": reset_token, "new_password": "newpassword123"},
        )
        assert response.status_code == 200

        # Verify can login with new password
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "newpassword123"},
        )
        assert login_response.status_code == 200

    @pytest.mark.api
    def test_confirm_password_reset_invalid_token(self, client):
        """Test confirming password reset with invalid token."""
        response = client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": "invalid_token", "new_password": "newpassword123"},
        )
        assert response.status_code == 400

    @pytest.mark.api
    def test_confirm_password_reset_expired_token(self, client, db_session):
        """Test confirming password reset with expired token."""
        from datetime import datetime, timedelta, timezone
        import secrets

        # Create user with expired reset token
        reset_token = secrets.token_urlsafe(32)
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash=hash_password("oldpassword"),
            reset_token=reset_token,
            reset_token_expires=datetime.now(timezone.utc)
            - timedelta(hours=1),  # Expired
        )
        db_session.add(user)
        db_session.commit()

        # Try to confirm
        response = client.post(
            "/api/v1/auth/password-reset/confirm",
            json={"token": reset_token, "new_password": "newpassword123"},
        )
        assert response.status_code == 400
        assert "expired" in response.json()["detail"].lower()


class TestChangePassword:
    """Test change password endpoint."""

    @pytest.mark.api
    def test_change_password_success(self, client):
        """Test changing password when authenticated."""
        # Register and login
        user_data = {"username": "testuser", "password": "oldpassword123"}
        client.post("/api/v1/auth/register", json=user_data)

        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "oldpassword123"},
        )
        token = login_response.json()["access_token"]

        # Change password
        response = client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "oldpassword123",
                "new_password": "newpassword123",
            },
        )
        assert response.status_code == 200

        # Verify can login with new password
        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "newpassword123"},
        )
        assert login_response.status_code == 200

    @pytest.mark.api
    def test_change_password_wrong_current(self, client):
        """Test changing password with wrong current password."""
        # Register and login
        user_data = {"username": "testuser", "password": "oldpassword123"}
        client.post("/api/v1/auth/register", json=user_data)

        login_response = client.post(
            "/api/v1/auth/login",
            json={"username": "testuser", "password": "oldpassword123"},
        )
        token = login_response.json()["access_token"]

        # Try to change password with wrong current
        response = client.post(
            "/api/v1/auth/change-password",
            headers={"Authorization": f"Bearer {token}"},
            json={
                "current_password": "wrongpassword",
                "new_password": "newpassword123",
            },
        )
        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"].lower()

    @pytest.mark.api
    def test_change_password_unauthenticated(self, client):
        """Test changing password without authentication."""
        response = client.post(
            "/api/v1/auth/change-password",
            json={"current_password": "oldpassword", "new_password": "newpassword"},
        )
        # HTTPBearer returns 403 when no credentials provided
        assert response.status_code == 403
