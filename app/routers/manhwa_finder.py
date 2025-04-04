from fastapi import APIRouter, Depends, Query
from typing import List, Optional, Dict, Any
from app.services.manhwa_database_manager import ManhwaDatabaseManager
from app.schemas.manhwa import (
    GenreBase,
    CategoryBase,
    RatingBase,
    StatusBase,
    ManhwaBase,
)
from app.core.exceptions import DatabaseError, ValidationError

router = APIRouter(tags=["Manhwa-Finder"])


def get_db_manager():
    return ManhwaDatabaseManager()


@router.get("/genres", response_model=List[GenreBase])
def get_genres(db: ManhwaDatabaseManager = Depends(get_db_manager)):
    try:
        return db.get_genres()
    except Exception as e:
        raise DatabaseError(f"Failed to retrieve genres: {str(e)}")


@router.get("/categories", response_model=List[CategoryBase])
def get_categories(db: ManhwaDatabaseManager = Depends(get_db_manager)):
    try:
        return db.get_categories()
    except Exception as e:
        raise DatabaseError(f"Failed to retrieve categories: {str(e)}")


@router.get("/ratings", response_model=List[RatingBase])
def get_ratings(db: ManhwaDatabaseManager = Depends(get_db_manager)):
    try:
        return db.get_ratings()
    except Exception as e:
        raise DatabaseError(f"Failed to retrieve ratings: {str(e)}")


@router.get("/statuses", response_model=List[StatusBase])
def get_statuses(db: ManhwaDatabaseManager = Depends(get_db_manager)):
    try:
        return db.get_statuses()
    except Exception as e:
        raise DatabaseError(f"Failed to retrieve statuses: {str(e)}")


@router.get(
    "/manhwas",
    response_model=Dict[str, Any],  # For pagination metadata
)
def get_manhwas(
    genres: Optional[List[str]] = Query(None),
    categories: Optional[List[str]] = Query(None),
    min_chapters: Optional[int] = None,
    max_chapters: Optional[int] = None,
    min_year_released: Optional[int] = None,
    max_year_released: Optional[int] = None,
    status: Optional[List[str]] = Query(None),
    ratings: Optional[List[str]] = Query(None),
    page: int = 1,
    per_page: int = 20,
    db: ManhwaDatabaseManager = Depends(get_db_manager),
):
    # Input validation
    if page < 1:
        raise ValidationError("Page number must be greater than 0")
    if per_page < 1 or per_page > 100:
        raise ValidationError("Items per page must be between 1 and 100")
    if min_chapters is not None and min_chapters < 0:
        raise ValidationError("Minimum chapters cannot be negative")
    if max_chapters is not None and max_chapters < 0:
        raise ValidationError("Maximum chapters cannot be negative")
    if (
        min_year_released is not None
        and max_year_released is not None
        and min_year_released > max_year_released
    ):
        raise ValidationError(
            "Minimum year released cannot be greater than maximum year released"
        )

    try:
        # This should return a dict with data and pagination info
        # The 'data' key should contain a list of ManhwaBase objects
        result = db.get_manhwas(
            genres=genres,
            categories=categories,
            min_chapters=min_chapters,
            max_chapters=max_chapters,
            min_year_released=min_year_released,
            max_year_released=max_year_released,
            status=status,
            ratings=ratings,
            page=page,
            per_page=per_page,
        )

        # Ensure the result includes needed pagination metadata
        if not isinstance(result, dict) or "data" not in result:
            # Convert to proper format if database manager doesn't do it
            result = {
                "data": result,
                "page": page,
                "per_page": per_page,
                "total": len(result) if result else 0,
            }

        return result
    except Exception as e:
        raise DatabaseError(f"Failed to retrieve manhwas: {str(e)}")


@router.get("/manhwa/{manhwa_id}", response_model=ManhwaBase)
def get_manhwa(manhwa_id: int, db: ManhwaDatabaseManager = Depends(get_db_manager)):
    try:
        result = db.get_manhwa(manhwa_id)
        if not result:
            raise ValidationError(f"Manhwa with ID {manhwa_id} not found")
        return result
    except ValidationError as e:
        raise e
    except Exception as e:
        raise DatabaseError(f"Failed to retrieve manhwa: {str(e)}")
