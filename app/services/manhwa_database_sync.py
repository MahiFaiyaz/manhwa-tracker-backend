import json
import os
from supabase import create_client
from app.config import SUPABASE_URL, SUPABASE_KEY


class ManhwaSync:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
            cls._instance.data_folder = "manhwa_data"
            cls._instance._cache = (
                {}
            )  # Caches IDs for fast lookups (genres, categories, etc.)
        return cls._instance

    def load_json(self, filename):
        """Loads JSON data from a file."""
        filepath = os.path.join(self.data_folder, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def sync_items(self, table_name, data, json_to_db_map):
        """Syncs data to a given table. Updates fields if values differ."""
        unique_key_json = list(data[0].keys())[0]
        unique_key_db = json_to_db_map[unique_key_json]  # Convert to DB column name

        db_records = self.get_all_records(table_name, unique_key_db)
        new_records = []
        updated_records = []
        seen_records = set()
        seen_json_values = set()  # To track duplicates in the JSON data

        for entry in data:
            unique_value = entry[
                unique_key_json
            ].strip()  # Get the unique value from JSON

            if unique_value in seen_json_values:
                continue
            seen_json_values.add(unique_value)

            record_data = {
                db_key: entry[json_key].strip()
                for json_key, db_key in json_to_db_map.items()
                if json_key in entry
            }

            if unique_value in db_records:
                # Update existing record
                record_id = db_records[unique_value]
                updated_records.append({**record_data, "id": record_id})
                seen_records.add(unique_value)
            else:
                # Insert new record
                new_records.append(record_data)
                seen_records.add(unique_value)

        # Bulk insert new records
        if new_records:
            response = self.supabase.table(table_name).insert(new_records).execute()
            if response.data:
                for row in response.data:
                    db_records[row[unique_key_db]] = row["id"]

        # Bulk update existing records
        if updated_records:
            self.supabase.table(table_name).upsert(updated_records).execute()

        # Delete records that are no longer in the JSON data
        to_delete = [db_records[key] for key in db_records if key not in seen_records]
        if to_delete:
            self.supabase.table(table_name).delete().in_("id", to_delete).execute()

    def get_all_records(self, table_name, unique_key_db="name"):
        """Fetch all records from the given table."""
        db_records = {}
        page = 1
        while True:
            # Fetch a page of records
            existing_db_data = (
                self.supabase.table(table_name)
                .select(f"id, {unique_key_db}")
                .range(
                    (page - 1) * 1000, page * 1000 - 1
                )  # Pagination: fetch 1000 records per page
                .execute()
            )

            # If no records returned, break the loop
            if not existing_db_data.data:
                break

            # Add records to db_records
            for row in existing_db_data.data:
                db_records[row[unique_key_db]] = row["id"]

            # Move to the next page
            page += 1

        return db_records

    def sync_manhwas(self):
        """Syncs manhwa data to Supabase, updating and deleting entries properly."""
        data = self.load_json("copy of master list.json")

        db_records = {}
        page = 1
        while True:
            # Fetch a page of records
            existing_db_data = (
                self.supabase.table("manhwas")
                .select("id, name, synopsis")
                .range(
                    (page - 1) * 1000, page * 1000 - 1
                )  # Pagination: fetch 1000 records per page
                .execute()
            )

            # If no records returned, break the loop
            if not existing_db_data.data:
                break

            # Add records to db_records
            for row in existing_db_data.data:
                # Build composite key (e.g., (name, synopsis))
                db_records[(row["name"], row["synopsis"])] = row["id"]

            # Move to the next page
            page += 1

        # Fetch existing status and rating IDs
        status_map = self.get_all_records("status")
        rating_map = self.get_all_records("rating")

        # Prepare lists for bulk insert/update
        new_manhwas = []
        updated_manhwas = []
        seen_manhwas = set()  # Set to ensure no duplicates

        for entry in data:
            title = entry["Title"].strip()
            synopsis = entry["Synopsis"].strip()
            key = (title, synopsis)

            # Get status and rating IDs efficiently
            status_id = status_map.get(entry["Status"])
            rating_id = rating_map.get(entry["Rating"])

            manhwa_data = {
                "name": title,
                "synopsis": synopsis,
                "year_released": int(entry["Year Released"]),
                "chapters": entry["Chapter(s)"].strip(),
                "chapter_min": (
                    0
                    if "Less than" in entry["Chapter(s)"]
                    else (
                        100
                        if "More than" in entry["Chapter(s)"]
                        else int(entry["Chapter(s)"])
                    )
                ),
                "chapter_max": 100 if "Less than" in entry["Chapter(s)"] else None,
                "status_id": status_id,
                "rating_id": rating_id,
            }

            if key in db_records:
                # Update existing manhwas
                manhwa_id = db_records[key]
                if key not in seen_manhwas:
                    updated_manhwas.append({**manhwa_data, "id": manhwa_id})
                    seen_manhwas.add(key)
            else:
                # Insert new manhwas
                new_manhwas.append(manhwa_data)
                seen_manhwas.add(key)

        # Bulk insert new manhwas
        if new_manhwas:
            response = self.supabase.table("manhwas").insert(new_manhwas).execute()
            if response.data:
                for row in response.data:
                    db_records[(row["name"], row["synopsis"])] = row["id"]

        # Bulk update existing manhwas
        if updated_manhwas:
            self.supabase.table("manhwas").upsert(updated_manhwas).execute()

        # Bulk process relationships
        self.bulk_link_manhwa_relations(data, db_records)
        to_delete = [db_records[key] for key in db_records if key not in seen_manhwas]
        # Delete removed manhwas
        if to_delete:
            self.supabase.table("manhwas").delete().in_("id", to_delete).execute()

    def bulk_link_manhwa_relations(self, data, db_records):
        """Efficiently links manhwas with genres, categories in bulk."""
        (
            genre_records,
            category_records,
        ) = (
            [],
            [],
        )
        genre_map = self.get_all_records("genres")
        category_map = self.get_all_records("categories")

        for entry in data:
            title = entry["Title"].strip()
            synopsis = entry["Synopsis"].strip()
            key = (title, synopsis)

            manhwa_id = db_records[key]
            # Get all genre, category IDs in one go
            genre_ids = [
                genre_map.get(genre) for genre in entry["Genre(s)"].split(", ")
            ]

            category_fix_map = {
                "Dungeon/Towers": "Dungeon/Tower",
                "Multiple Protagonists": "Multiple Protagonist",
            }
            category_ids = []
            for category in entry["Categories"].split(", "):
                category_id = category_map.get(category)
                if category_id:
                    category_ids.append(category_id)
                else:
                    if category in category_fix_map:
                        category_ids.append(
                            category_map.get(category_fix_map[category])
                        )
                    else:
                        category_ids.append(None)
                        print(category_ids)
                        print(f"{category} not found in category list.")

            # Prepare records for batch insert
            genre_records.extend(
                {"manhwa_id": manhwa_id, "genre_id": gid} for gid in genre_ids
            )
            category_records.extend(
                {"manhwa_id": manhwa_id, "category_id": cid} for cid in category_ids
            )
        # Bulk insert all relationships
        if genre_records:
            self.supabase.table("manhwa_genres").upsert(genre_records).execute()
        if category_records:
            self.supabase.table("manhwa_categories").upsert(category_records).execute()

    def sync_genres(self):
        """Syncs genres data to Supabase."""
        data = self.load_json("genres.json")
        self.sync_items("genres", data, {"Genre": "name", "Description": "description"})

    def sync_categories(self):
        """Syncs categories data to Supabase."""
        data = self.load_json("categories.json")
        self.sync_items(
            "categories",
            data,
            {"Main Categories": "name", "Description": "description"},
        )

    def sync_ratings(self):
        """Syncs ratings data to Supabase."""
        data = self.load_json("rating.json")
        self.sync_items(
            "rating", data, {"Rating": "name", "Description": "description"}
        )

    def sync_status(self):
        """Syncs status data to Supabase."""
        data = self.load_json("status.json")
        self.sync_items(
            "status", data, {"Status": "name", "Description": "description"}
        )

    def sync_all(self):
        """Runs all sync functions."""
        self.sync_genres()
        self.sync_categories()
        self.sync_ratings()
        self.sync_status()
        self.sync_manhwas()
        print("Sync complete.")
