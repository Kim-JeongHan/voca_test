# -*- coding: utf-8 -*-
from pydantic_settings import BaseSettings
from typing import Optional
from functools import cached_property


class Settings(BaseSettings):
    # Database (DATABASE_PUBLIC_URL takes priority for Railway external access)
    database_public_url: Optional[str] = None
    database_url: str = "sqlite:///./voca.db"

    @cached_property
    def db_url(self) -> str:
        """Use public URL if available (Railway), otherwise standard DATABASE_URL."""
        return self.database_public_url or self.database_url

    # API Keys
    elevenlabs_api_key: Optional[str] = None

    # CORS (comma-separated in .env, stored as string)
    cors_origins_str: str = "http://localhost:3000,http://127.0.0.1:3000"

    # App
    app_name: str = "Voca Test API"
    debug: bool = True

    # JWT Authentication
    jwt_secret_key: str = "change-me-in-production-use-env-var"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    @cached_property
    def cors_origins(self) -> list[str]:
        """Parse comma-separated CORS origins into a list."""
        return [
            origin.strip()
            for origin in self.cors_origins_str.split(",")
            if origin.strip()
        ]

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
