from fastapi import APIRouter, Depends
from app.services.manhwa_database_manager import ManhwaDatabaseManager
from app.schemas.auth import RefreshTokenRequest, TokenResponse
from app.core.exceptions import AuthenticationError
from app.core.dependencies import get_db_manager

router = APIRouter()


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
        raise AuthenticationError(f"Token refresh failed: {str(e)}")
