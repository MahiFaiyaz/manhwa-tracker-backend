from supabase import create_client
from typing import List, Optional
from app.config import SUPABASE_URL, SUPABASE_KEY


class ManhwaDatabaseManager:
    def __init__(self):
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    def get_genres(self):
        """Fetch all genres with name and description."""
        response = self.supabase.table("genres").select("name, description").execute()
        return response.data if response.data else []

    def get_categories(self):
        """Fetch all categories with name and description."""
        response = (
            self.supabase.table("categories").select("name, description").execute()
        )
        return response.data if response.data else []

    def get_ratings(self):
        """Fetch all ratings with name and description."""
        response = self.supabase.table("rating").select("name, description").execute()
        return response.data if response.data else []

    def get_statuses(self):
        """Fetch all statuses with name and description."""
        response = self.supabase.table("status").select("name, description").execute()
        return response.data if response.data else []

    def get_all_manhwas(self):
        """Fetch all manhwas and their details."""
        response = (
            self.supabase.table("manhwas")
            .select("*", "status(name)", "rating(name)")
            .execute()
        )
        return response.data if response.data else []

    def get_filtered_manhwas(
        self,
        genres: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        min_chapters: Optional[int] = None,
        max_chapters: Optional[int] = None,
        year_released: Optional[int] = None,
        status: Optional[List[str]] = None,
        ratings: Optional[List[str]] = None,
    ):
        """Fetch manhwas based on filters."""
        query = self.supabase.table("manhwas").select(
            "*", "status(name)", "rating(name)"
        )

        if year_released:
            query = query.eq("year_released", year_released)
        if min_chapters:
            query = query.gte("chapter_min", min_chapters)
        if max_chapters:
            query = query.lte("chapter_max", max_chapters)
        if status:
            query = query.in_("status_id", self._get_status_ids(status))
        if ratings:
            query = query.in_("rating_id", self._get_rating_ids(ratings))
        if genres:
            query = query.filter("id", "in", self._get_manhwa_ids_by_genres(genres))
        if categories:
            query = query.filter(
                "id", "in", self._get_manhwa_ids_by_categories(categories)
            )

        response = query.execute()
        return response.data if response.data else []

    def _get_status_ids(self, status_names: List[str]) -> List[int]:
        response = (
            self.supabase.table("status")
            .select("id")
            .in_("name", status_names)
            .execute()
        )
        return [row["id"] for row in response.data] if response.data else []

    def _get_rating_ids(self, rating_names: List[str]) -> List[int]:
        response = (
            self.supabase.table("rating")
            .select("id")
            .in_("name", rating_names)
            .execute()
        )
        return [row["id"] for row in response.data] if response.data else []

    def _get_manhwa_ids_by_genres(self, genres: List[str]) -> List[int]:
        response = (
            self.supabase.table("manhwa_genres")
            .select("manhwa_id")
            .in_("genre_id", self._get_genre_ids(genres))
            .execute()
        )
        return [row["manhwa_id"] for row in response.data] if response.data else []

    def _get_manhwa_ids_by_categories(self, categories: List[str]) -> List[int]:
        response = (
            self.supabase.table("manhwa_categories")
            .select("manhwa_id")
            .in_("category_id", self._get_category_ids(categories))
            .execute()
        )
        return [row["manhwa_id"] for row in response.data] if response.data else []

    def _get_genre_ids(self, genre_names: List[str]) -> List[int]:
        response = (
            self.supabase.table("genres")
            .select("id")
            .in_("name", genre_names)
            .execute()
        )
        return [row["id"] for row in response.data] if response.data else []

    def _get_category_ids(self, category_names: List[str]) -> List[int]:
        response = (
            self.supabase.table("categories")
            .select("id")
            .in_("name", category_names)
            .execute()
        )
        return [row["id"] for row in response.data] if response.data else []
