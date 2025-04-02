from supabase import create_client
from typing import List, Optional
from app.config import SUPABASE_URL, SUPABASE_KEY
from fastapi import HTTPException, Header


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

    def get_manhwas_without_image(self):
        """Fetch manhwas with missing images."""
        response = (
            self.supabase.table("manhwas")
            .select("id, name, image_url")
            .is_("image_url", None)
            .execute()
        )
        return response.data if response.data else []

    def update_image_url(self, manhwa_id: int, image_url: str):
        """Update the image URL for a specific manhwa."""
        response = (
            self.supabase.table("manhwas")
            .update({"image_url": image_url})
            .eq("id", manhwa_id)
            .execute()
        )
        return response.data if response.data else []

    def get_manhwas(
        self,
        genres: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        min_chapters: Optional[int] = None,
        max_chapters: Optional[int] = None,
        min_year_released: Optional[int] = None,
        max_year_released: Optional[int] = None,
        status: Optional[List[str]] = None,
        ratings: Optional[List[str]] = None,
    ):
        """Fetch manhwas based on filters."""

        # Fetch valid names from corresponding tables
        valid_genres = {
            g["name"]
            for g in self.supabase.table("genres").select("name").execute().data or []
        }
        valid_categories = {
            c["name"]
            for c in self.supabase.table("categories").select("name").execute().data
            or []
        }
        valid_statuses = {
            s["name"]
            for s in self.supabase.table("status").select("name").execute().data or []
        }
        valid_ratings = {
            r["name"]
            for r in self.supabase.table("rating").select("name").execute().data or []
        }

        # Validate user input
        invalid_genres = set(genres or []) - valid_genres
        invalid_categories = set(categories or []) - valid_categories
        invalid_statuses = set(status or []) - valid_statuses
        invalid_ratings = set(ratings or []) - valid_ratings

        invalid_filters = {}

        if invalid_genres:
            invalid_filters["invalid_genres"] = list(invalid_genres)
        if invalid_categories:
            invalid_filters["invalid_categories"] = list(invalid_categories)
        if invalid_statuses:
            invalid_filters["invalid_statuses"] = list(invalid_statuses)
        if invalid_ratings:
            invalid_filters["invalid_ratings"] = list(invalid_ratings)

        if invalid_filters:
            raise HTTPException(
                status_code=400,
                detail={"error": "Invalid filters", **invalid_filters},
            )

        query = self.supabase.table("manhwas").select(
            "*",
            "status(name)",
            "rating(name)",
            "manhwa_genres!inner(genre_id, genres(name))",
            "manhwa_categories!inner(category_id, categories(name))",
        )

        if min_year_released:
            query = query.gte("year_released", min_year_released)
        if max_year_released:
            query = query.lte("year_released", max_year_released)
        if min_chapters:
            query = query.gte("chapter_min", min_chapters)
        if max_chapters:
            query = query.lte("chapter_max", max_chapters)
        if status:
            query = query.in_("status_id", self._get_status_ids(status))
        if ratings:
            query = query.in_("rating_id", self._get_rating_ids(ratings))
        if genres:
            query = query.in_("id", self._get_manhwa_ids_by_genres(genres))
        if categories:
            query = query.in_("id", self._get_manhwa_ids_by_categories(categories))

        response = query.execute()
        manhwas = response.data if response.data else []

        for manhwa in manhwas:
            manhwa["genres"] = [
                g["genres"]["name"] for g in manhwa.get("manhwa_genres", [])
            ]
            manhwa["categories"] = [
                c["categories"]["name"] for c in manhwa.get("manhwa_categories", [])
            ]
            # Remove redundant nested lists
            manhwa.pop("manhwa_genres", None)
            manhwa.pop("manhwa_categories", None)
            manhwa.pop("status_id", None)
            manhwa.pop("rating_id", None)
            manhwa.pop("created_at", None)

        return response.data if response.data else []

    def _get_status_ids(self, status_names: List[str]) -> List[int]:
        response = (
            self.supabase.table("status")
            .select("id")
            .in_("name", status_names)
            .execute()
        )
        print(response.data)
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

    def sign_up(self, email: str, password: str):
        """Sign up a new user."""
        return self.supabase.auth.sign_up(
            {
                "email": email,
                "password": password,
            }
        )

    def login(self, email: str, password: str):
        """Log in an existing user."""
        response =  self.supabase.auth.sign_in_with_password(
            {
                "email": email,
                "password": password,
            }
        )
        session = response.session
        if session:
            return {"access_token": session.access_token, "refresh_token": session.refresh_token}
    
        return {"error": "Login failed"}
    
    def get_user_id(self, access_token):
        try:
            response = self.supabase.auth.get_user(access_token)
            user = response.user
            if not user:
                raise HTTPException(status_code=401, detail="User not found")

            # Now you can use user_id to fetch user-specific data, like progress
            return user.id
        
        except Exception as e:
            print(e)
            raise HTTPException(status_code=401, detail="Invalid or expired token")


    def add_progress(self, access_token, manhwa_id: int, current_chapter: int, reading_status: str):
        """Add or update progress for a specific manhwa."""
        user_id = self.get_user_id(access_token)
        response = (
            self.supabase.table("user_manhwa_progress")
            .insert(
                {
                    "user_id": user_id,
                    "manhwa_id": manhwa_id,
                    "current_chapter": current_chapter,
                    "status": reading_status,
                }
            )
            .execute()
        )
        return response.data if response.data else []

    def update_progress(
        self, access_token, manhwa_id: int, current_chapter: int, reading_status: str
    ):
        """Update progress for a specific manhwa."""
        user_id = self.get_user_id(access_token)
        response = (
            self.supabase.table("user_manhwa_progress")
            .update(
                {
                    "current_chapter": current_chapter,
                    "status": reading_status,
                }
            )
            .eq("manhwa_id", manhwa_id)
            .execute()
        )
        return response.data if response.data else []

    def get_user_progress(self, access_token):
        """Fetch progress for a specific user."""
        user_id = self.get_user_id(access_token)
        response = (
            self.supabase.table("user_manhwa_progress")
            .select("*")
            .eq("user_id", user_id)
            .execute()
        )
        return response.data if response.data else []

    def get_manhwa_progress(self, manhwa_id: str):
        """Fetch progress for a specific manhwa."""
        response = (
            self.supabase.table("user_manhwa_progress")
            .select("*")
            .eq("manhwa_id", manhwa_id)
            .execute()
        )
        return response.data if response.data else []
    
    def refresh_token(self, refresh_token):
        try:
            response = self.supabase.auth.refresh_session(refresh_token)
            
            # Extract new tokens
            new_access_token = response.session.access_token
            new_refresh_token = response.session.refresh_token  # Sometimes Supabase gives a new one
            
            return new_access_token, new_refresh_token
        except Exception as e:
            raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
