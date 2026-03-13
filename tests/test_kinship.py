import os
import sys

import pytest

# make sure the repository root is on PYTHONPATH so we can import `app`
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.db import SessionLocal, engine
from app.models.family import Base, Individual, Marriage, Relationship
from app.services.kinship import infer_relationship, infer_shona_kinship


@pytest.fixture(autouse=True)
def setup_db():
    engine.dispose()
    if os.path.exists("test.db"):
        os.remove("test.db")
    Base.metadata.create_all(bind=engine)
    yield
    engine.dispose()
    if os.path.exists("test.db"):
        os.remove("test.db")


def _seed_family_tree(db):
    people = [
        Individual(name="Sekuru", gender="male", birth_date="1940-01-01"),
        Individual(name="Ambuya", gender="female", birth_date="1945-01-01"),
        Individual(name="Baba", gender="male", birth_date="1970-01-01"),
        Individual(name="Tete", gender="female", birth_date="1972-01-01"),
        Individual(name="Amai", gender="female", birth_date="1973-01-01"),
        Individual(name="Tawanda", gender="male", birth_date="2000-01-01"),
        Individual(name="Rudo", gender="female", birth_date="2003-01-01"),
        Individual(name="Kundai", gender="male", birth_date="2004-01-01"),
    ]
    db.add_all(people)
    db.commit()

    relationships = [
        Relationship(parent_id=1, child_id=3, type="biological"),
        Relationship(parent_id=2, child_id=3, type="biological"),
        Relationship(parent_id=1, child_id=4, type="biological"),
        Relationship(parent_id=2, child_id=4, type="biological"),
        Relationship(parent_id=3, child_id=6, type="biological"),
        Relationship(parent_id=5, child_id=6, type="biological"),
        Relationship(parent_id=3, child_id=7, type="biological"),
        Relationship(parent_id=5, child_id=7, type="biological"),
        Relationship(parent_id=4, child_id=8, type="biological"),
    ]
    db.add_all(relationships)

    marriages = [
        Marriage(partner1_id=3, partner2_id=5, date="1995-06-15"),
    ]
    db.add_all(marriages)
    db.commit()


def test_infer_relationships_core_cases():
    db = SessionLocal()
    try:
        _seed_family_tree(db)

        # Person 6 (Tawanda) perspective
        assert infer_relationship(db, 6, 3) == "father"
        assert infer_relationship(db, 6, 5) == "mother"
        assert infer_relationship(db, 6, 2) == "grandmother"
        assert infer_relationship(db, 6, 7) == "sister"
        assert infer_relationship(db, 6, 4) == "aunt"
        assert infer_relationship(db, 6, 8) == "cousin"
        assert infer_relationship(db, 6, 6) == "self"

        # Person 3 (Baba) perspective
        assert infer_relationship(db, 3, 5) == "wife"
        assert infer_relationship(db, 3, 6) == "son"
        assert infer_relationship(db, 3, 7) == "daughter"
    finally:
        db.close()


def test_infer_shona_kinship():
    db = SessionLocal()
    try:
        _seed_family_tree(db)

        assert infer_shona_kinship(db, 6, 3) == "baba"
        assert infer_shona_kinship(db, 6, 5) == "amai"
        assert infer_shona_kinship(db, 6, 4) == "tete"
        assert infer_shona_kinship(db, 6, 2) == "ambuya"
    finally:
        db.close()


def test_maternal_uncle_is_sekuru():
    """Nuance 1: all of a person's mother's brothers are called sekuru."""
    db = SessionLocal()
    try:
        # Maternal grandparents
        mgf = Individual(name="MaternalGF", gender="male", birth_date="1930-01-01")
        mgm = Individual(name="MaternalGM", gender="female", birth_date="1935-01-01")
        # Amai and her brother (the maternal uncle)
        amai = Individual(name="Amai", gender="female", birth_date="1973-01-01")
        va_sekuru = Individual(name="VaSekuru", gender="male", birth_date="1970-01-01")
        # Father (paternal side has no shared grandparents with va_sekuru)
        baba = Individual(name="Baba", gender="male", birth_date="1970-01-01")
        # Child
        mwana = Individual(name="Mwana", gender="male", birth_date="2000-01-01")

        db.add_all([mgf, mgm, amai, va_sekuru, baba, mwana])
        db.commit()

        # Amai and VaSekuru share the same parents (maternal grandparents)
        db.add_all([
            Relationship(parent_id=mgf.id, child_id=amai.id, type="biological"),
            Relationship(parent_id=mgm.id, child_id=amai.id, type="biological"),
            Relationship(parent_id=mgf.id, child_id=va_sekuru.id, type="biological"),
            Relationship(parent_id=mgm.id, child_id=va_sekuru.id, type="biological"),
            # Mwana's parents
            Relationship(parent_id=amai.id, child_id=mwana.id, type="biological"),
            Relationship(parent_id=baba.id, child_id=mwana.id, type="biological"),
        ])
        db.commit()

        assert infer_relationship(db, mwana.id, va_sekuru.id) == "uncle"
        assert infer_shona_kinship(db, mwana.id, va_sekuru.id) == "sekuru"
    finally:
        db.close()


