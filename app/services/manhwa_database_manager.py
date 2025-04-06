from typing import List, Optional, Dict, Any
from functools import lru_cache
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.exceptions import DatabaseError, ValidationError
from app.schemas.manhwa import ReadingStatus
from app.services.manhwa_utils import (
    process_manhwa_result,
    validate_filters,
    get_status_ids,
    get_rating_ids,
    get_manhwa_ids_by_genres,
    get_manhwa_ids_by_categories,
    get_user_id,
)

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
        from app.services.manhwa_utils import get_genres

        return get_genres(self.supabase)

    @lru_cache(maxsize=128)
    def get_categories(self) -> List[Dict[str, Any]]:
        """Fetch all categories with name and description."""
        from app.services.manhwa_utils import get_categories

        return get_categories(self.supabase)

    @lru_cache(maxsize=128)
    def get_ratings(self) -> List[Dict[str, Any]]:
        """Fetch all ratings with name and description."""
        from app.services.manhwa_utils import get_ratings

        return get_ratings(self.supabase)

    @lru_cache(maxsize=128)
    def get_statuses(self) -> List[Dict[str, Any]]:
        """Fetch all statuses with name and description."""
        from app.services.manhwa_utils import get_statuses

        return get_statuses(self.supabase)

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
        access_token: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch manhwas based on filters with pagination."""
        try:
            # Validate filters
            validate_filters(self.supabase, genres, categories, status, ratings)

            if access_token:
                user_id = get_user_id(self.supabase, access_token)
                # Build query
                query = (
                    self.supabase.table("manhwas")
                    .select(
                        """
                        *,
                        status(name),
                        rating(name),
                        manhwa_genres!inner(genre_id, genres(name)),
                        manhwa_categories!inner(category_id, categories(name)),
                        user_manhwa_progress(current_chapter, reading_status)
                        """
                    )
                    .eq("user_manhwa_progress.user_id", user_id)
                )  # Filter by the user_id

            else:
                # Build query
                query = self.supabase.table("manhwas").select(
                    "*",
                    "status(name)",
                    "rating(name)",
                    "manhwa_genres!inner(genre_id, genres(name))",
                    "manhwa_categories!inner(category_id, categories(name))",
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
                query = query.in_("status_id", get_status_ids(self.supabase, status))
            if ratings:
                query = query.in_("rating_id", get_rating_ids(self.supabase, ratings))
            if genres:
                query = query.in_("id", get_manhwa_ids_by_genres(self.supabase, genres))
            if categories:
                query = query.in_(
                    "id", get_manhwa_ids_by_categories(self.supabase, categories)
                )

            # Add alphabetical sorting by name
            query = query.order("name")  # Sort by name alphabetically

            # Execute query
            response = query.execute()
            manhwas = response.data if response.data else []
            processed_manhwas = process_manhwa_result(manhwas)
            return processed_manhwas

        except ValidationError as e:
            raise e
        except Exception as e:
            logger.error(f"Error fetching manhwas: {str(e)}")
            raise DatabaseError("Failed to fetch manhwas")

    def get_manhwa_progress(self, manhwa_id: str) -> Dict[str, Any]:
        """Fetch progress for a specific manhwa."""
        try:
            # Default counts for all statuses
            reading_status_counts = {
                reading_status.value: 0 for reading_status in ReadingStatus
            }

            response = self.supabase.rpc(
                "get_manhwa_progress", {"manhwa_id_param": manhwa_id}
            ).execute()

            if response.data:
                for entry in response.data:
                    reading_status_counts[entry["reading_status"]] = entry["count"]

            return reading_status_counts
        except Exception as e:
            logger.error(f"Error getting manhwa progress: {str(e)}")
            raise DatabaseError("Failed to get manhwa progress")
