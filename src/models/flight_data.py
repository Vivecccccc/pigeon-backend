from pydantic import BaseModel, model_validator
from typing import List, Optional

class Loc(BaseModel):
    lat: float
    long: float

class Focus(BaseModel):
    elem: str
    flag: bool

class FocusLoc(Focus):
    loc: Optional[Loc]

    @model_validator
    def _flag_loc_check(cls, ins: "FocusLoc"):
        if ins.loc is None:
            ins.flag = False
            # TODO
            # ins.searched = False
        return ins

class Preflight(BaseModel):
    focuses: List[FocusLoc]
    assume_scope: Optional[List[str]]

class Flight(BaseModel):
    focuses: List[FocusLoc]
    set_scope: Optional[List[str]]
