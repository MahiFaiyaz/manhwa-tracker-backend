from typing import List, Dict, Any, Tuple
from app.core.database import get_db
from app.core.logging import get_logger
from app.core.exceptions import DatabaseError, AuthenticationError
from app.services.manhwa_utils import process_manhwa_result, get_user_id

logger = get_logger("user_auth_manager")


class UserAuthManager:
    """Manager for user authentication and progress tracking."""

    def sign_up(self, email: str, password: str) -> Dict[str, Any]:
        """Sign up a new user."""
        try:
            with get_db() as supabase:
                response = supabase.auth.sign_up({"email": email, "password": password})
            if not response:
                raise AuthenticationError("Failed to sign up user")
            return response
        except Exception as e:
            logger.error(f"Error signing up user: {str(e)}")
            raise AuthenticationError(f"Failed to sign up user: {str(e)}")

    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Log in an existing user."""
        try:
            with get_db() as supabase:
                response = supabase.auth.sign_in_with_password(
                    {"email": email, "password": password}
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

    def add_progress(
        self,
        access_token: str,
        manhwa_id: int,
        current_chapter: int,
        reading_status: str,
    ) -> List[Dict[str, Any]]:
        """Add progress for a specific manhwa."""
        try:
            with get_db() as supabase:
                user_id = get_user_id(supabase, access_token)

                existing = (
                    supabase.table("user_manhwa_progress")
                    .select("*")
                    .eq("user_id", user_id)
                    .eq("manhwa_id", manhwa_id)
                    .execute()
                )

                if existing.data:
                    return self.update_progress(
                        access_token, manhwa_id, current_chapter, reading_status
                    )

                response = (
                    supabase.table("user_manhwa_progress")
                    .insert(
                        {
                            "user_id": user_id,
                            "manhwa_id": manhwa_id,
                            "current_chapter": current_chapter,
                            "reading_status": reading_status,
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
            with get_db() as supabase:
                user_id = get_user_id(supabase, access_token)
                response = (
                    supabase.table("user_manhwa_progress")
                    .update(
                        {
                            "current_chapter": current_chapter,
                            "reading_status": reading_status,
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
            with get_db() as supabase:
                user_id = get_user_id(supabase, access_token)
                response = (
                    supabase.table("user_manhwa_progress")
                    .select(
                        """
                        current_chapter,
                        reading_status,
                        manhwas (
                            *,
                            status(name),
                            rating(name),
                            manhwa_genres!inner(genre_id, genres(name)),
                            manhwa_categories!inner(category_id, categories(name))
                        )
                        """
                    )
                    .eq("user_id", user_id)
                    .execute()
                )
                return process_manhwa_result(response.data)
        except AuthenticationError as e:
            raise e
        except Exception as e:
            logger.error(f"Error getting user progress: {str(e)}")
            raise DatabaseError("Failed to get user progress")

    def refresh_token(self, refresh_token: str) -> Tuple[str, str]:
        """Refresh access token using refresh token."""
        try:
            with get_db() as supabase:
                response = supabase.auth.refresh_session(refresh_token)

                if not response or not response.session:
                    raise AuthenticationError("Failed to refresh token")

                return (
                    response.session.access_token,
                    response.session.refresh_token,
                )
        except Exception as e:
            logger.error(f"Error refreshing token: {str(e)}")
            raise AuthenticationError("Invalid or expired refresh token")
