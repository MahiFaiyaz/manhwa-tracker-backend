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
            )  # Caches IDs for fast lookups (genres, authors, etc.)
        return cls._instance

    def load_json(self, filename):
        """Loads JSON data from a file."""
        filepath = os.path.join(self.data_folder, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def get_or_create(self, table, name, cache=None):
        """Fetches or inserts an entry and caches it for efficiency."""

        if cache is None:
            cache = self.get_existing_ids(table)

        if name in cache:
            return cache[name]

        # Insert new entry
        response = self.supabase.table(table).insert({"name": name}).execute()
        if response.data:
            new_id = response.data[0]["id"]
            cache[name] = new_id  # Update cache
            return new_id
        else:
            raise ValueError(f"Failed to insert {name} into {table}")

    def update_item_fields(self, table_name, item_id, item_data):
        """Updates a specific field for an item if the value is different."""
        # Fetch the current value of the field
        current_data = (
            self.supabase.table(table_name)
            .select(",".join(item_data.keys()))  # Select only necessary fields
            .eq("id", item_id)
            .execute()
        )

        if current_data.data:
            existing_item = current_data.data[0]  # Extract the first record

            # Identify which fields have changed
            updates = {
                field: value
                for field, value in item_data.items()
                if existing_item.get(field) != value
            }

            # If there are changes, update the record in one request
            if updates:
                update_response = (
                    self.supabase.table(table_name)
                    .update(updates)
                    .eq("id", item_id)
                    .execute()
                )

                if update_response.data:
                    pass  # success, no error
                elif update_response.error:
                    print(
                        f"Failed to update {table_name} ID {item_id}: {update_response.error}"
                    )

    def sync_items(self, table_name, data, json_to_db_map):
        """Syncs data to a given table. Updates fields if values differ."""
        unique_key_json = list(data[0].keys())[0]
        unique_key_db = json_to_db_map[unique_key_json]  # Convert to DB column name

        # Fetch existing records from the database
        # existing_db_data = (
        # self.supabase.table(table_name).select(f"id, {unique_key_db}").execute()
        # )

        # db_records = {row[unique_key_db]: row["id"] for row in existing_db_data.data}
        db_records = self.get_all_records(table_name, unique_key_db)
        new_records = []
        updated_records = []
        seen_records = set()
        seen_json_values = set()  # To track duplicates in the JSON data

        for entry in data:
            unique_value = entry[unique_key_json]  # Get the unique value from JSON

            if unique_value in seen_json_values:
                continue
            seen_json_values.add(unique_value)

            record_data = {
                db_key: entry[json_key]
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

    def get_existing_ids(self, table_name):
        """Fetch all existing items from a table and return a dictionary mapping names to IDs."""
        response = self.supabase.table(table_name).select("id, name").execute()
        return {row["name"]: row["id"] for row in response.data}

    def sync_manhwas(self):
        """Syncs manhwa data to Supabase, updating and deleting entries properly."""
        data = self.load_json("copy of master list.json")

        # Get all existing manhwas from the database
        existing_db_data = self.supabase.table("manhwas").select("id, name").execute()
        db_records = {row["name"]: row["id"] for row in existing_db_data.data}

        # Fetch existing status and rating IDs
        status_map = self.get_existing_ids("status")
        rating_map = self.get_existing_ids("rating")

        # Prepare lists for bulk insert/update
        new_manhwas = []
        updated_manhwas = []
        new_titles = set()

        for entry in data:
            title = entry["Title"]
            # Get status and rating IDs efficiently
            status_name = entry["Status"]
            rating_name = entry["Rating"]

            status_id = status_map.get(status_name)
            rating_id = rating_map.get(rating_name)

            manhwa_data = {
                "name": title,
                "synopsis": entry["Synopsis"],
                "year_released": int(entry["Year Released"]),
                "chapters": entry["Chapter(s)"],
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

            if title in db_records:
                # Update existing manhwas
                manhwa_id = db_records[title]
                updated_manhwas.append({**manhwa_data, "id": manhwa_id})
            else:
                # Insert new manhwas
                new_manhwas.append(manhwa_data)
                new_titles.add(title)

        # Bulk insert new manhwas
        if new_manhwas:
            response = self.supabase.table("manhwas").insert(new_manhwas).execute()
            if response.data:
                for row in response.data:
                    db_records[row["name"]] = row["id"]

        # Bulk update existing manhwas
        if updated_manhwas:
            self.supabase.table("manhwas").upsert(updated_manhwas).execute()

        # Bulk process relationships
        self.bulk_link_manhwa_relations(data, db_records)

        to_delete = [
            db_records[title]
            for title in db_records
            if title not in [entry["Title"] for entry in data]
        ]

        # Delete removed manhwas
        if to_delete:
            self.supabase.table("manhwas").delete().in_("id", to_delete).execute()

    def bulk_link_manhwa_relations(self, data, db_records):
        """Efficiently links manhwas with genres, categories, and authors in bulk."""
        genre_records, category_records, author_records = [], [], []

        for entry in data:
            manhwa_id = db_records[entry["Title"]]

            # Get all genre, category, and author IDs in one go
            genre_ids = [
                self.get_or_create("genres", g) for g in entry["Genre(s)"].split(", ")
            ]
            category_ids = [
                self.get_or_create("categories", c)
                for c in entry["Categories"].split(", ")
            ]
            author_ids = [
                self.get_or_create("authors", a) for a in entry["Author(s)"].split(", ")
            ]

            # Prepare records for batch insert
            genre_records.extend(
                {"manhwa_id": manhwa_id, "genre_id": gid} for gid in genre_ids
            )
            category_records.extend(
                {"manhwa_id": manhwa_id, "category_id": cid} for cid in category_ids
            )
            author_records.extend(
                {"manhwa_id": manhwa_id, "author_id": aid} for aid in author_ids
            )

        # Bulk insert all relationships
        if genre_records:
            self.supabase.table("manhwa_genres").upsert(genre_records).execute()
        if category_records:
            self.supabase.table("manhwa_categories").upsert(category_records).execute()
        if author_records:
            self.supabase.table("manhwa_authors").upsert(author_records).execute()

    def sync_genres(self):
        """Syncs genres data to Supabase."""
        data = self.load_json("genres.json")
        self.sync_items("genres", data, "Genre")

    def sync_categories(self):
        """Syncs categories data to Supabase."""
        data = self.load_json("categories.json")
        self.sync_items("categories", data, "Main Categories")

    def sync_authors(self):
        """Syncs authors data to Supabase."""
        data = self.load_json("authors.json")
        self.sync_items("authors", data, "Authors")

    def sync_ratings(self):
        """Syncs authors data to Supabase."""
        data = self.load_json("rating.json")
        self.sync_items("rating", data, "Rating")

    def sync_status(self):
        """Syncs authors data to Supabase."""
        data = self.load_json("status.json")
        self.sync_items("status", data, "Status")

    def sync_all(self):
        """Runs all sync functions."""
        # self.sync_genres()
        # self.sync_categories()
        # self.sync_authors()
        # self.sync_ratings()
        # self.sync_status()
        self.sync_manhwas()
        print("Sync complete.")
