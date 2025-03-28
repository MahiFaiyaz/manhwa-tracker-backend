from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from app.routers import sync, manhwa_finder, health

limiter = Limiter(key_func=get_remote_address, default_limits=["60 per minute"])

app = FastAPI(
    title="Manhwa Finder API",
    description="An API for fetching and filtering manhwa details",
    version="1.0",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


# Add a root route
@app.get("/")
def read_root():
    return {"message": "Welcome to the Manhwa Finder API!"}


@app.get("/", include_in_schema=False)
async def root():
    return RedirectResponse(url="/docs")


# Include routers
app.include_router(manhwa_finder.router)
# This adds routes from sync.py to the app
app.include_router(sync.router)
app.include_router(health.router)
