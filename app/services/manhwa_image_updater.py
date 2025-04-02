import requests
import time
from app.core.settings import get_settings
from app.core.logging import get_logger
from app.core.exceptions import DatabaseError
from app.services.manhwa_database_manager import ManhwaDatabaseManager

logger = get_logger("manhwa_image_updater")
settings = get_settings()


class ManhwaImageUpdater:
    def __init__(self):
        logger.info("Initializing ManhwaImageUpdater")
        self.db_manager = ManhwaDatabaseManager()
        self.api_url = "https://api.myanimelist.net/v2/manga"
        self.mal_client_id = settings.MAL_CLIENT_ID

    def _fetch_image(self, title):
        """Fetch image URL for a given manhwa title."""
        try:
            logger.debug(f"Fetching image for: {title}")
            params = {
                "q": title[0:64],
                "fields": "main_picture",
                "limit": 1,
            }
            headers = {"X-MAL-CLIENT-ID": self.mal_client_id}

            response = requests.get(self.api_url, headers=headers, params=params)

            if response.status_code == 200:
                data = response.json()
                if data.get("data") and len(data["data"]) > 0:
                    image_url = data["data"][0]["node"]["main_picture"].get("medium")
                    if image_url:
                        logger.debug(f"Found image for {title}")
                        return image_url
                    else:
                        logger.debug(f"No image found in API response for {title}")
                else:
                    logger.debug(f"No data found in API response for {title}")
            elif response.status_code == 429:
                logger.warning("Rate limit exceeded, waiting before retry")
                time.sleep(60)  # Wait for 1 minute before retrying
            elif response.status_code == 504:
                logger.warning("Gateway timeout, waiting before retry")
                time.sleep(180)  # Wait for 3 minutes before retrying
            else:
                logger.warning(
                    f"API request failed with status code {response.status_code} for {title}"
                )

            return None
        except requests.RequestException as e:
            logger.error(f"Request error fetching image for {title}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error fetching image for {title}: {str(e)}")
            return None

    def fetch_missing_images(self, max_retries=3):
        """Fetch and update images for manhwas without images."""
        logger.info("Starting to fetch missing images")
        try:
            manhwas = self.db_manager.get_manhwas_without_image()
            logger.info(f"Found {len(manhwas)} manhwas without images")

            for index, manhwa in enumerate(manhwas):
                logger.info(f"Processing {index+1}/{len(manhwas)}: {manhwa['name']}")

                # Try with retries
                retries = 0
                while retries < max_retries:
                    image_url = self._fetch_image(manhwa["name"])
                    if image_url:
                        try:
                            self.db_manager.update_image_url(manhwa["id"], image_url)
                            logger.info(f"Updated image for {manhwa['name']}")
                            break
                        except Exception as e:
                            logger.error(
                                f"Failed to update image URL in database for {manhwa['name']}: {str(e)}"
                            )
                            retries += 1
                    else:
                        logger.warning(f"Image not found for {manhwa['name']}")
                        retries += 1

                    if retries < max_retries:
                        time.sleep(2)  # Wait before retry

                # Standard wait between requests to avoid rate limiting
                time.sleep(1)

            logger.info("Completed fetching missing images")
        except Exception as e:
            logger.error(f"Error during fetch missing images: {str(e)}")
            raise DatabaseError(f"Failed to fetch missing images: {str(e)}")

    def fetch_all_images(self, max_retries=3):
        """Fetch and update images for all manhwas."""
        logger.info("Starting to fetch all images")
        try:
            # Get all manhwas with pagination to handle large data sets
            page = 1
            per_page = 100
            processed = 0

            while True:
                logger.info(f"Fetching manhwas page {page}")
                manhwas_response = self.db_manager.get_manhwas(
                    page=page, per_page=per_page
                )
                manhwas = manhwas_response.get("data", [])

                if not manhwas:
                    break

                total_manhwas = manhwas_response.get("pagination", {}).get("total", 0)
                logger.info(
                    f"Processing page {page} with {len(manhwas)} manhwas (Total: {total_manhwas})"
                )

                for index, manhwa in enumerate(manhwas):
                    processed += 1
                    logger.info(
                        f"Processing {processed}/{total_manhwas}: {manhwa['name']}"
                    )

                    # Try with retries
                    retries = 0
                    while retries < max_retries:
                        image_url = self._fetch_image(manhwa["name"])
                        if image_url:
                            try:
                                self.db_manager.update_image_url(
                                    manhwa["id"], image_url
                                )
                                logger.info(f"Updated image for {manhwa['name']}")
                                break
                            except Exception as e:
                                logger.error(
                                    f"Failed to update image URL in database for {manhwa['name']}: {str(e)}"
                                )
                                retries += 1
                        else:
                            logger.warning(f"Image not found for {manhwa['name']}")
                            retries += 1

                        if retries < max_retries:
                            time.sleep(2)  # Wait before retry

                    # Standard wait between requests to avoid rate limiting
                    time.sleep(1)

                page += 1

            logger.info("Completed fetching all images")
        except Exception as e:
            logger.error(f"Error during fetch all images: {str(e)}")
            raise DatabaseError(f"Failed to fetch all images: {str(e)}")
