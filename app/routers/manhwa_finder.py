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

router = APIRouter(tags=["Manhwa-Finder"])


def get_db_manager():
    return ManhwaDatabaseManager()


@router.get("/genres", response_model=List[GenreBase])
def get_genres(db: ManhwaDatabaseManager = Depends(get_db_manager)):
    return db.get_genres()


@router.get("/categories", response_model=List[CategoryBase])
def get_categories(db: ManhwaDatabaseManager = Depends(get_db_manager)):
    return db.get_categories()


@router.get("/ratings", response_model=List[RatingBase])
def get_ratings(db: ManhwaDatabaseManager = Depends(get_db_manager)):
    return db.get_ratings()


@router.get("/statuses", response_model=List[StatusBase])
def get_statuses(db: ManhwaDatabaseManager = Depends(get_db_manager)):
    return db.get_statuses()


@router.get(
    "/manhwas", response_model=Dict[str, Any]
)  # Custom dict response for pagination
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
    return db.get_manhwas(
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
