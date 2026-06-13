# -*- coding: utf-8 -*-
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    deepseek_api_key: str = ""  # 通过 .env 注入，源码中不保留任何密钥
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"  # legacy / fallback default
    deepseek_model_simple: str = "deepseek-v4-flash"  # 简易模式 (快)
    deepseek_model_detail: str = "deepseek-v4-pro"    # 详细模式 (全)
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
