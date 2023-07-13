from fastapi import UploadFile
from pydantic import BaseModel, Field, model_validator, field_validator
from enum import Enum
from typing import List, Optional, Union

from models.flight_data import Focus

class SearchType(Enum):
    TEXT = 0
    IMG = 1
    # TODO
    # LINK = -1

class SearchData(BaseModel):
    type: SearchType
    content: Union[str, UploadFile] = Field(...)
    # TODO
    preset_scope: Optional[List[str]]

    @field_validator("content")
    def _uploadfile_is_img(cls, val):
        if isinstance(val, str):
            return val
        if val.content_type not in ["image/png", "image/jpeg"]:
            raise ValueError("input file type not accepted")
        return val
    
    @model_validator(mode="before")
    def _content_type_match_type(cls, ins: "SearchData"):
        type, content = ins.type, ins.content
        if type is None or content is None:
            raise ValueError("nonetype was passed")
        if (type == SearchType.TEXT ^ isinstance(content, str)) == 1 \
        or (type == SearchType.IMG ^ isinstance(content, UploadFile)) == 1:
            raise ValueError("input type does not match")
        return ins
    
class AppendData(BaseModel):
    focuses: List[Focus]
    set_scope: Optional[List[str]]