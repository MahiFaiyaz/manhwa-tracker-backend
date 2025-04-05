from fastapi import Header
from typing import Optional
from app.core.exceptions import AuthenticationError
from app.services.manhwa_database_manager import ManhwaDatabaseManager


def get_bearer_token(required: bool = True):
    async def _get_token(auth_token: Optional[str] = Header(None)) -> Optional[str]:
        if not auth_token:
            if required:
                raise AuthenticationError("Authorization token is required")
            return None

        if not auth_token.startswith("Bearer "):
            raise AuthenticationError(
                "Invalid token format. Expected 'Bearer <token>'."
            )

        return auth_token.split("Bearer ")[1]

    return _get_token


def get_db_manager():
    return ManhwaDatabaseManager()
