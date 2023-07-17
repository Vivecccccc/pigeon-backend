from pydantic import BaseModel, root_validator
from typing import List, Optional

class Loc(BaseModel):
    location: str
    name: str
    id: str

class Focus(BaseModel):
    elem: str
    flag: bool
    begin: bool

class FocusLoc(Focus):
    loc: Optional[List[Loc]]

    @root_validator
    def _flag_loc_check(cls, val):
        if val.get("loc") is None:
            val["flag"] = False
            val["begin"] = False
            # TODO
            # ins.searched = False
        return val

class Preflight(BaseModel):
    focuses: List[FocusLoc]
    assume_scope: Optional[List[str]]

class Flight(BaseModel):
    focuses: List[FocusLoc]
    set_scope: Optional[List[str]]
