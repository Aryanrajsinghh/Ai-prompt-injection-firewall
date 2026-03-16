"""Configuration management for the prompt firewall."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    """Application settings loaded from environment variables."""

    ai_detection_api_url: str = os.getenv(
        "AI_DETECTION_API_URL",
        "http://127.0.0.1:8001/ai_detect",
    )
    database_path: str = os.getenv(
        "DATABASE_PATH",
        str(BASE_DIR / "prompt_firewall.db"),
    )


settings = Settings()
