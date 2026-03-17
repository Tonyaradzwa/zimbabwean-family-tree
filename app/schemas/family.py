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


class MarriageBase(BaseModel):
    partner1_id: int
    partner2_id: int
    date: Optional[str] = None


class MarriageCreate(MarriageBase):
    pass


class Marriage(MarriageBase):
    id: int

    class Config:
        from_attributes = True


class KinshipResult(BaseModel):
    person_id: int
    relative_id: int
    english_relationship: str
    shona_relationship: str


class QueryRequest(BaseModel):
    query: str


class QueryResponse(BaseModel):
    query: str
    subject_name: Optional[str] = None
    subject_id: Optional[int] = None
    relationship_asked: Optional[str] = None
    answer: str