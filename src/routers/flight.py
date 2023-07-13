from fastapi import APIRouter

from models.search_data import SearchData, SearchType
from utils.process_text import extract_entry


router = APIRouter()

@router.post("/search")
async def departure(data: SearchData):
    if data.type == SearchType.TEXT:
        _ = extract_entry(data.content, closed=False)
    else:
        pass