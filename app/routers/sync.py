from fastapi import APIRouter, BackgroundTasks, Header
from app.core.settings import get_settings
from app.core.exceptions import DatabaseError, AuthenticationError
from app.core.logging import get_logger

router = APIRouter()
settings = get_settings()
logger = get_logger("sync")


@router.post("/sync", tags=["Sync"])
async def sync(background_tasks: BackgroundTasks, api_key: str = Header(None)):
    # Validate API key
    if api_key != settings.SYNC_API_KEY:
        raise AuthenticationError("Invalid API Key for sync operation")

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

            logger.info("Database sync completed successfully")
        except DatabaseError as e:
            logger.error(f"Database sync error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during sync: {str(e)}", exc_info=True)

    # Add the sync task to be executed in the background
    background_tasks.add_task(sync_task)

    return {"message": "Sync started", "status": "processing"}
