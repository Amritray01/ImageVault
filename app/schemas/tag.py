from pydantic import BaseModel, ConfigDict, Field
from typing import Optional

class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50, description="Tag name")
    color: Optional[str] = Field("#6366f1", max_length=20, description="Hex color code")

class TagCreate(TagBase):
    pass

class TagResponse(TagBase):
    id: int
    model_config = ConfigDict(from_attributes=True)
