# -*- coding: utf-8 -*-
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    deepseek_api_key: str = "sk-3e7ab7379d5443dfb4f374d0fbc7b114"
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    db_path: str = str(Path(__file__).parent / "projects.db")
    repos_dir: str = str(Path(__file__).parent / "repos")
    max_file_size: int = 200 * 1024
    max_total_size: int = 5 * 1024 * 1024

    # Auth
    jwt_secret: str = "change-me-in-prod-please-use-32-chars-min"
    jwt_algorithm: str = "HS256"
    access_token_ttl_min: int = 15
    refresh_token_ttl_days: int = 7

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()
