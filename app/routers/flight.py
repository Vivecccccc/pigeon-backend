from fastapi import APIRouter

from models.search_data import SearchData, SearchType
from utils.process_text import extract_entry


router = APIRouter()

@router.post("/search")
async def departure(data: SearchData):
    if data.type == SearchType.TEXT:
        focuses = extract_entry(data.content, closed=True, excluded_types=["位置", "菜品"])
    else:
        raise NotImplementedError
    return focuses