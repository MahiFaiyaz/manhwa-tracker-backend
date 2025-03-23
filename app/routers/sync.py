from fastapi import APIRouter, BackgroundTasks, HTTPException, Header
from app.config import SYNC_API_KEY


router = APIRouter()

SECRET_API_KEY = SYNC_API_KEY


@router.post("/sync")
async def sync(background_tasks: BackgroundTasks, api_key=Header(None)):
    # Run both fetch_all and sync_all methods in the background
    if api_key != SECRET_API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden: Invalid API Key")

    def sync_task():
        from app.services.manhwa_database_sync import ManhwaSync
        from app.services.google_sheets_manager import GoogleSheetsManager

        # Create instances of ManhwaDataManager and ManhwaSync
        data_manager = GoogleSheetsManager()
        syncer = ManhwaSync()

        # Fetch data first
        data_manager.fetch_all()

        # Then sync the data
        syncer.sync_all()

    # Add the sync task to be executed in the background
    background_tasks.add_task(sync_task)

    return {"message": "Sync started"}
