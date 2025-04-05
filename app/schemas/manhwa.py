from typing import List, Optional
from enum import Enum
from pydantic import BaseModel


class ReadingStatus(str, Enum):
    """Enum for reading status."""

    PLANNING = "planning"
    READING = "reading"
    COMPLETED = "completed"
    DROPPED = "dropped"
    ON_HOLD = "on_hold"


class GenreBase(BaseModel):
    """Base schema for genres."""

    name: str
    description: str


class CategoryBase(BaseModel):
    """Base schema for categories."""

    name: str
    description: str


class RatingBase(BaseModel):
    """Base schema for ratings."""

    name: str
    description: str


class StatusBase(BaseModel):
    """Base schema for statuses."""

    name: str
    description: str


class ManhwaBase(BaseModel):
    """Base schema for manhwas."""

    id: int
    name: str
    synopsis: str
    year_released: int
    chapters: str
    chapter_min: int = 0
    chapter_max: Optional[int] = None
    image_url: Optional[str] = None
    status: str
    rating: str
    genres: List[str]
    categories: List[str]


class UserProgress(BaseModel):
    """Schema for user progress."""

    manhwa_id: int
    current_chapter: int
    status: ReadingStatus


class ManhwaFilter(BaseModel):
    """Schema for filtering manhwas."""

    genres: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    min_chapters: Optional[int] = None
    max_chapters: Optional[int] = None
    min_year_released: Optional[int] = None
    max_year_released: Optional[int] = None
    status: Optional[List[str]] = None
    ratings: Optional[List[str]] = None


class ManhwaProgressResponse(BaseModel):
    """Response model for manhwa progress statistics."""

    planning: int = 0
    reading: int = 0
    completed: int = 0
    dropped: int = 0
    on_hold: int = 0


class ManhwaWithProgress(BaseModel):
    """Schema for manhwa with user progress."""

    current_chapter: int
    status: ReadingStatus
    manhwa: ManhwaBase
