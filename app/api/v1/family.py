from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models.family import Individual, Relationship, Marriage
from app import schemas
from typing import List

router = APIRouter()

@router.post("/individuals/", response_model=schemas.Individual)
def create_individual(ind: schemas.IndividualCreate, db: Session = Depends(get_db)):
    person = Individual(name=ind.name, gender=ind.gender, birth_date=ind.birth_date)
    db.add(person)
    db.commit()
    db.refresh(person)
    return person

@router.get("/individuals/", response_model=List[schemas.Individual])
def list_individuals(db: Session = Depends(get_db)):
    individuals = db.query(Individual).all()
    return individuals

@router.get("/individuals/{individual_id}", response_model=schemas.Individual)
def get_individual(individual_id: int, db: Session = Depends(get_db)):
    person = db.query(Individual).filter(Individual.id == individual_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Individual not found")
    return person

@router.put("/individuals/{individual_id}", response_model=schemas.Individual)
def update_individual(individual_id: int, ind: schemas.IndividualCreate, db: Session = Depends(get_db)):
    person = db.query(Individual).filter(Individual.id == individual_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Individual not found")
    person.name = ind.name
    person.gender = ind.gender
    person.birth_date = ind.birth_date
    db.commit()
    db.refresh(person)
    return person

@router.delete("/individuals/{individual_id}")
def delete_individual(individual_id: int, db: Session = Depends(get_db)):
    person = db.query(Individual).filter(Individual.id == individual_id).first()
    if not person:
        raise HTTPException(status_code=404, detail="Individual not found")
    db.delete(person)
    db.commit()
    return {"message": f"Individual {individual_id} deleted successfully"}