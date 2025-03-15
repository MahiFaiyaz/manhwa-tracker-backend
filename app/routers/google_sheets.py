from fastapi import APIRouter
from app.services.google_sheets_service import fetch_sheet_data

router = APIRouter(prefix="/sheets", tags=["Google Sheets"])


@router.get("/{sheet_id}/{sheet_range}")
def get_sheet_data(sheet_id: str, sheet_range: str):
    return fetch_sheet_data(sheet_id, sheet_range)


@router.get("/my_first_api")
def get_sheet_data(sheet_id: str, sheet_range: str):
    return fetch_sheet_data(sheet_id, sheet_range)
