from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from supabase import PostgrestAPIError
from app.core.logging import get_logger

logger = get_logger("exceptions")


class DatabaseError(Exception):
    """Exception raised for database errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class AuthenticationError(Exception):
    """Exception raised for authentication errors."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ValidationError(Exception):
    """Exception raised for validation errors."""

    def __init__(self, message: str, details: dict = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)


def setup_exception_handlers(app: FastAPI) -> None:
    """Set up exception handlers for the application."""

    @app.exception_handler(DatabaseError)
    async def database_exception_handler(request: Request, exc: DatabaseError):
        logger.error(f"Database error: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Database error", "message": exc.message},
        )

    @app.exception_handler(AuthenticationError)
    async def auth_exception_handler(request: Request, exc: AuthenticationError):
        logger.error(f"Authentication error: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"error": "Authentication error", "message": exc.message},
        )

    @app.exception_handler(ValidationError)
    async def validation_exception_handler(request: Request, exc: ValidationError):
        logger.error(f"Validation error: {exc.message}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "error": "Validation error",
                "message": exc.message,
                "details": exc.details,
            },
        )

    @app.exception_handler(PostgrestAPIError)
    async def postgrest_exception_handler(request: Request, exc: PostgrestAPIError):
        logger.error(f"Supabase error: {str(exc)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"error": "Database operation failed", "message": str(exc)},
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "message": "An unexpected error occurred",
            },
        )
