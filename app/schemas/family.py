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
        from_attributes = True

class RelationshipBase(BaseModel):
    parent_id: int
    child_id: int
    type: str = 'biological'


class RelationshipCreate(RelationshipBase):
    pass


class Relationship(RelationshipBase):
    id: int

    class Config:
        from_attributes = True