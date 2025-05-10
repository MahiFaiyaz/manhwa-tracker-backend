from typing import List, Dict, Any, Optional
from app.core.logging import get_logger
from app.core.exceptions import DatabaseError, ValidationError, AuthenticationError
from collections import Counter

logger = get_logger("manhwa_utils")


def process_manhwa_result(manhwas) -> List[Dict[str, Any]]:
    """Process and normalize manhwa results from database queries."""
    processed = []

    for item in manhwas:
        # Check if this is the progress-wrapped format (case 2)
        if "manhwas" in item:
            manhwa_data = item["manhwas"]
            current_chapter = item.get("current_chapter", 0)
            reading_status = item.get("reading_status", "not_read")
        else:
            manhwa_data = item
            # Try to get progress info from user_manhwa_progress if present
            progress = manhwa_data.get("user_manhwa_progress", [])
            if progress and isinstance(progress, list):
                current_chapter = progress[0].get("current_chapter", 0)
                reading_status = progress[0].get("reading_status", "not_read")
            else:
                current_chapter = 0
                reading_status = "not_read"

        # Build manhwa sub-object (normalized)
        manhwa_data["genres"] = [
            g["genres"]["name"] for g in manhwa_data.get("manhwa_genres", [])
        ]
        manhwa_data["categories"] = [
            c["categories"]["name"] for c in manhwa_data.get("manhwa_categories", [])
        ]
        manhwa_data["rating"] = manhwa_data.get("rating", {}).get("name")
        manhwa_data["status"] = manhwa_data.get("status", {}).get("name")

        # Clean up unnecessary fields
        for key in [
            "manhwa_genres",
            "manhwa_categories",
            "status_id",
            "rating_id",
            "created_at",
            "user_manhwa_progress",
        ]:
            manhwa_data.pop(key, None)

        # Append in ManhwaWithProgress format
        processed.append(
            {
                "current_chapter": current_chapter,
                "reading_status": reading_status,
                "manhwa": manhwa_data,
            }
        )
    return processed


def validate_filters(
    supabase,
    genres: Optional[List[str]] = None,
    categories: Optional[List[str]] = None,
    status: Optional[List[str]] = None,
    ratings: Optional[List[str]] = None,
) -> None:
    """Validate filter parameters against database values."""
    invalid_filters = {}

    # Get valid names from corresponding tables
    valid_genres = {g["name"] for g in get_genres(supabase)}
    valid_categories = {c["name"] for c in get_categories(supabase)}
    valid_statuses = {s["name"] for s in get_statuses(supabase)}
    valid_ratings = {r["name"] for r in get_ratings(supabase)}

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


def get_genres(supabase) -> List[Dict[str, Any]]:
    """Fetch all genres with name and description."""
    try:
        response = supabase.table("genres").select("name, description").execute()
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Error fetching genres: {str(e)}")
        raise DatabaseError("Failed to fetch genres")


def get_categories(supabase) -> List[Dict[str, Any]]:
    """Fetch all categories with name and description."""
    try:
        response = supabase.table("categories").select("name, description").execute()
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Error fetching categories: {str(e)}")
        raise DatabaseError("Failed to fetch categories")


def get_ratings(supabase) -> List[Dict[str, Any]]:
    """Fetch all ratings with name and description."""
    try:
        response = supabase.table("rating").select("name, description").execute()
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Error fetching ratings: {str(e)}")
        raise DatabaseError("Failed to fetch ratings")


def get_statuses(supabase) -> List[Dict[str, Any]]:
    """Fetch all statuses with name and description."""
    try:
        response = supabase.table("status").select("name, description").execute()
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Error fetching statuses: {str(e)}")
        raise DatabaseError("Failed to fetch statuses")


def get_status_ids(supabase, status_names: List[str]) -> List[int]:
    """Get status IDs from names."""
    try:
        response = (
            supabase.table("status").select("id").in_("name", status_names).execute()
        )
        return [row["id"] for row in response.data] if response.data else []
    except Exception as e:
        logger.error(f"Error getting status IDs: {str(e)}")
        raise DatabaseError("Failed to get status IDs")


def get_rating_ids(supabase, rating_names: List[str]) -> List[int]:
    """Get rating IDs from names."""
    try:
        response = (
            supabase.table("rating").select("id").in_("name", rating_names).execute()
        )
        return [row["id"] for row in response.data] if response.data else []
    except Exception as e:
        logger.error(f"Error getting rating IDs: {str(e)}")
        raise DatabaseError("Failed to get rating IDs")


def get_genre_ids(supabase, genre_names: List[str]) -> List[int]:
    """Get genre IDs from names."""
    try:
        response = (
            supabase.table("genres").select("id").in_("name", genre_names).execute()
        )
        return [row["id"] for row in response.data] if response.data else []
    except Exception as e:
        logger.error(f"Error getting genre IDs: {str(e)}")
        raise DatabaseError("Failed to get genre IDs")


def get_category_ids(supabase, category_names: List[str]) -> List[int]:
    """Get category IDs from names."""
    try:
        response = (
            supabase.table("categories")
            .select("id")
            .in_("name", category_names)
            .execute()
        )
        return [row["id"] for row in response.data] if response.data else []
    except Exception as e:
        logger.error(f"Error getting category IDs: {str(e)}")
        raise DatabaseError("Failed to get category IDs")


def get_manhwa_ids_by_genres(supabase, genres: List[str]) -> List[int]:
    """Get manhwa IDs by genre names."""
    try:
        genre_ids = get_genre_ids(supabase, genres)
        response = (
            supabase.table("manhwa_genres")
            .select("manhwa_id, genre_id")
            .in_("genre_id", genre_ids)
            .execute()
        )
        if not response.data:
            return []

        manhwa_ids = [row["manhwa_id"] for row in response.data]
        count = Counter(manhwa_ids)

        # Return only manhwas that matched *all* selected genres
        return [manhwa_id for manhwa_id, c in count.items() if c == len(genre_ids)]
    except Exception as e:
        logger.error(f"Error getting manhwa IDs by genres: {str(e)}")
        raise DatabaseError("Failed to get manhwa IDs by genres")


def get_manhwa_ids_by_categories(supabase, categories: List[str]) -> List[int]:
    """Get manhwa IDs by category names."""
    try:
        category_ids = get_category_ids(supabase, categories)
        response = (
            supabase.table("manhwa_categories")
            .select("manhwa_id, category_id")
            .in_("category_id", category_ids)
            .execute()
        )
        if not response.data:
            return []

        manhwa_ids = [row["manhwa_id"] for row in response.data]
        count = Counter(manhwa_ids)

        # Return only manhwas that matched *all* selected genres
        return [manhwa_id for manhwa_id, c in count.items() if c == len(category_ids)]
    except Exception as e:
        logger.error(f"Error getting manhwa IDs by categories: {str(e)}")
        raise DatabaseError("Failed to get manhwa IDs by categories")


def get_user_id(supabase, access_token: str) -> str:
    """Get user ID from access token."""
    try:
        response = supabase.auth.get_user(access_token)
        user = response.user
        if not user:
            raise AuthenticationError("User not found")
        return user.id
    except Exception as e:
        logger.error(f"Error getting user ID: {str(e)}")
        raise AuthenticationError("Invalid or expired token")
