from fastapi import UploadFile
from pydantic import BaseModel, Field, root_validator, validator
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

    @validator("content")
    def _uploadfile_is_img(cls, val):
        if isinstance(val, str):
            return val
        if val.content_type not in ["image/png", "image/jpeg"]:
            raise ValueError("input file type not accepted")
        return val
    
    @root_validator(pre=True)
    def _content_type_match_type(cls, val):
        type, content = val.get("type"), val.get("content")
        if type is None or content is None:
            raise ValueError("nonetype was passed")
        if ((type == SearchType.TEXT.value) ^ isinstance(content, str)) == 1 \
        or ((type == SearchType.IMG.value) ^ isinstance(content, UploadFile)) == 1:
            raise ValueError("input type does not match")
        return val
    
class AppendData(BaseModel):
    focuses: List[Focus]
    set_scope: Optional[List[str]]