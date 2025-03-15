from fastapi import FastAPI
from app.routers import google_sheets

app = FastAPI(title="Manhwa Tracker API")

app.include_router(google_sheets.router)


@app.get("/")
def home():
    return {"message": "API is running"}
