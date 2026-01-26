# -*- coding: utf-8 -*-
from pydantic_settings import BaseSettings
from typing import Optional
from functools import cached_property


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./voca.db"

    # API Keys
    elevenlabs_api_key: Optional[str] = None

    # CORS (comma-separated in .env, stored as string)
    cors_origins_str: str = "http://localhost:3000,http://127.0.0.1:3000"

    # App
    app_name: str = "Voca Test API"
    debug: bool = True

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
