import json
import gspread
import os
from supabase import create_client, Client
from app.config import GOOGLE_SHEETS_API_KEY, SUPABASE_URL, SUPABASE_KEY

SHEET_ID = "1ZluFOVtJCv-cQLXWhmCLNoZFIMLV0eTrqozwyEb1zw8"


class ManhwaDataManager:
    _instance = None

    def __new__(cls, sheet_id, api_key):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.sheet_id = sheet_id
            cls._instance.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            cls._instance.gc = gspread.api_key(api_key)
            cls._instance.sh = cls._instance.gc.open_by_key(sheet_id)
        return cls._instance

    def __init__(self, sheet_id, api_key):
        if not hasattr(self, "initialized"):
            self.sheet_id = sheet_id
            self.supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
            self.gc = gspread.api_key(api_key)
            self.sh = self.gc.open_by_key(sheet_id)
            self.initialized = True

    def fetch_data(self, sheet_name, column_index, header_row_index):
        """Fetches manhwa data from Google Sheets."""
        try:
            worksheet = self.sh.worksheet(sheet_name)

            all_data = worksheet.get_values()
            starting_column_index = column_index[0]
            ending_column_index = column_index[1] + 1

            headers = all_data[header_row_index][
                starting_column_index:ending_column_index
            ]
            data = [
                row[starting_column_index:ending_column_index]
                for row in all_data[header_row_index + 1 :]
            ]
            dict_data = gspread.utils.to_records(headers, data)

            folder_path = "manhwa_data"
            os.makedirs(folder_path, exist_ok=True)

            # Save JSON file inside the 'manhwa_data' directory
            file_path = os.path.join(folder_path, f"{sheet_name}.json")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(dict_data, f, indent=4)  # Pretty print JSON

            return dict_data
        except gspread.exceptions.APIError as e:
            print(f"Google Sheets API error: {e}")
        except Exception as e:
            print(f"Error fetching data from {sheet_name}: {e}")
        return None

    def fetch_master_list(self):
        sheet_name = "Copy of Master List"
        self.fetch_data(sheet_name, column_index=(0, 9), header_row_index=7)

    def fetch_genres(self):
        sheet_name = "Genres"
        self.fetch_data(sheet_name, column_index=(3, 4), header_row_index=1)

    def fetch_categories(self):
        sheet_name = "Categories"
        self.fetch_data(sheet_name, column_index=(3, 5), header_row_index=1)

    def fetch_authors(self):
        sheet_name = "Authors"
        self.fetch_data(sheet_name, column_index=(3, 3), header_row_index=1)

    def fetch_status(self):
        sheet_name = "Status"
        self.fetch_data(sheet_name, column_index=(3, 4), header_row_index=1)

    def fetch_rating(self):
        sheet_name = "Rating"
        self.fetch_data(sheet_name, column_index=(3, 4), header_row_index=1)
