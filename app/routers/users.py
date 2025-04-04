from fastapi import APIRouter, Depends, HTTPException, Header
from app.services.manhwa_database_manager import ManhwaDatabaseManager
from app.schemas.auth import UserSignUp, UserLogin, TokenResponse
from app.schemas.manhwa import (
    UserProgressCreate,
    UserProgressUpdate,
    UserProgress,
    ReadingStatus,
)

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
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=TokenResponse)
async def login(user: UserLogin, db: ManhwaDatabaseManager = Depends(get_db_manager)):
    try:
        response = db.login(user.email, user.password)
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/progress")
async def add_progress(
    progress: UserProgressCreate,
    auth_token: str = Header(None),
    db: ManhwaDatabaseManager = Depends(get_db_manager),
):
    if not auth_token:
        raise HTTPException(status_code=401, detail="Authorization token is required")

    try:
        access_token = auth_token.split("Bearer ")[1]
        return db.add_progress(
            access_token,
            progress.manhwa_id,
            progress.current_chapter,
            progress.reading_status,
        )
    except IndexError:
        raise HTTPException(status_code=401, detail="Invalid token format")


@router.patch("/progress/{manhwa_id}")
async def update_progress(
    manhwa_id: int,
    progress: UserProgressUpdate,
    auth_token: str = Header(None),
    db: ManhwaDatabaseManager = Depends(get_db_manager),
):
    if not auth_token:
        raise HTTPException(status_code=401, detail="Authorization token is required")

    try:
        access_token = auth_token.split("Bearer ")[1]
        return db.update_progress(
            access_token, manhwa_id, progress.current_chapter, progress.reading_status
        )
    except IndexError:
        raise HTTPException(status_code=401, detail="Invalid token format")


@router.get("/progress", response_model=List[UserProgress])
async def get_user_progress(
    auth_token: str = Header(None), db: ManhwaDatabaseManager = Depends(get_db_manager)
):
    if not auth_token:
        raise HTTPException(status_code=401, detail="Authorization token is required")

    try:
        access_token = auth_token.split("Bearer ")[1]
        return db.get_user_progress(access_token)
    except IndexError:
        raise HTTPException(status_code=401, detail="Invalid token format")


@router.get("/progress/{manhwa_id}", response_model=List[UserProgress])
async def get_manhwa_progress(
    manhwa_id: str, db: ManhwaDatabaseManager = Depends(get_db_manager)
):
    return db.get_manhwa_progress(manhwa_id)
