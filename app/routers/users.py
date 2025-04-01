from fastapi import APIRouter, Depends, HTTPException, Request, status
from app.services.manhwa_database_manager import ManhwaDatabaseManager

router = APIRouter(tags=["users"])


def get_db_manager():
    return ManhwaDatabaseManager()


@router.post("/signup")
async def sign_up(
    email: str, password: str, db: ManhwaDatabaseManager = Depends(get_db_manager)
):
    response = db.sign_up(email, password)
    if "error" in response:
        raise HTTPException(status_code=400, detail=response["error"]["message"])
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
    request: Request,
    manhwa_id: int,
    current_chapter: int,
    reading_status: str,
    db: ManhwaDatabaseManager = Depends(get_db_manager),
):
    user_id = request.state.user_id
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User not authenticated"
        )
    try:
        db.add_progress(user_id, manhwa_id, current_chapter, reading_status)
        return {"message": "Progress added successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )


@router.patch("/progress/{manhwa_id}")
async def update_progress(
    current_chapter: int,
    reading_status: str,
    db: ManhwaDatabaseManager = Depends(get_db_manager),
):
    db.update_progress(current_chapter, reading_status)


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
