from fastapi import APIRouter, Depends, HTTPException, Request, status, Header
from app.services.manhwa_database_manager import ManhwaDatabaseManager

router = APIRouter(tags=["users"])


def get_db_manager():
    return ManhwaDatabaseManager()


@router.post("/signup")
async def sign_up(
    email: str, password: str, db: ManhwaDatabaseManager = Depends(get_db_manager)
):
    try:
        response = db.sign_up(email, password)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return response


@router.post("/login")
async def login(
    email: str, password: str, db: ManhwaDatabaseManager = Depends(get_db_manager)
):
    try:
        response = db.login(email, password)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return response


@router.post("/progress")
async def add_progress(
    manhwa_id: int,
    current_chapter: int,
    reading_status: str,
    auth_token = Header(None), 
    db: ManhwaDatabaseManager = Depends(get_db_manager),
):
    if not auth_token:
        raise HTTPException(status_code=401, detail="Authorization token is required")

    access_token = auth_token.split("Bearer ")[1]
    return db.add_progress(access_token, manhwa_id, current_chapter, reading_status)


@router.patch("/progress/{manhwa_id}")
async def update_progress(
    current_chapter: int,
    reading_status: str,
    auth_token = Header(None), 
    db: ManhwaDatabaseManager = Depends(get_db_manager),
):
    if not auth_token:
        raise HTTPException(status_code=401, detail="Authorization token is required")

    access_token = auth_token.split("Bearer ")[1]
    return db.update_progress(access_token, current_chapter, reading_status)


@router.get("/progress")
async def get_user_progress(auth_token = Header(None), db: ManhwaDatabaseManager = Depends(get_db_manager)):
    if not auth_token:
        raise HTTPException(status_code=401, detail="Authorization token is required")

    # Extract the token from the Authorization header
    access_token = auth_token.split("Bearer ")[1]
    return db.get_user_progress(access_token)


@router.get("/progress/{manhwa_id}")
async def get_manhwa_progress(
    manhwa_id: str, db: ManhwaDatabaseManager = Depends(get_db_manager)
):
    return db.get_manhwa_progress(manhwa_id)
