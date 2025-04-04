from fastapi import APIRouter, Depends, Header
from typing import List
from app.services.manhwa_database_manager import ManhwaDatabaseManager
from app.schemas.auth import UserSignUp, UserLogin, TokenResponse
from app.schemas.manhwa import (
    UserProgressCreate,
    UserProgressUpdate,
    UserProgress,
    ReadingStatus,
)
from app.core.exceptions import DatabaseError, AuthenticationError, ValidationError

router = APIRouter(tags=["users"])


def get_db_manager():
    return ManhwaDatabaseManager()


@router.post("/signup", response_model=TokenResponse)
async def sign_up(
    user: UserSignUp, db: ManhwaDatabaseManager = Depends(get_db_manager)
):
    try:
        response = db.sign_up(user.email, user.password)
        return TokenResponse(
            access_token=response["session"]["access_token"],
            refresh_token=response["session"]["refresh_token"],
        )
    except Exception as e:
        raise ValidationError(f"Sign up failed: {str(e)}")


@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin, db: ManhwaDatabaseManager = Depends(get_db_manager)):
    try:
        response = db.login(user.email, user.password)
        return response
    except Exception as e:
        raise AuthenticationError(f"Login failed: {str(e)}")


@router.post("/progress")
async def add_progress(
    progress: UserProgressCreate,
    auth_token: str = Header(None),
    db: ManhwaDatabaseManager = Depends(get_db_manager),
):
    if not auth_token:
        raise AuthenticationError("Authorization token is required")

    try:
        access_token = auth_token.split("Bearer ")[1]
    except IndexError:
        raise AuthenticationError("Invalid token format")

    try:
        return db.add_progress(
            access_token,
            progress.manhwa_id,
            progress.current_chapter,
            progress.reading_status,
        )
    except Exception as e:
        raise DatabaseError(f"Failed to add progress: {str(e)}")


@router.patch("/progress/{manhwa_id}")
async def update_progress(
    manhwa_id: int,
    progress: UserProgressUpdate,
    auth_token: str = Header(None),
    db: ManhwaDatabaseManager = Depends(get_db_manager),
):
    if not auth_token:
        raise AuthenticationError("Authorization token is required")

    try:
        access_token = auth_token.split("Bearer ")[1]
    except IndexError:
        raise AuthenticationError("Invalid token format")

    try:
        return db.update_progress(
            access_token, manhwa_id, progress.current_chapter, progress.reading_status
        )
    except Exception as e:
        raise DatabaseError(f"Failed to update progress: {str(e)}")


@router.get("/progress", response_model=List[UserProgress])
async def get_user_progress(
    auth_token: str = Header(None), db: ManhwaDatabaseManager = Depends(get_db_manager)
):
    if not auth_token:
        raise AuthenticationError("Authorization token is required")

    try:
        access_token = auth_token.split("Bearer ")[1]
    except IndexError:
        raise AuthenticationError("Invalid token format")

    try:
        return db.get_user_progress(access_token)
    except Exception as e:
        raise DatabaseError(f"Failed to get user progress: {str(e)}")


@router.get("/progress/{manhwa_id}", response_model=List[UserProgress])
async def get_manhwa_progress(
    manhwa_id: str, db: ManhwaDatabaseManager = Depends(get_db_manager)
):
    try:
        return db.get_manhwa_progress(manhwa_id)
    except Exception as e:
        raise DatabaseError(f"Failed to get manhwa progress: {str(e)}")
