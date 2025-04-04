from fastapi import APIRouter, Depends, Header
from typing import List
from app.services.manhwa_database_manager import ManhwaDatabaseManager
from app.schemas.auth import UserSignUp, UserLogin, TokenResponse
from app.schemas.manhwa import UserProgressCreate, UserProgress, ManhwaProgressResponse
from app.core.exceptions import DatabaseError, AuthenticationError, ValidationError

router = APIRouter(tags=["users"])


def get_db_manager():
    return ManhwaDatabaseManager()


@router.post("/signup")
async def sign_up(
    user: UserSignUp, db: ManhwaDatabaseManager = Depends(get_db_manager)
):
    # Password is already validated by the schema's validator
    try:
        response = db.sign_up(user.email, user.password)
        if not response.user.user_metadata:
            return {"message": f"User with email {user.email} already exists."}
        return {
            "message": f"User signed up successfully. Confirmation email sent to {user.email}."
        }
    except Exception as e:
        raise ValidationError(f"Sign up failed: {str(e)}")


@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin, db: ManhwaDatabaseManager = Depends(get_db_manager)):
    try:
        response = db.login(user.email, user.password)
        return TokenResponse(
            access_token=response["access_token"],
            refresh_token=response["refresh_token"],
        )
    except Exception as e:
        raise AuthenticationError(f"Login failed: {str(e)}")


@router.post("/progress", response_model=List[UserProgress])
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


@router.get("/progress/{manhwa_id}", response_model=ManhwaProgressResponse)
async def get_manhwa_progress(
    manhwa_id: int, db: ManhwaDatabaseManager = Depends(get_db_manager)
):
    try:
        return db.get_manhwa_progress(manhwa_id)
    except Exception as e:
        raise DatabaseError(f"Failed to get manhwa progress: {str(e)}")