def test_paternal_aunt_is_tete():
    """Nuance 2: all of a person's father's sisters are called tete."""
    db = SessionLocal()
    try:
        # Paternal grandparents
        pgf = Individual(name="PaternalGF", gender="male", birth_date="1930-01-01")
        pgm = Individual(name="PaternalGM", gender="female", birth_date="1935-01-01")
        # Baba and his sister (the paternal aunt)
        baba = Individual(name="Baba", gender="male", birth_date="1970-01-01")
        tete = Individual(name="Tete", gender="female", birth_date="1972-01-01")
        # Mother lives on a separate branch
        amai = Individual(name="Amai", gender="female", birth_date="1973-01-01")
        # Child
        mwana = Individual(name="Mwana", gender="male", birth_date="2000-01-01")

        db.add_all([pgf, pgm, baba, tete, amai, mwana])
        db.commit()

        # Baba and Tete share the same parents (paternal grandparents)
        db.add_all([
            Relationship(parent_id=pgf.id, child_id=baba.id, type="biological"),
            Relationship(parent_id=pgm.id, child_id=baba.id, type="biological"),
            Relationship(parent_id=pgf.id, child_id=tete.id, type="biological"),
            Relationship(parent_id=pgm.id, child_id=tete.id, type="biological"),
            # Mwana's parents
            Relationship(parent_id=baba.id, child_id=mwana.id, type="biological"),
            Relationship(parent_id=amai.id, child_id=mwana.id, type="biological"),
        ])
        db.commit()

        assert infer_relationship(db, mwana.id, tete.id) == "aunt"
        assert infer_shona_kinship(db, mwana.id, tete.id) == "tete"
    finally:
        db.close()


def test_mothers_older_sister_is_maiguru():
    """Nuance 3a: all of a person's mother's older sisters are called maiguru."""
    db = SessionLocal()
    try:
        mgf = Individual(name="MaternalGF", gender="male", birth_date="1930-01-01")
        mgm = Individual(name="MaternalGM", gender="female", birth_date="1935-01-01")
        maiguru = Individual(name="Maiguru", gender="female", birth_date="1970-01-01")
        amai = Individual(name="Amai", gender="female", birth_date="1973-01-01")
        baba = Individual(name="Baba", gender="male", birth_date="1970-01-01")
        mwana = Individual(name="Mwana", gender="male", birth_date="2000-01-01")

        db.add_all([mgf, mgm, maiguru, amai, baba, mwana])
        db.commit()

        db.add_all([
            Relationship(parent_id=mgf.id, child_id=maiguru.id, type="biological"),
            Relationship(parent_id=mgm.id, child_id=maiguru.id, type="biological"),
            Relationship(parent_id=mgf.id, child_id=amai.id, type="biological"),
            Relationship(parent_id=mgm.id, child_id=amai.id, type="biological"),
            Relationship(parent_id=amai.id, child_id=mwana.id, type="biological"),
            Relationship(parent_id=baba.id, child_id=mwana.id, type="biological"),
        ])
        db.commit()

        assert infer_relationship(db, mwana.id, maiguru.id) == "aunt"
        assert infer_shona_kinship(db, mwana.id, maiguru.id) == "maiguru"
    finally:
        db.close()


