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
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware


settings = get_settings()
logger = get_logger("app")

limiter = Limiter(
    key_func=get_remote_address, default_limits=[settings.DEFAULT_RATE_LIMIT]
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up")
    yield
    logger.info("Application shutting down")


app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
    lifespan=lifespan,
)

# Set up exception handlers
setup_exception_handlers(app)

# Set up rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add middlewares
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://manhwa-tracker-565ed.web.app",  # ✅ your live Flutter app
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
