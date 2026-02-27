from sqlalchemy import Column, Integer, String, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Individual(Base):
    __tablename__ = "individuals"
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    gender = Column(Enum('male', 'female', name='gender'), nullable=False)
    birth_date = Column(String, nullable=True)

    parents = relationship("Relationship", back_populates="child", foreign_keys="[Relationship.child_id]")
    children = relationship("Relationship", back_populates="parent", foreign_keys="[Relationship.parent_id]")
    spouses = relationship(
        "Marriage",
        primaryjoin="or_(Individual.id==Marriage.partner1_id, Individual.id==Marriage.partner2_id)",
        back_populates="partners"
    )

class Relationship(Base):
    __tablename__ = "relationships"
    id = Column(Integer, primary_key=True)
    parent_id = Column(Integer, ForeignKey('individuals.id'))
    child_id = Column(Integer, ForeignKey('individuals.id'))
    type = Column(Enum('biological', 'adoptive', name='relationship_type'))

    parent = relationship("Individual", foreign_keys=[parent_id], back_populates="children")
    child = relationship("Individual", foreign_keys=[child_id], back_populates="parents")

    __table_args__ = (UniqueConstraint('parent_id', 'child_id', name='uq_parent_child'),)

class Marriage(Base):
    __tablename__ = "marriages"
    id = Column(Integer, primary_key=True)
    partner1_id = Column(Integer, ForeignKey('individuals.id'))
    partner2_id = Column(Integer, ForeignKey('individuals.id'))
    date = Column(String, nullable=True)

    partners = relationship("Individual", primaryjoin="or_(Marriage.partner1_id==Individual.id, Marriage.partner2_id==Individual.id)")