def test_mothers_younger_sister_is_mainini():
    """Nuance 3b: all of a person's mother's younger sisters are called mainini."""
    db = SessionLocal()
    try:
        mgf = Individual(name="MaternalGF", gender="male", birth_date="1930-01-01")
        mgm = Individual(name="MaternalGM", gender="female", birth_date="1935-01-01")
        amai = Individual(name="Amai", gender="female", birth_date="1973-01-01")
        mainini = Individual(name="Mainini", gender="female", birth_date="1976-01-01")
        baba = Individual(name="Baba", gender="male", birth_date="1970-01-01")
        mwana = Individual(name="Mwana", gender="male", birth_date="2000-01-01")

        db.add_all([mgf, mgm, amai, mainini, baba, mwana])
        db.commit()

        db.add_all([
            Relationship(parent_id=mgf.id, child_id=amai.id, type="biological"),
            Relationship(parent_id=mgm.id, child_id=amai.id, type="biological"),
            Relationship(parent_id=mgf.id, child_id=mainini.id, type="biological"),
            Relationship(parent_id=mgm.id, child_id=mainini.id, type="biological"),
            Relationship(parent_id=amai.id, child_id=mwana.id, type="biological"),
            Relationship(parent_id=baba.id, child_id=mwana.id, type="biological"),
        ])
        db.commit()

        assert infer_relationship(db, mwana.id, mainini.id) == "aunt"
        assert infer_shona_kinship(db, mwana.id, mainini.id) == "mainini"
    finally:
        db.close()


def test_female_speaker_sibling_terms():
    """Nuance 4a: female speaker calls brother handzvadzi and sister mukoma."""
    db = SessionLocal()
    try:
        parent1 = Individual(name="Parent1", gender="male", birth_date="1970-01-01")
        parent2 = Individual(name="Parent2", gender="female", birth_date="1972-01-01")
        sister = Individual(name="Sister", gender="female", birth_date="2000-01-01")
        speaker = Individual(name="FemaleSpeaker", gender="female", birth_date="2002-01-01")
        brother = Individual(name="Brother", gender="male", birth_date="2004-01-01")

        db.add_all([parent1, parent2, sister, speaker, brother])
        db.commit()

        db.add_all([
            Relationship(parent_id=parent1.id, child_id=sister.id, type="biological"),
            Relationship(parent_id=parent2.id, child_id=sister.id, type="biological"),
            Relationship(parent_id=parent1.id, child_id=speaker.id, type="biological"),
            Relationship(parent_id=parent2.id, child_id=speaker.id, type="biological"),
            Relationship(parent_id=parent1.id, child_id=brother.id, type="biological"),
            Relationship(parent_id=parent2.id, child_id=brother.id, type="biological"),
        ])
        db.commit()

        assert infer_relationship(db, speaker.id, brother.id) == "brother"
        assert infer_relationship(db, speaker.id, sister.id) == "sister"
        assert infer_shona_kinship(db, speaker.id, brother.id) == "handzvadzi"
        assert infer_shona_kinship(db, speaker.id, sister.id) == "mukoma"
    finally:
        db.close()


def test_male_speaker_sibling_terms():
    """Nuance 4b: male speaker calls sister handzvadzi and brother mukoma."""
    db = SessionLocal()
    try:
        parent1 = Individual(name="Parent1", gender="male", birth_date="1970-01-01")
        parent2 = Individual(name="Parent2", gender="female", birth_date="1972-01-01")
        sister = Individual(name="Sister", gender="female", birth_date="2000-01-01")
        speaker = Individual(name="MaleSpeaker", gender="male", birth_date="2002-01-01")
        brother = Individual(name="Brother", gender="male", birth_date="2004-01-01")

        db.add_all([parent1, parent2, sister, speaker, brother])
        db.commit()

        db.add_all([
            Relationship(parent_id=parent1.id, child_id=sister.id, type="biological"),
            Relationship(parent_id=parent2.id, child_id=sister.id, type="biological"),
            Relationship(parent_id=parent1.id, child_id=speaker.id, type="biological"),
            Relationship(parent_id=parent2.id, child_id=speaker.id, type="biological"),
            Relationship(parent_id=parent1.id, child_id=brother.id, type="biological"),
            Relationship(parent_id=parent2.id, child_id=brother.id, type="biological"),
        ])
        db.commit()

        assert infer_relationship(db, speaker.id, sister.id) == "sister"
        assert infer_relationship(db, speaker.id, brother.id) == "brother"
        assert infer_shona_kinship(db, speaker.id, sister.id) == "handzvadzi"
        assert infer_shona_kinship(db, speaker.id, brother.id) == "mukoma"
    finally:
        db.close()
