import requests
from app.config import MAL_CLIENT_ID
from app.services.manhwa_database_manager import ManhwaDatabaseManager
import time


class ManhwaImageUpdater:
    def __init__(self):
        self.db_manager = ManhwaDatabaseManager()
        self.api_url = "https://api.myanimelist.net/v2/manga"

    def _fetch_image(self, title):
        """Fetch image URL for a given manhwa title."""
        params = {
            "q": title[0:64],
            "fields": "main_picture",
            "limit": 1,
        }
        headers = {"X-MAL-CLIENT-ID": MAL_CLIENT_ID}
        response = requests.get(self.api_url, headers=headers, params=params)

        if response.status_code == 200:
            data = response.json()
            if data["data"]:
                return data["data"][0]["node"]["main_picture"]["medium"]
        else:
            if response.status_code == 504:
                time.sleep(180)  # Wait for 5 minutes before retrying
            return None

    def fetch_missing_images(self):
        """Fetch and update images for manhwas without images."""
        manhwas = self.db_manager.get_manhwas_without_image()
        for manhwa in manhwas:
            print(manhwa["name"])
            image_url = self._fetch_image(manhwa["name"])
            time.sleep(1)  # To avoid hitting the API rate limit
            if image_url:
                self.db_manager.update_image_url(manhwa["id"], image_url)
                print(f"Updated image for {manhwa['name']}")
            else:
                print(f"Image not found for {manhwa['name']}")

    def fetch_all_images(self):
        """Fetch and update images for all manhwas."""
        manhwas = self.db_manager.get_manhwas()
        for manhwa in manhwas:
            image_url = self._fetch_image(manhwa["name"])
            if image_url:
                self.db_manager.update_image_url(manhwa["id"], image_url)
                print(f"Updated image for {manhwa['name']}")
            else:
                print(f"Image not found for {manhwa['name']}")


x = ManhwaImageUpdater()
x.fetch_missing_images()
