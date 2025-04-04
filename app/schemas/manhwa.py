from typing import List, Optional
from enum import Enum
from pydantic import BaseModel, Field


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
    status: StatusBase
    rating: RatingBase
    genres: List[str]
    categories: List[str]


class UserProgressCreate(BaseModel):
    """Schema for creating user progress."""

    manhwa_id: int
    current_chapter: int
    reading_status: ReadingStatus


class UserProgressUpdate(BaseModel):
    """Schema for updating user progress."""

    current_chapter: int
    reading_status: ReadingStatus


class UserProgress(BaseModel):
    """Schema for user progress."""

    user_id: str
    manhwa_id: int
    current_chapter: int
    status: ReadingStatus
