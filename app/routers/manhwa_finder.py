from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from app.services.manhwa_database_manager import ManhwaDatabaseManager

router = APIRouter()


def get_db_manager():
    return ManhwaDatabaseManager()


@router.get("/genres")
def get_genres(db: ManhwaDatabaseManager = Depends(get_db_manager)):
    return db.get_genres()


@router.get("/categories")
def get_categories(db: ManhwaDatabaseManager = Depends(get_db_manager)):
    return db.get_categories()


@router.get("/ratings")
def get_ratings(db: ManhwaDatabaseManager = Depends(get_db_manager)):
    return db.get_ratings()


@router.get("/statuses")
def get_statuses(db: ManhwaDatabaseManager = Depends(get_db_manager)):
    return db.get_statuses()


@router.get("/manhwas")
def get_all_manhwas(db: ManhwaDatabaseManager = Depends(get_db_manager)):
    return db.get_all_manhwas()


@router.get("/manhwas/filter")
def get_filtered_manhwas(
    genres: Optional[List[str]] = Query(None),
    categories: Optional[List[str]] = Query(None),
    min_chapters: Optional[int] = None,
    max_chapters: Optional[int] = None,
    year_released: Optional[int] = None,
    status: Optional[List[str]] = Query(None),
    ratings: Optional[List[str]] = Query(None),
    db: ManhwaDatabaseManager = Depends(get_db_manager),
):
    return db.get_filtered_manhwas(
        genres=genres,
        categories=categories,
        min_chapters=min_chapters,
        max_chapters=max_chapters,
        year_released=year_released,
        status=status,
        ratings=ratings,
    )
