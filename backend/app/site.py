# app/site.py

from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

INDEX_FILE = Path(__file__).parent / "static" / "index.html"


@router.get(
    "/app",
    response_class=HTMLResponse,
    include_in_schema=False,
)
def patient_site():
    return INDEX_FILE.read_text(encoding="utf-8")
