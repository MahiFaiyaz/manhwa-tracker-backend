from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.routers import sync, manhwa_finder, health, users, refresh_token
from app.core.settings import get_settings
from app.core.logging import get_logger
from app.core.exceptions import setup_exception_handlers
from app.middleware.logging_middleware import LoggingMiddleware

settings = get_settings()
logger = get_logger("app")

limiter = Limiter(
    key_func=get_remote_address, default_limits=[settings.DEFAULT_RATE_LIMIT]
)

app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
)

# Set up exception handlers
setup_exception_handlers(app)

# Set up rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add middlewares
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(LoggingMiddleware)


# Root API
@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


# Include routers
app.include_router(manhwa_finder.router)
app.include_router(sync.router)
app.include_router(health.router)
app.include_router(users.router)
app.include_router(refresh_token.router)


@app.on_event("startup")
async def startup_event():
    logger.info("Application starting up")


@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Application shutting down")
