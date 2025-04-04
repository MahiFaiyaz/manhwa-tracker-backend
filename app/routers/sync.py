from fastapi import APIRouter, BackgroundTasks, HTTPException, Header, status
from app.config import SYNC_API_KEY
from app.core.exceptions import DatabaseError

router = APIRouter()


@router.post("/sync", tags=["Sync"])
async def sync(background_tasks: BackgroundTasks, api_key: str = Header(None)):
    # Validate API key
    if api_key != SYNC_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden: Invalid API Key"
        )

    def sync_task():
        try:
            from app.services.manhwa_database_sync import ManhwaSync
            from app.services.google_sheets_manager import GoogleSheetsManager

            # Create instances of ManhwaDataManager and ManhwaSync
            data_manager = GoogleSheetsManager()
            syncer = ManhwaSync()

            # Fetch data first
            data_manager.fetch_all()

            # Then sync the data
            syncer.sync_all()
        except DatabaseError as e:
            # Log the error (your logger is already set up in your services)
            pass
        except Exception as e:
            # Log any unexpected errors
            pass

    # Add the sync task to be executed in the background
    background_tasks.add_task(sync_task)

    return {"message": "Sync started", "status": "processing"}
