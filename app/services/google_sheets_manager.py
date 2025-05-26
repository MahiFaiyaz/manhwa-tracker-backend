import json
import gspread
import os
from app.core.settings import get_settings
from app.core.logging import get_logger
from app.core.exceptions import DatabaseError

logger = get_logger("google_sheets_manager")
settings = get_settings()


class GoogleSheetsManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            logger.info("Initializing Google Sheets Manager")
            cls._instance = super().__new__(cls)
            cls._instance.sheet_id = settings.SHEETS_ID
            try:
                cls._instance.gc = gspread.api_key(settings.GOOGLE_SHEETS_API_KEY)
                cls._instance.sh = cls._instance.gc.open_by_key(settings.SHEETS_ID)
            except Exception as e:
                logger.error(f"Failed to initialize Google Sheets connection: {str(e)}")
                raise DatabaseError(f"Google Sheets connection error: {str(e)}")
        return cls._instance

    def parse_column_ranges(self, column_string):
        """Parses a string of column ranges into a list of column indexes."""
        selected_columns = set()

        # Split by commas and process each part
        for part in column_string.split(","):
            part = part.strip()  # Remove spaces
            if ":" in part:  # Range format "x:y"
                start, end = map(int, part.split(":"))
                selected_columns.update(range(start, end + 1))
            else:  # Single column
                selected_columns.add(int(part))

        return sorted(selected_columns)

    def fetch_data(self, sheet_name, column_string, header_row_index):
        """Fetches manhwa data from Google Sheets."""
        try:
            logger.info(f"Fetching data from sheet: {sheet_name}")
            worksheet = self.sh.worksheet(sheet_name)

            all_data = worksheet.get_values()
            selected_columns = self.parse_column_ranges(column_string)

            # Extract headers
            headers = [all_data[header_row_index][col] for col in selected_columns]

            # Extract data
            data = [
                [row[col] for col in selected_columns]
                for row in all_data[header_row_index + 1 :]
            ]
            dict_data = gspread.utils.to_records(headers, data)

            return dict_data
        except gspread.exceptions.APIError as e:
            logger.error(f"Google Sheets API error: {e}")
            raise DatabaseError(f"Google Sheets API error: {str(e)}")
        except Exception as e:
            logger.error(f"Error fetching data from {sheet_name}: {e}")
            raise DatabaseError(f"Error fetching data from {sheet_name}: {str(e)}")

    def fetch_master_list(self):
        logger.info("Fetching master list data")
        sheet_name = "Copy of Master List"
        return self.fetch_data(sheet_name, "0:9", header_row_index=7)

    def fetch_genres(self):
        logger.info("Fetching genres data")
        sheet_name = "Genres"
        return self.fetch_data(sheet_name, "3:4", header_row_index=1)

    def fetch_categories(self):
        logger.info("Fetching categories data")
        sheet_name = "Categories"
        return self.fetch_data(sheet_name, "3, 5", header_row_index=1)

    def fetch_status(self):
        logger.info("Fetching status data")
        sheet_name = "Status"
        return self.fetch_data(sheet_name, "3:4", header_row_index=1)

    def fetch_rating(self):
        logger.info("Fetching rating data")
        sheet_name = "Rating"
        return self.fetch_data(sheet_name, "3:4", header_row_index=1)

    def fetch_all(self):
        logger.info("Starting fetch of all data")
        try:
            data = {
                "genres": self.fetch_genres(),
                "categories": self.fetch_categories(),
                "status": self.fetch_status(),
                "rating": self.fetch_rating(),
                "master_list": self.fetch_master_list(),
            }
            logger.info("All data fetched successfully")
            return data
        except Exception as e:
            logger.error(f"Error during fetch all operation: {str(e)}")
            raise DatabaseError(f"Failed to fetch all data: {str(e)}")
