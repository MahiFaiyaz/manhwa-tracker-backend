from fastapi import APIRouter, BackgroundTasks
from app.services.manhwa_database_sync import ManhwaSync
from app.services.google_sheets_manager import GoogleSheetsManager

router = APIRouter()


@router.post("/sync")
async def sync(background_tasks: BackgroundTasks):
    # Run both fetch_all and sync_all methods in the background

    def sync_task():
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
