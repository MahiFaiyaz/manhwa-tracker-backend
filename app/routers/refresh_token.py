from fastapi import APIRouter, Depends, HTTPException, Header
from app.services.manhwa_database_manager import ManhwaDatabaseManager


router = APIRouter()

def get_db_manager():
    return ManhwaDatabaseManager()


@router.post("/refresh_token", tags=["Token"])
async def refresh_token(refresh_token=Header(None), db: ManhwaDatabaseManager = Depends(get_db_manager)):
    if not refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token is required")

    try:
        new_access_token, new_refresh_token = db.refresh_token(refresh_token)
        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token  # Optional: send if Supabase issues a new one
        }
    except HTTPException as e:
        raise e

