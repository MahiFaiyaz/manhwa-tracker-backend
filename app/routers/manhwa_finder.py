from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from app.services.manhwa_database_manager import ManhwaDatabaseManager

router = APIRouter()


def get_db_manager():
    return ManhwaDatabaseManager()


@router.get("/genres", tags=["Manhwa-Finder"])
def get_genres(db: ManhwaDatabaseManager = Depends(get_db_manager)):
    return db.get_genres()


@router.get("/categories", tags=["Manhwa-Finder"])
def get_categories(db: ManhwaDatabaseManager = Depends(get_db_manager)):
    return db.get_categories()


@router.get("/ratings", tags=["Manhwa-Finder"])
def get_ratings(db: ManhwaDatabaseManager = Depends(get_db_manager)):
    return db.get_ratings()


@router.get("/statuses", tags=["Manhwa-Finder"])
def get_statuses(db: ManhwaDatabaseManager = Depends(get_db_manager)):
    return db.get_statuses()


@router.get("/manhwas", tags=["Manhwa-Finder"])
def get_manhwas(
    genres: Optional[List[str]] = Query(None),
    categories: Optional[List[str]] = Query(None),
    min_chapters: Optional[int] = None,
    max_chapters: Optional[int] = None,
    min_year_released: Optional[int] = None,
    max_year_released: Optional[int] = None,
    status: Optional[List[str]] = Query(None),
    ratings: Optional[List[str]] = Query(None),
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
    )
