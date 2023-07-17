from fastapi import APIRouter

from models.search_data import SearchData, SearchType
from utils.process_text import extract_entry
from utils.utils import postprocessing
from utils.locate import estimate_scope_and_anchors, fetch_location


router = APIRouter()

@router.post("/search")
async def departure(data: SearchData):
    if data.type == SearchType.TEXT:
        entities = extract_entry(data.content, closed=True)
    else:
        raise NotImplementedError
    emerged_loc = [ent["text"] for _, ent_list in entities for ent in ent_list if ent["type"] == "位置"]
    scope = data.preset_scope if data.preset_scope is not None else []
    anchors = estimate_scope_and_anchors(emerged_loc, scope)
    print(anchors)
    focuses = postprocessing(entities, excludes=["位置", "菜品"])
    fetch_location(focuses, anchors)
    return focuses