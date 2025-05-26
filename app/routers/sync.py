from fastapi import APIRouter, BackgroundTasks, Header, Request
from app.core.settings import get_settings
from app.core.exceptions import DatabaseError, AuthenticationError
from app.core.logging import get_logger

router = APIRouter(tags=["Sync"])
settings = get_settings()
logger = get_logger("sync")


@router.post("/sync")
async def sync(request: Request, background_tasks: BackgroundTasks):

    # Validate API key
    print(request.headers)
    api_key = request.headers.get("api_key")

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
            all_data = data_manager.fetch_all()

            # Then sync the data
            syncer.sync_all(all_data)

            logger.info("Database sync completed successfully")
        except DatabaseError as e:
            logger.error(f"Database sync error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during sync: {str(e)}", exc_info=True)

    # Add the sync task to be executed in the background
    background_tasks.add_task(sync_task)

    return {"message": "Sync started", "status": "processing"}


@router.post("/sync_missing_images")
async def sync_missing_images(request: Request, background_tasks: BackgroundTasks):

    # Validate API key
    api_key = request.headers.get("api_key")

    if api_key != settings.SYNC_API_KEY:
        raise AuthenticationError("Invalid API Key for sync operation")

    def sync_missing_images_task():
        try:
            from app.services.manhwa_image_updater import ManhwaImageUpdater

            # Create instances of ManhwaDataManager and ManhwaSync
            syncer = ManhwaImageUpdater()

            # Then sync the data
            syncer.fetch_missing_images()

            logger.info("Missing image sync completed successfully")
        except DatabaseError as e:
            logger.error(f"Database sync error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during sync: {str(e)}", exc_info=True)

    # Add the sync task to be executed in the background
    background_tasks.add_task(sync_missing_images_task)

    return {"message": "Missing image sync started", "status": "processing"}


@router.post("/sync_all_images")
async def sync_all_images(request: Request, background_tasks: BackgroundTasks):

    # Validate API key
    api_key = request.headers.get("api_key")

    if api_key != settings.SYNC_API_KEY:
        raise AuthenticationError("Invalid API Key for sync operation")

    def sync_all_images_task():
        try:
            from app.services.manhwa_image_updater import ManhwaImageUpdater

            # Create instances of ManhwaDataManager and ManhwaSync
            syncer = ManhwaImageUpdater()

            # Then sync the data
            syncer.fetch_all_images()

            logger.info("All image sync completed successfully")
        except DatabaseError as e:
            logger.error(f"Database sync error: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during sync: {str(e)}", exc_info=True)

    # Add the sync task to be executed in the background
    background_tasks.add_task(sync_all_images_task)

    return {"message": "All image sync started", "status": "processing"}
