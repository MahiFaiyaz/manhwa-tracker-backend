from fastapi import APIRouter, Depends, Query
from typing import List, Optional, Dict, Any
from app.services.manhwa_database_manager import ManhwaDatabaseManager
from app.schemas.manhwa import (
    GenreBase,
    CategoryBase,
    RatingBase,
    StatusBase,
    ManhwaFilter,
)
from app.core.exceptions import DatabaseError, ValidationError
from app.core.dependencies import get_db_manager

router = APIRouter(tags=["Manhwa-Finder"])


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


@router.post(
    "/manhwas",
    response_model=Dict[str, Any],  # For pagination metadata
)
def get_manhwas(
    filter: ManhwaFilter,
    db: ManhwaDatabaseManager = Depends(get_db_manager),
):
    # Input validation
    if filter.min_chapters is not None and filter.min_chapters < 0:
        raise ValidationError("Minimum chapters cannot be negative")
    if filter.max_chapters is not None and filter.max_chapters < 0:
        raise ValidationError("Maximum chapters cannot be negative")
    if (
        filter.min_year_released is not None
        and filter.max_year_released is not None
        and filter.min_year_released > filter.max_year_released
    ):
        raise ValidationError(
            "Minimum year released cannot be greater than maximum year released"
        )

    try:
        # This should return a dict with data and pagination info
        # The 'data' key should contain a list of ManhwaBase objects
        result = db.get_manhwas(
            genres=filter.genres,
            categories=filter.categories,
            min_chapters=filter.min_chapters,
            max_chapters=filter.max_chapters,
            min_year_released=filter.min_year_released,
            max_year_released=filter.max_year_released,
            status=filter.status,
            ratings=filter.ratings,
        )

        return result
    except ValidationError as e:
        raise e
    except Exception as e:
        raise DatabaseError(f"Failed to retrieve manhwas: {str(e)}")
