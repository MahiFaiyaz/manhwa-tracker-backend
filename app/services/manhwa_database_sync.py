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

    def get_or_create(self, table, value, key="name"):
        """Fetches or inserts an entry and caches it for efficiency."""
        if table not in self._cache:
            self._cache[table] = {}

        if value in self._cache[table]:
            return self._cache[table][value]
        response = self.supabase.table(table).select("id").eq(key, value).execute()
        if response.data:
            item_id = response.data[0]["id"]
        else:
            insert_response = self.supabase.table(table).insert({key: value}).execute()
            item_id = insert_response.data[0]["id"]

        self._cache[table][value] = item_id
        return item_id

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

    def sync_items(
        self,
        table_name,
        items,
        json_key,
        db_key="name",
    ):
        """Syncs data to a given table. Updates fields if values differ."""
        # Convert JSON data into a dictionary for quick lookups
        existing_values = {item[json_key]: item for item in items}
        # Fetch existing data from the database
        existing_db_data = (
            self.supabase.table(table_name).select("id, " + db_key).execute()
        )
        db_records = {row[db_key]: row["id"] for row in existing_db_data.data}

        # Find entries to delete (exist in DB but not in JSON)
        to_delete = [
            db_records[name] for name in db_records if name not in existing_values
        ]

        for item in items:
            value = item.get(
                json_key
            )  # This is the value (e.g., Genre, Category, Author)

            # Get the ID of the item (or create if it doesn't exist)
            item_id = self.get_or_create(table_name, value, db_key)
            # Check and update fields if necessary
            # Convert field names to lowercase to match DB column names
            field_updates = {
                field.lower(): item[field] for field in item if field != json_key
            }

            # Update fields in a single call
            if field_updates:
                self.update_item_fields(table_name, item_id, field_updates)
        # Delete removed items from the database
        if to_delete:
            self.supabase.table(table_name).delete().in_("id", to_delete).execute()

    def sync_manhwas(self):
        """Syncs manhwa data to Supabase, updating and deleting entries properly."""
        data = self.load_json("copy of master list.json")

        # Get all existing manhwas from the database
        existing_db_data = self.supabase.table("manhwas").select("id, name").execute()
        db_records = {row["name"]: row["id"] for row in existing_db_data.data}
        to_delete = [
            db_records[title]
            for title in db_records
            if title not in [entry["Title"] for entry in data]
        ]
        for entry in data:
            title = entry["Title"]

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
                "status_id": self.get_or_create("status", entry["Status"]),
                "rating_id": self.get_or_create("rating", entry["Rating"]),
            }

            # If the manhwa already exists, get its ID, otherwise insert and get the new ID
            if title in db_records:
                manhwa_id = db_records[title]
                self.update_item_fields("manhwas", manhwa_id, manhwa_data)
            else:
                response = self.supabase.table("manhwas").insert(manhwa_data).execute()
                if response.data:
                    manhwa_id = response.data[0]["id"]
                    db_records[title] = manhwa_id  # Add it to the cache
                elif response.error:
                    print(f"Failed to insert into 'manhwas': {response.error}")

            self.link_manhwa_relations(manhwa_id, entry)

        # Delete removed manhwas
        if to_delete:
            self.supabase.table("manhwas").delete().in_("id", to_delete).execute()

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

    def link_manhwa_relations(self, manhwa_id, entry):
        """Links a manhwa with its genres, categories, and authors."""
        genres = entry["Genre(s)"].split(", ")
        categories = entry["Categories"].split(", ")
        authors = entry["Author(s)"].split(", ")

        for genre in genres:
            genre_id = self.get_or_create("genres", genre)
            self.supabase.table("manhwa_genres").upsert(
                {"manhwa_id": manhwa_id, "genre_id": genre_id}
            ).execute()

        for category in categories:
            category_id = self.get_or_create("categories", category)
            self.supabase.table("manhwa_categories").upsert(
                {"manhwa_id": manhwa_id, "category_id": category_id}
            ).execute()

        for author in authors:
            author_id = self.get_or_create("authors", author)
            self.supabase.table("manhwa_authors").upsert(
                {"manhwa_id": manhwa_id, "author_id": author_id}
            ).execute()

    def sync_all(self):
        """Runs all sync functions."""
        # self.sync_genres()
        # self.sync_categories()
        # self.sync_authors()
        # self.sync_ratings()
        # self.sync_status()
        self.sync_manhwas()
        print("Sync complete.")
