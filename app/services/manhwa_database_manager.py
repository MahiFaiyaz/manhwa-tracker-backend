from typing import List, Optional, Dict, Any, Tuple
from functools import lru_cache
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.exceptions import DatabaseError, AuthenticationError, ValidationError

logger = get_logger("manhwa_database_manager")


class ManhwaDatabaseManager:
    """Manager for manhwa database operations."""

    def __init__(self):
        """Initialize the database manager."""
        with get_db() as supabase:
            self.supabase = supabase

    @lru_cache(maxsize=128)
    def get_genres(self) -> List[Dict[str, Any]]:
        """Fetch all genres with name and description."""
        try:
            response = (
                self.supabase.table("genres").select("name, description").execute()
            )
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching genres: {str(e)}")
            raise DatabaseError("Failed to fetch genres")

    @lru_cache(maxsize=128)
    def get_categories(self) -> List[Dict[str, Any]]:
        """Fetch all categories with name and description."""
        try:
            response = (
                self.supabase.table("categories").select("name, description").execute()
            )
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching categories: {str(e)}")
            raise DatabaseError("Failed to fetch categories")

    @lru_cache(maxsize=128)
    def get_ratings(self) -> List[Dict[str, Any]]:
        """Fetch all ratings with name and description."""
        try:
            response = (
                self.supabase.table("rating").select("name, description").execute()
            )
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching ratings: {str(e)}")
            raise DatabaseError("Failed to fetch ratings")

    @lru_cache(maxsize=128)
    def get_statuses(self) -> List[Dict[str, Any]]:
        """Fetch all statuses with name and description."""
        try:
            response = (
                self.supabase.table("status").select("name, description").execute()
            )
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching statuses: {str(e)}")
            raise DatabaseError("Failed to fetch statuses")

    def get_manhwas_without_image(self) -> List[Dict[str, Any]]:
        """Fetch manhwas with missing images."""
        try:
            response = (
                self.supabase.table("manhwas")
                .select("id, name, image_url")
                .is_("image_url", None)
                .execute()
            )
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching manhwas without images: {str(e)}")
            raise DatabaseError("Failed to fetch manhwas without images")

    def update_image_url(self, manhwa_id: int, image_url: str) -> List[Dict[str, Any]]:
        """Update the image URL for a specific manhwa."""
        try:
            response = (
                self.supabase.table("manhwas")
                .update({"image_url": image_url})
                .eq("id", manhwa_id)
                .execute()
            )
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error updating image URL for manhwa {manhwa_id}: {str(e)}")
            raise DatabaseError(f"Failed to update image URL for manhwa {manhwa_id}")

    def _validate_filters(
        self,
        genres: Optional[List[str]] = None,
        categories: Optional[List[str]] = None,
        status: Optional[List[str]] = None,
        ratings: Optional[List[str]] = None,
    ) -> None:
        """Validate filter parameters against database values."""
        invalid_filters = {}

        # Get valid names from corresponding tables
        valid_genres = {g["name"] for g in self.get_genres()}
        valid_categories = {c["name"] for c in self.get_categories()}
        valid_statuses = {s["name"] for s in self.get_statuses()}
        valid_ratings = {r["name"] for r in self.get_ratings()}

        # Validate user input
        if genres:
            invalid_genres = set(genres) - valid_genres
            if invalid_genres:
                invalid_filters["invalid_genres"] = list(invalid_genres)

        if categories:
            invalid_categories = set(categories) - valid_categories
            if invalid_categories:
                invalid_filters["invalid_categories"] = list(invalid_categories)

        if status:
            invalid_statuses = set(status) - valid_statuses
            if invalid_statuses:
                invalid_filters["invalid_statuses"] = list(invalid_statuses)

        if ratings:
            invalid_ratings = set(ratings) - valid_ratings
            if invalid_ratings:
                invalid_filters["invalid_ratings"] = list(invalid_ratings)

        if invalid_filters:
            raise ValidationError("Invalid filters", invalid_filters)

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
        page: int = 1,
        per_page: int = 20,
    ) -> Dict[str, Any]:
        """Fetch manhwas based on filters with pagination."""
        try:
            # Validate filters
            self._validate_filters(genres, categories, status, ratings)

            # Build query
            query = self.supabase.table("manhwas").select(
                "*",
                "status(name)",
                "rating(name)",
                "manhwa_genres!inner(genre_id, genres(name))",
                "manhwa_categories!inner(category_id, categories(name))",
                count="exact",  # Get total count for pagination
            )

            # Apply filters
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

            # Apply pagination
            start = (page - 1) * per_page
            end = start + per_page - 1
            query = query.range(start, end)

            # Add alphabetical sorting by name
            query = query.order("name")  # Sort by name alphabetically

            # Execute query
            response = query.execute()
            manhwas = response.data if response.data else []
            total_count = response.count if hasattr(response, "count") else 0

            # Process results
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

            # Return with pagination info
            return {
                "data": manhwas,
                "pagination": {
                    "page": page,
                    "per_page": per_page,
                    "total": total_count,
                    "pages": (total_count + per_page - 1) // per_page,
                },
            }

        except ValidationError as e:
            raise e
        except Exception as e:
            logger.error(f"Error fetching manhwas: {str(e)}")
            raise DatabaseError("Failed to fetch manhwas")

    def _get_status_ids(self, status_names: List[str]) -> List[int]:
        """Get status IDs from names."""
        try:
            response = (
                self.supabase.table("status")
                .select("id")
                .in_("name", status_names)
                .execute()
            )
            return [row["id"] for row in response.data] if response.data else []
        except Exception as e:
            logger.error(f"Error getting status IDs: {str(e)}")
            raise DatabaseError("Failed to get status IDs")

    def _get_rating_ids(self, rating_names: List[str]) -> List[int]:
        """Get rating IDs from names."""
        try:
            response = (
                self.supabase.table("rating")
                .select("id")
                .in_("name", rating_names)
                .execute()
            )
            return [row["id"] for row in response.data] if response.data else []
        except Exception as e:
            logger.error(f"Error getting rating IDs: {str(e)}")
            raise DatabaseError("Failed to get rating IDs")

    def _get_manhwa_ids_by_genres(self, genres: List[str]) -> List[int]:
        """Get manhwa IDs by genre names."""
        try:
            response = (
                self.supabase.table("manhwa_genres")
                .select("manhwa_id")
                .in_("genre_id", self._get_genre_ids(genres))
                .execute()
            )
            return [row["manhwa_id"] for row in response.data] if response.data else []
        except Exception as e:
            logger.error(f"Error getting manhwa IDs by genres: {str(e)}")
            raise DatabaseError("Failed to get manhwa IDs by genres")

    def _get_manhwa_ids_by_categories(self, categories: List[str]) -> List[int]:
        """Get manhwa IDs by category names."""
        try:
            response = (
                self.supabase.table("manhwa_categories")
                .select("manhwa_id")
                .in_("category_id", self._get_category_ids(categories))
                .execute()
            )
            return [row["manhwa_id"] for row in response.data] if response.data else []
        except Exception as e:
            logger.error(f"Error getting manhwa IDs by categories: {str(e)}")
            raise DatabaseError("Failed to get manhwa IDs by categories")

    def _get_genre_ids(self, genre_names: List[str]) -> List[int]:
        """Get genre IDs from names."""
        try:
            response = (
                self.supabase.table("genres")
                .select("id")
                .in_("name", genre_names)
                .execute()
            )
            return [row["id"] for row in response.data] if response.data else []
        except Exception as e:
            logger.error(f"Error getting genre IDs: {str(e)}")
            raise DatabaseError("Failed to get genre IDs")

    def _get_category_ids(self, category_names: List[str]) -> List[int]:
        """Get category IDs from names."""
        try:
            response = (
                self.supabase.table("categories")
                .select("id")
                .in_("name", category_names)
                .execute()
            )
            return [row["id"] for row in response.data] if response.data else []
        except Exception as e:
            logger.error(f"Error getting category IDs: {str(e)}")
            raise DatabaseError("Failed to get category IDs")

    def sign_up(self, email: str, password: str) -> Dict[str, Any]:
        """Sign up a new user."""
        try:
            response = self.supabase.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                }
            )
            if not response:
                raise AuthenticationError("Failed to sign up user")
            return response
        except Exception as e:
            logger.error(f"Error signing up user: {str(e)}")
            raise AuthenticationError(f"Failed to sign up user: {str(e)}")

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Log in an existing user."""
        try:
            response = self.supabase.auth.sign_in_with_password(
                {
                    "email": email,
                    "password": password,
                }
            )

            session = response.session
            if session:
                return {
                    "access_token": session.access_token,
                    "refresh_token": session.refresh_token,
                }

            raise AuthenticationError("Login failed")
        except Exception as e:
            logger.error(f"Error logging in user: {str(e)}")
            raise AuthenticationError("Invalid credentials")

    def get_user_id(self, access_token: str) -> str:
        """Get user ID from access token."""
        try:
            response = self.supabase.auth.get_user(access_token)
            user = response.user
            if not user:
                raise AuthenticationError("User not found")
            return user.id
        except Exception as e:
            logger.error(f"Error getting user ID: {str(e)}")
            raise AuthenticationError("Invalid or expired token")

    def add_progress(
        self,
        access_token: str,
        manhwa_id: int,
        current_chapter: int,
        reading_status: str,
    ) -> List[Dict[str, Any]]:
        """Add progress for a specific manhwa."""
        try:
            user_id = self.get_user_id(access_token)

            # Check if progress already exists
            existing = (
                self.supabase.table("user_manhwa_progress")
                .select("id")
                .eq("user_id", user_id)
                .eq("manhwa_id", manhwa_id)
                .execute()
            )

            if existing.data:
                # Update existing progress
                return self.update_progress(
                    access_token, manhwa_id, current_chapter, reading_status
                )

            # Insert new progress
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
        except AuthenticationError as e:
            raise e
        except Exception as e:
            logger.error(f"Error adding progress: {str(e)}")
            raise DatabaseError("Failed to add progress")

    def update_progress(
        self,
        access_token: str,
        manhwa_id: int,
        current_chapter: int,
        reading_status: str,
    ) -> List[Dict[str, Any]]:
        """Update progress for a specific manhwa."""
        try:
            user_id = self.get_user_id(access_token)
            response = (
                self.supabase.table("user_manhwa_progress")
                .update(
                    {
                        "current_chapter": current_chapter,
                        "status": reading_status,
                    }
                )
                .eq("user_id", user_id)
                .eq("manhwa_id", manhwa_id)
                .execute()
            )
            return response.data if response.data else []
        except AuthenticationError as e:
            raise e
        except Exception as e:
            logger.error(f"Error updating progress: {str(e)}")
            raise DatabaseError("Failed to update progress")

    def get_user_progress(self, access_token: str) -> List[Dict[str, Any]]:
        """Fetch progress for a specific user."""
        try:
            user_id = self.get_user_id(access_token)
            response = (
                self.supabase.table("user_manhwa_progress")
                .select("*, manhwas(name, image_url)")
                .eq("user_id", user_id)
                .execute()
            )
            return response.data if response.data else []
        except AuthenticationError as e:
            raise e
        except Exception as e:
            logger.error(f"Error getting user progress: {str(e)}")
            raise DatabaseError("Failed to get user progress")

    def get_manhwa_progress(self, manhwa_id: str) -> List[Dict[str, Any]]:
        """Fetch progress for a specific manhwa."""
        try:
            response = (
                self.supabase.table("user_manhwa_progress")
                .select("*")
                .eq("manhwa_id", manhwa_id)
                .execute()
            )
            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error getting manhwa progress: {str(e)}")
            raise DatabaseError("Failed to get manhwa progress")

    def refresh_token(self, refresh_token: str) -> Tuple[str, str]:
        """Refresh access token using refresh token."""
        try:
            response = self.supabase.auth.refresh_session(refresh_token)

            if not response or not response.session:
                raise AuthenticationError("Failed to refresh token")

            # Extract new tokens
            new_access_token = response.session.access_token
            new_refresh_token = response.session.refresh_token

            return new_access_token, new_refresh_token
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise AuthenticationError("Invalid or expired refresh token")
