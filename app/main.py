from fastapi import FastAPI

from app.routers import sync, manhwa_finder

app = FastAPI(
    title="Manhwa Finder API",
    description="An API for fetching and filtering manhwa details",
    version="1.0",
)


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
