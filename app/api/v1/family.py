from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app import models, schemas

router = APIRouter()

@router.post("/individuals/", response_model=schemas.Individual)
def create_individual(ind: schemas.IndividualCreate, db: Session = Depends(get_db)):
    person = models.Individual(name=ind.name, gender=ind.gender, birth_date=ind.birth_date)
    db.add(person)
    db.commit()
    db.refresh(person)
    return person