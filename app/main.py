from fastapi import FastAPI, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from starlette.responses import JSONResponse
from app.routers import sync, manhwa_finder

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Manhwa Finder API",
    description="An API for fetching and filtering manhwa details",
    version="1.0",
)


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429, content={"error": "Too many requests. Try again later."}
    )


# Apply rate limiting globally with middleware
@app.middleware("http")
async def rate_limit(request: Request, call_next):
    # Apply rate limiting to the request using slowapi Limiter
    try:
        # This will check the rate limit and raise RateLimitExceeded if needed
        limiter.hit(request)
    except RateLimitExceeded as e:
        # If rate limit exceeded, it will automatically trigger the exception handler
        raise e

    # Proceed with the request handling
    response = await call_next(request)
    return response


# Add a root route
@app.get("/")
def read_root():
    return {"message": "Welcome to the Manhwa Finder API!"}


# Include routers
app.include_router(manhwa_finder.router)
# This adds routes from sync.py to the app
app.include_router(sync.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True)
