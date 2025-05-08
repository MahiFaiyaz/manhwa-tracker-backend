from fastapi import APIRouter, Depends
from typing import List
from app.services.manhwa_auth_manager import UserAuthManager
from app.schemas.auth import UserSignUp, UserLogin, TokenResponse
from app.schemas.manhwa import UserProgress, ManhwaWithProgress
from app.core.exceptions import DatabaseError, AuthenticationError, ValidationError
from app.core.dependencies import get_bearer_token, get_auth_manager
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["users"])


@router.post("/signup")
async def sign_up(user: UserSignUp, db: UserAuthManager = Depends(get_auth_manager)):
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
async def login(user: UserLogin, db: UserAuthManager = Depends(get_auth_manager)):
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
    progress: UserProgress,
    access_token: str = Depends(get_bearer_token(required=True)),
    db: UserAuthManager = Depends(get_auth_manager),
):
    try:
        return db.add_progress(
            access_token,
            progress.manhwa_id,
            progress.current_chapter,
            progress.reading_status,
        )
    except Exception as e:
        raise DatabaseError(f"Failed to add progress: {str(e)}")


@router.get("/progress", response_model=List[ManhwaWithProgress])
async def get_user_progress(
    access_token: str = Depends(get_bearer_token(required=True)),
    db: UserAuthManager = Depends(get_auth_manager),
):
    try:
        return db.get_user_progress(access_token)
    except Exception as e:
        raise DatabaseError(f"Failed to get user progress: {str(e)}")


@router.delete("/progress/{manhwa_id}")
async def delete_user_progress(
    manhwa_id: int,
    access_token: str = Depends(get_bearer_token(required=True)),
    db: UserAuthManager = Depends(get_auth_manager),
):
    try:
        db.delete_progress(access_token, manhwa_id)
        return {"message": "Progress deleted successfully"}
    except Exception as e:
        raise DatabaseError(f"Failed to delete progress: {str(e)}")


@router.get("/email-confirmation")
async def email_confirmation():
    return HTMLResponse(
        content="""
        <html>
            <head>
                <title>Email Confirmation</title>
            </head>
            <body>
                <h1>Your email has been confirmed!</h1>
                <p>Thank you for confirming your email. You can now log in to your account.</p>
            </body>
        </html>
    """,
        status_code=200,
    )
