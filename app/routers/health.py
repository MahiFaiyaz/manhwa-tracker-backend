from fastapi import APIRouter
from app.core.database import get_db
from app.core.exceptions import DatabaseError

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    # Basic health check
    status = {"api": "ok"}

    # Check database connection
    try:
        with get_db() as db:
            # Simple query to verify database connection
            db.from_("status").select("id").limit(1).execute()
        status["database"] = "ok"
    except Exception as e:
        status["database"] = "error"
        status["database_message"] = str(e)

    return status
