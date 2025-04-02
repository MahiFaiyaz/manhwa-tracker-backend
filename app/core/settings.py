from pydantic import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Application settings."""

    # API Configuration
    API_TITLE: str = "Manhwa Finder API"
    API_DESCRIPTION: str = "An API for fetching and filtering manhwa details"
    API_VERSION: str = "1.0"

    # Database Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str

    # Google Sheets Configuration
    GOOGLE_SHEETS_API_KEY: str
    SHEETS_ID: str = "1ZluFOVtJCv-cQLXWhmCLNoZFIMLV0eTrqozwyEb1zw8"

    # External API Configuration
    MAL_CLIENT_ID: str

    # Authentication Configuration
    SYNC_API_KEY: str

    # Rate Limiting
    DEFAULT_RATE_LIMIT: str = "60 per minute"
    AUTH_RATE_LIMIT: str = "20 per minute"

    class Config:
        env_file = ".env"
        case_sensitive = True


@lru_cache()
def get_settings():
    """Create cached settings instance."""
    return Settings()
