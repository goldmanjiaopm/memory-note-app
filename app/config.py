import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

# Load environment variables from .env file
load_dotenv()

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# Environment
ENV = os.getenv("ENV", "development")
DEBUG = os.getenv("DEBUG", "true").lower() == "true"

# Database
DEFAULT_DB_URL = f"sqlite+aiosqlite:///{DATA_DIR}/notes.db"
DATABASE_URL = os.getenv("DATABASE_URL", DEFAULT_DB_URL)

# API configuration
API_V1_PREFIX = "/api/v1"

# Vector store settings
VECTOR_STORE_DIR = DATA_DIR / "vector_store"
VECTOR_STORE_DIR.mkdir(exist_ok=True)


class Settings(BaseSettings):
    """Application settings."""

    DATABASE_URL: str = DATABASE_URL
    VECTOR_STORE_DIR: Path = VECTOR_STORE_DIR

    class Config:
        """Pydantic config."""

        env_file = ".env"


# Create global settings object
settings = Settings()
