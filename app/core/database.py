from supabase import create_client, Client
from app.core.settings import get_settings
from app.core.logging import get_logger
from contextlib import contextmanager
from typing import Generator

logger = get_logger("database")
settings = get_settings()


class Database:
    """Database connection manager."""

    _instance = None
    _client = None

    def __new__(cls):
        if cls._instance is None:
            logger.info("Initializing database connection")
            cls._instance = super().__new__(cls)
            cls._instance._client = create_client(
                settings.SUPABASE_URL, settings.SUPABASE_KEY
            )
        return cls._instance

    @property
    def client(self) -> Client:
        """Get database client."""
        return self._client


@contextmanager
def get_db() -> Generator[Client, None, None]:
    """Get database connection with context manager."""
    db = Database()
    try:
        yield db.client
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        raise
