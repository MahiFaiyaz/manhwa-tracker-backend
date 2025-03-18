from fastapi import FastAPI
from app.routers import sync, manhwa_finder

app = FastAPI()

app.include_router(manhwa_finder.router)
app.include_router(sync.router)  # This adds the /sync route
