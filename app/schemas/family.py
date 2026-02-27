from pydantic import BaseModel
from typing import Optional, List

class IndividualBase(BaseModel):
    name: str
    gender: str
    birth_date: Optional[str] = None

class IndividualCreate(IndividualBase):
    pass

class Individual(IndividualBase):
    id: int

    class Config:
        orm_mode = True

class RelationshipCreate(BaseModel):
    parent_id: int
    child_id: int
    type: str = 'biological'