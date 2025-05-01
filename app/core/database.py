from supabase import create_client, Client
from app.core.settings import get_settings
from app.core.logging import get_logger
from contextlib import contextmanager
from typing import Generator

logger = get_logger("database")
settings = get_settings()


@contextmanager
def get_db() -> Generator[Client, None, None]:
    """Get a fresh Supabase client per request."""
    try:
        client = create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)
        yield client
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise
