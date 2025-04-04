from fastapi import APIRouter, Depends, HTTPException, Header
from app.services.manhwa_database_manager import ManhwaDatabaseManager
from app.schemas.auth import RefreshTokenRequest, TokenResponse

router = APIRouter()


def get_db_manager():
    return ManhwaDatabaseManager()


@router.post("/refresh_token", response_model=TokenResponse, tags=["Token"])
async def refresh_token(
    refresh_request: RefreshTokenRequest,
    db: ManhwaDatabaseManager = Depends(get_db_manager),
):
    try:
        new_access_token, new_refresh_token = db.refresh_token(
            refresh_request.refresh_token
        )
        return TokenResponse(
            access_token=new_access_token, refresh_token=new_refresh_token
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))
