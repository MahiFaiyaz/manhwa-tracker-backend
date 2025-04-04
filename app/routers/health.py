from fastapi import APIRouter
from app.core.database import Database
from app.core.exceptions import DatabaseError

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    # Basic health check
    status = {"api": "ok"}

    # Check database connection
    try:
        db = Database()
        # Simple query to verify database connection
        db.client.from_("status").select("id").limit(1).execute()
        status["database"] = "ok"
    except Exception as e:
        status["database"] = "error"
        status["database_message"] = str(e)
        # We don't raise an exception here because we want the health check
        # to report the state rather than fail completely

    return status
