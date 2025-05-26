import json
import os
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.exceptions import DatabaseError
from app.core.settings import get_settings

logger = get_logger("manhwa_sync")
settings = get_settings()


class ManhwaSync:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            logger.info("Initializing ManhwaSync")
            cls._instance = super().__new__(cls)
            cls._instance.data_folder = "manhwa_data"
            cls._instance._cache = (
                {}
            )  # Caches IDs for fast lookups (genres, categories, etc.)
        return cls._instance

    def load_json(self, filename):
        """Loads JSON data from a file."""
        try:
            filepath = os.path.join(self.data_folder, filename)
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"File not found: {filepath}")
            raise DatabaseError(f"Data file not found: {filename}")
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON format in file: {filename}")
            raise DatabaseError(f"Invalid data format in file: {filename}")
        except Exception as e:
            logger.error(f"Error loading JSON data from {filename}: {str(e)}")
            raise DatabaseError(f"Failed to load data from {filename}: {str(e)}")

    def sync_items(self, table_name, data, json_to_db_map):
        """Syncs data to a given table. Updates fields if values differ."""
        logger.info(f"Syncing {table_name} data")
        try:
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

            with get_db() as supabase:
                # Bulk insert new records
                if new_records:
                    logger.info(
                        f"Inserting {len(new_records)} new {table_name} records"
                    )
                    response = supabase.table(table_name).insert(new_records).execute()
                    if response.data:
                        for row in response.data:
                            db_records[row[unique_key_db]] = row["id"]

                # Bulk update existing records
                if updated_records:
                    logger.info(
                        f"Updating {len(updated_records)} existing {table_name} records"
                    )
                    supabase.table(table_name).upsert(updated_records).execute()

                # Delete records that are no longer in the JSON data
                to_delete = [
                    db_records[key] for key in db_records if key not in seen_records
                ]
                if to_delete:
                    logger.info(
                        f"Deleting {len(to_delete)} obsolete {table_name} records"
                    )
                    supabase.table(table_name).delete().in_("id", to_delete).execute()

            logger.info(f"Successfully synced {table_name} data")
        except Exception as e:
            logger.error(f"Error syncing {table_name} data: {str(e)}")
            raise DatabaseError(f"Failed to sync {table_name} data: {str(e)}")

    def get_all_records(self, table_name, unique_key_db="name"):
        """Fetch all records from the given table."""
        logger.info(f"Fetching all records from {table_name}")
        db_records = {}
        try:
            with get_db() as supabase:
                page = 1
                while True:
                    # Fetch a page of records
                    existing_db_data = (
                        supabase.table(table_name)
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

            logger.info(f"Fetched {len(db_records)} records from {table_name}")
            return db_records
        except Exception as e:
            logger.error(f"Error fetching records from {table_name}: {str(e)}")
            raise DatabaseError(f"Failed to fetch records from {table_name}: {str(e)}")

    def sync_manhwas(self, data):
        """Syncs manhwa data to Supabase, updating and deleting entries properly."""
        logger.info("Syncing manhwa data")
        try:
            db_records = {}
            with get_db() as supabase:
                page = 1
                while True:
                    # Fetch a page of records
                    existing_db_data = (
                        supabase.table("manhwas")
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
                        "chapter_max": (
                            100 if "Less than" in entry["Chapter(s)"] else None
                        ),
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
                    logger.info(f"Inserting {len(new_manhwas)} new manhwas")
                    response = supabase.table("manhwas").insert(new_manhwas).execute()
                    if response.data:
                        for row in response.data:
                            db_records[(row["name"], row["synopsis"])] = row["id"]

                # Bulk update existing manhwas
                if updated_manhwas:
                    logger.info(f"Updating {len(updated_manhwas)} existing manhwas")
                    supabase.table("manhwas").upsert(updated_manhwas).execute()

                # Bulk process relationships
                self.bulk_link_manhwa_relations(data, db_records)

                # Delete removed manhwas
                to_delete = [
                    db_records[key] for key in db_records if key not in seen_manhwas
                ]
                if to_delete:
                    logger.info(f"Deleting {len(to_delete)} obsolete manhwas")
                    supabase.table("manhwas").delete().in_("id", to_delete).execute()

            logger.info("Successfully synced manhwa data")
        except Exception as e:
            logger.error(f"Error syncing manhwa data: {str(e)}")
            raise DatabaseError(f"Failed to sync manhwa data: {str(e)}")

    def bulk_link_manhwa_relations(self, data, db_records):
        """Efficiently links manhwas with genres, categories in bulk."""
        logger.info("Linking manhwa relationships")
        try:
            genre_records, category_records = [], []
            genre_map = self.get_all_records("genres")
            category_map = self.get_all_records("categories")

            for entry in data:
                title = entry["Title"].strip()
                synopsis = entry["Synopsis"].strip()
                key = (title, synopsis)

                manhwa_id = db_records.get(key)
                if not manhwa_id:
                    logger.warning(f"Manhwa not found in database: {title}")
                    continue

                # Get all genre, category IDs in one go
                genre_ids = [
                    genre_map.get(genre)
                    for genre in entry["Genre(s)"].split(", ")
                    if genre.strip()
                ]
                genre_ids = [gid for gid in genre_ids if gid]  # Filter out None values

                category_fix_map = {
                    "Dungeon/Towers": "Dungeon/Tower",
                    "Multiple Protagonists": "Multiple Protagonist",
                }
                category_ids = []
                for category in entry["Categories"].split(", "):
                    category = category.strip()
                    if not category:
                        continue

                    category_id = category_map.get(category)
                    if category_id:
                        category_ids.append(category_id)
                    else:
                        if category in category_fix_map:
                            mapped_id = category_map.get(category_fix_map[category])
                            if mapped_id:
                                category_ids.append(mapped_id)
                            else:
                                logger.warning(
                                    f"Category not found even after mapping: {category}"
                                )
                        else:
                            logger.warning(f"Category not found: {category}")

                # Prepare records for batch insert
                genre_records.extend(
                    {"manhwa_id": manhwa_id, "genre_id": gid}
                    for gid in genre_ids
                    if gid
                )
                category_records.extend(
                    {"manhwa_id": manhwa_id, "category_id": cid}
                    for cid in category_ids
                    if cid
                )

            # Bulk insert all relationships
            with get_db() as supabase:
                if genre_records:
                    logger.info(f"Upserting {len(genre_records)} genre relationships")
                    supabase.table("manhwa_genres").upsert(genre_records).execute()
                if category_records:
                    logger.info(
                        f"Upserting {len(category_records)} category relationships"
                    )
                    supabase.table("manhwa_categories").upsert(
                        category_records
                    ).execute()

            logger.info("Successfully linked manhwa relationships")
        except Exception as e:
            logger.error(f"Error linking manhwa relationships: {str(e)}")
            raise DatabaseError(f"Failed to link manhwa relationships: {str(e)}")

    def sync_genres(self, data):
        """Syncs genres data to Supabase."""
        try:
            logger.info("Syncing genres data")
            data = self.load_json("genres.json")
            self.sync_items(
                "genres", data, {"Genre": "name", "Description": "description"}
            )
        except Exception as e:
            logger.error(f"Error syncing genres: {str(e)}")
            raise DatabaseError(f"Failed to sync genres: {str(e)}")

    def sync_categories(self, data):
        """Syncs categories data to Supabase."""
        try:
            logger.info("Syncing categories data")
            data = self.load_json("categories.json")
            self.sync_items(
                "categories",
                data,
                {"Main Categories": "name", "Description": "description"},
            )
        except Exception as e:
            logger.error(f"Error syncing categories: {str(e)}")
            raise DatabaseError(f"Failed to sync categories: {str(e)}")

    def sync_ratings(self, data):
        """Syncs ratings data to Supabase."""
        try:
            logger.info("Syncing ratings data")
            data = self.load_json("rating.json")
            self.sync_items(
                "rating", data, {"Rating": "name", "Description": "description"}
            )
        except Exception as e:
            logger.error(f"Error syncing ratings: {str(e)}")
            raise DatabaseError(f"Failed to sync ratings: {str(e)}")

    def sync_status(self, data):
        """Syncs status data to Supabase."""
        try:
            logger.info("Syncing status data")
            data = self.load_json("status.json")
            self.sync_items(
                "status", data, {"Status": "name", "Description": "description"}
            )
        except Exception as e:
            logger.error(f"Error syncing status: {str(e)}")
            raise DatabaseError(f"Failed to sync status: {str(e)}")

    def sync_all(self, all_data):
        """Runs all sync functions."""
        logger.info("Starting sync of all data")
        genres = all_data["genres"]
        categories = all_data["categories"]
        rating = all_data["rating"]
        status = all_data["status"]
        master_list = all_data["master_list"]
        try:
            self.sync_genres(genres)
            self.sync_categories(categories)
            self.sync_ratings(rating)
            self.sync_status(status)
            self.sync_manhwas(master_list)
            logger.info("All data synced successfully")
        except Exception as e:
            logger.error(f"Error during sync all operation: {str(e)}")
            raise DatabaseError(f"Failed to sync all data: {str(e)}")
