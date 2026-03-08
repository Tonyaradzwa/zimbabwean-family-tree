from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
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


@router.post("/relationships/", response_model=schemas.Relationship)
def create_relationship(rel: schemas.RelationshipCreate, db: Session = Depends(get_db)):
    if rel.parent_id == rel.child_id:
        raise HTTPException(status_code=400, detail="Parent and child must be different individuals")

    parent = db.query(Individual).filter(Individual.id == rel.parent_id).first()
    if not parent:
        raise HTTPException(status_code=404, detail="Parent not found")

    child = db.query(Individual).filter(Individual.id == rel.child_id).first()
    if not child:
        raise HTTPException(status_code=404, detail="Child not found")

    relationship = Relationship(parent_id=rel.parent_id, child_id=rel.child_id, type=rel.type)
    db.add(relationship)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Relationship already exists")

    db.refresh(relationship)
    return relationship


@router.get("/relationships/", response_model=List[schemas.Relationship])
def list_relationships(db: Session = Depends(get_db)):
    relationships = db.query(Relationship).all()
    return relationships


@router.get("/relationships/{relationship_id}", response_model=schemas.Relationship)
def get_relationship(relationship_id: int, db: Session = Depends(get_db)):
    relationship = db.query(Relationship).filter(Relationship.id == relationship_id).first()
    if not relationship:
        raise HTTPException(status_code=404, detail="Relationship not found")
    return relationship


@router.delete("/relationships/{relationship_id}")
def delete_relationship(relationship_id: int, db: Session = Depends(get_db)):
    relationship = db.query(Relationship).filter(Relationship.id == relationship_id).first()
    if not relationship:
        raise HTTPException(status_code=404, detail="Relationship not found")

    db.delete(relationship)
    db.commit()
    return {"message": f"Relationship {relationship_id} deleted successfully"}


@router.post("/marriages/", response_model=schemas.Marriage)
def create_marriage(mar: schemas.MarriageCreate, db: Session = Depends(get_db)):
    if mar.partner1_id == mar.partner2_id:
        raise HTTPException(status_code=400, detail="Marriage partners must be different individuals")

    partner1 = db.query(Individual).filter(Individual.id == mar.partner1_id).first()
    if not partner1:
        raise HTTPException(status_code=404, detail="Partner 1 not found")

    partner2 = db.query(Individual).filter(Individual.id == mar.partner2_id).first()
    if not partner2:
        raise HTTPException(status_code=404, detail="Partner 2 not found")

    # Marriage is symmetric, so treat (A, B) as duplicate of (B, A).
    existing_marriage = db.query(Marriage).filter(
        or_(
            and_(Marriage.partner1_id == mar.partner1_id, Marriage.partner2_id == mar.partner2_id),
            and_(Marriage.partner1_id == mar.partner2_id, Marriage.partner2_id == mar.partner1_id),
        )
    ).first()
    if existing_marriage:
        raise HTTPException(status_code=400, detail="Marriage already exists")

    marriage = Marriage(partner1_id=mar.partner1_id, partner2_id=mar.partner2_id, date=mar.date)
    db.add(marriage)
    db.commit()
    db.refresh(marriage)
    return marriage


@router.get("/marriages/", response_model=List[schemas.Marriage])
def list_marriages(db: Session = Depends(get_db)):
    marriages = db.query(Marriage).all()
    return marriages


@router.get("/marriages/{marriage_id}", response_model=schemas.Marriage)
def get_marriage(marriage_id: int, db: Session = Depends(get_db)):
    marriage = db.query(Marriage).filter(Marriage.id == marriage_id).first()
    if not marriage:
        raise HTTPException(status_code=404, detail="Marriage not found")
    return marriage


@router.delete("/marriages/{marriage_id}")
def delete_marriage(marriage_id: int, db: Session = Depends(get_db)):
    marriage = db.query(Marriage).filter(Marriage.id == marriage_id).first()
    if not marriage:
        raise HTTPException(status_code=404, detail="Marriage not found")

    db.delete(marriage)
    db.commit()
    return {"message": f"Marriage {marriage_id} deleted successfully"}