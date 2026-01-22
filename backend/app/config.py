from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./voca.db"

    # API Keys
    elevenlabs_api_key: Optional[str] = None
    huggingface_api_key: Optional[str] = None
    github_token: Optional[str] = None

    # GitHub Config
    github_owner: str = ""
    github_repo: str = ""
    github_branch: str = "master"

    # CORS
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    # App
    app_name: str = "Voca Test API"
    debug: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
