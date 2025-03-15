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
            cls._instance.gc = gspread.api_key(api_key)
            cls._instance.sh = cls._instance.gc.open_by_key(sheet_id)
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
        self.fetch_data(sheet_name, "0:9", header_row_index=7)

    def fetch_genres(self):
        sheet_name = "Genres"
        self.fetch_data(sheet_name, "3:4", header_row_index=1)

    def fetch_categories(self):
        sheet_name = "Categories"
        self.fetch_data(sheet_name, "3, 5", header_row_index=1)

    def fetch_authors(self):
        sheet_name = "Authors"
        self.fetch_data(sheet_name, "3", header_row_index=1)

    def fetch_status(self):
        sheet_name = "Status"
        self.fetch_data(sheet_name, "3:4", header_row_index=1)

    def fetch_rating(self):
        sheet_name = "Rating"
        self.fetch_data(sheet_name, "3:4", header_row_index=1)
