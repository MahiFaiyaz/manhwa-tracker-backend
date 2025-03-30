from fastapi import APIRouter, Depends
from app.services.manhwa_database_manager import ManhwaDatabaseManager

router = APIRouter(tags=["users"])


def get_db_manager():
    return ManhwaDatabaseManager()


@router.post("/signup")
async def sign_up(
    email: str, password: str, db: ManhwaDatabaseManager = Depends(get_db_manager)
):
    db.sign_up(email, password)


@router.post("/login")
async def login(
    email: str, password: str, db: ManhwaDatabaseManager = Depends(get_db_manager)
):
    db.login(email, password)


@router.post("/progress")
async def add_progress(
    manhwa_id: int,
    current_chapter: int,
    status: str,
    db: ManhwaDatabaseManager = Depends(get_db_manager),
):
    db.add_progress(manhwa_id, current_chapter, status)


@router.patch("/progress/{manhwa_id}")
async def add_progress(
    manhwa_id: int,
    current_chapter: int,
    status: str,
    db: ManhwaDatabaseManager = Depends(get_db_manager),
):
    db.add_progress(manhwa_id, current_chapter, status)


@router.get("/progress/{user_id}")
async def get_user_progress(
    user_id: str, db: ManhwaDatabaseManager = Depends(get_db_manager)
):
    db.get_user_progress(user_id)


@router.get("/progress/{manhwa_id}")
async def get_manhwa_progress(
    manhwa_id: str, db: ManhwaDatabaseManager = Depends(get_db_manager)
):
    db.get_manhwa_progress(manhwa_id)
