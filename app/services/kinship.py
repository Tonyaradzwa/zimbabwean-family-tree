from collections import deque
from typing import Dict, Optional, Set

from sqlalchemy.orm import Session

from app.models.family import Individual, Marriage, Relationship


def _build_parent_map(db: Session) -> Dict[int, Set[int]]:
    parent_map: Dict[int, Set[int]] = {}
    rows = db.query(Relationship.parent_id, Relationship.child_id).all()
    for parent_id, child_id in rows:
        parent_map.setdefault(child_id, set()).add(parent_id)
    return parent_map


def _build_child_map(db: Session) -> Dict[int, Set[int]]:
    child_map: Dict[int, Set[int]] = {}
    rows = db.query(Relationship.parent_id, Relationship.child_id).all()
    for parent_id, child_id in rows:
        child_map.setdefault(parent_id, set()).add(child_id)
    return child_map


def _build_spouse_map(db: Session) -> Dict[int, Set[int]]:
    spouse_map: Dict[int, Set[int]] = {}
    rows = db.query(Marriage.partner1_id, Marriage.partner2_id).all()
    for partner1_id, partner2_id in rows:
        spouse_map.setdefault(partner1_id, set()).add(partner2_id)
        spouse_map.setdefault(partner2_id, set()).add(partner1_id)
    return spouse_map


def _build_gender_map(db: Session) -> Dict[int, str]:
    rows = db.query(Individual.id, Individual.gender).all()
    return {individual_id: gender for individual_id, gender in rows}


def _is_older_than(person: Optional[Individual], other: Optional[Individual]) -> Optional[bool]:
    if not person or not other:
        return None
    if not person.birth_date or not other.birth_date:
        return None
    if person.birth_date == other.birth_date:
        return None
    return person.birth_date < other.birth_date


def _distance_via_edges(graph: Dict[int, Set[int]], start_id: int, target_id: int) -> Optional[int]:
    if start_id == target_id:
        return 0

    visited = {start_id}
    queue = deque([(start_id, 0)])

    while queue:
        current, depth = queue.popleft()
        for next_node in graph.get(current, set()):
            if next_node == target_id:
                return depth + 1
            if next_node not in visited:
                visited.add(next_node)
                queue.append((next_node, depth + 1))

    return None


def _ancestor_distance(parent_map: Dict[int, Set[int]], person_id: int, maybe_ancestor_id: int) -> Optional[int]:
    return _distance_via_edges(parent_map, person_id, maybe_ancestor_id)


def _descendant_distance(child_map: Dict[int, Set[int]], person_id: int, maybe_descendant_id: int) -> Optional[int]:
    return _distance_via_edges(child_map, person_id, maybe_descendant_id)


def _make_ancestor_label(distance: int, gender: Optional[str]) -> str:
    if distance == 1:
        return "father" if gender == "male" else "mother" if gender == "female" else "parent"
    if distance == 2:
        return "grandfather" if gender == "male" else "grandmother" if gender == "female" else "grandparent"
    return "ancestor"


def _make_descendant_label(distance: int, gender: Optional[str]) -> str:
    if distance == 1:
        return "son" if gender == "male" else "daughter" if gender == "female" else "child"
    if distance == 2:
        return "grandson" if gender == "male" else "granddaughter" if gender == "female" else "grandchild"
    return "descendant"


def infer_relationship(db: Session, person_id: int, relative_id: int) -> str:
    parent_map = _build_parent_map(db)
    child_map = _build_child_map(db)
    spouse_map = _build_spouse_map(db)
    gender_map = _build_gender_map(db)

    if person_id == relative_id:
        return "self"

    if relative_id in spouse_map.get(person_id, set()):
        relative_gender = gender_map.get(relative_id)
        if relative_gender == "male":
            return "husband"
        if relative_gender == "female":
            return "wife"
        return "spouse"

    ancestor_distance = _ancestor_distance(parent_map, person_id, relative_id)
    if ancestor_distance:
        return _make_ancestor_label(ancestor_distance, gender_map.get(relative_id))

    descendant_distance = _descendant_distance(child_map, person_id, relative_id)
    if descendant_distance:
        return _make_descendant_label(descendant_distance, gender_map.get(relative_id))

    person_parents = parent_map.get(person_id, set())
    relative_parents = parent_map.get(relative_id, set())
    if person_parents and relative_parents and person_parents.intersection(relative_parents):
        relative_gender = gender_map.get(relative_id)
        if relative_gender == "male":
            return "brother"
        if relative_gender == "female":
            return "sister"
        return "sibling"

    parent_siblings: Set[int] = set()
    for parent_id in person_parents:
        parent_parent_ids = parent_map.get(parent_id, set())
        if not parent_parent_ids:
            continue
        for maybe_sibling_id, maybe_sibling_parents in parent_map.items():
            if maybe_sibling_id == parent_id:
                continue
            if parent_parent_ids.intersection(maybe_sibling_parents):
                parent_siblings.add(maybe_sibling_id)

    if relative_id in parent_siblings:
        relative_gender = gender_map.get(relative_id)
        if relative_gender == "male":
            return "uncle"
        if relative_gender == "female":
            return "aunt"
        return "parent_sibling"

    siblings = set()
    for maybe_sibling_id, maybe_sibling_parents in parent_map.items():
        if maybe_sibling_id == person_id:
            continue
        if person_parents and person_parents.intersection(maybe_sibling_parents):
            siblings.add(maybe_sibling_id)

    sibling_children: Set[int] = set()
    for sibling_id in siblings:
        sibling_children.update(child_map.get(sibling_id, set()))

    if relative_id in sibling_children:
        relative_gender = gender_map.get(relative_id)
        if relative_gender == "male":
            return "nephew"
        if relative_gender == "female":
            return "niece"
        return "sibling_child"

    person_grandparents: Set[int] = set()
    for parent_id in person_parents:
        person_grandparents.update(parent_map.get(parent_id, set()))

    relative_grandparents: Set[int] = set()
    for parent_id in relative_parents:
        relative_grandparents.update(parent_map.get(parent_id, set()))

    if person_grandparents and relative_grandparents and person_grandparents.intersection(relative_grandparents):
        return "cousin"

    # In-law inference paths.
    spouses = spouse_map.get(person_id, set())
    if spouses:
        # Parent-in-law: spouse's parents.
        spouses_parents: Set[int] = set()
        for spouse_id in spouses:
            spouses_parents.update(parent_map.get(spouse_id, set()))
        if relative_id in spouses_parents:
            relative_gender = gender_map.get(relative_id)
            if relative_gender == "male":
                return "father_in_law"
            if relative_gender == "female":
                return "mother_in_law"
            return "parent_in_law"

        # Sibling-in-law path 1: spouse's siblings.
        spouses_siblings: Set[int] = set()
        for spouse_id in spouses:
            spouse_parents = parent_map.get(spouse_id, set())
            if not spouse_parents:
                continue
            for maybe_sibling_id, maybe_sibling_parents in parent_map.items():
                if maybe_sibling_id == spouse_id:
                    continue
                if spouse_parents.intersection(maybe_sibling_parents):
                    spouses_siblings.add(maybe_sibling_id)
        if relative_id in spouses_siblings:
            relative_gender = gender_map.get(relative_id)
            if relative_gender == "male":
                return "brother_in_law"
            if relative_gender == "female":
                return "sister_in_law"
            return "sibling_in_law"

    # Build siblings from the person's own parent set for remaining in-law checks.
    siblings = set()
    for maybe_sibling_id, maybe_sibling_parents in parent_map.items():
        if maybe_sibling_id == person_id:
            continue
        if person_parents and person_parents.intersection(maybe_sibling_parents):
            siblings.add(maybe_sibling_id)

    # Sibling-in-law path 2: sibling's spouse.
    siblings_spouses: Set[int] = set()
    for sibling_id in siblings:
        siblings_spouses.update(spouse_map.get(sibling_id, set()))
    if relative_id in siblings_spouses:
        relative_gender = gender_map.get(relative_id)
        if relative_gender == "male":
            return "brother_in_law"
        if relative_gender == "female":
            return "sister_in_law"
        return "sibling_in_law"

    # Child-in-law: child's spouse.
    children = child_map.get(person_id, set())
    childrens_spouses: Set[int] = set()
    for child_id in children:
        childrens_spouses.update(spouse_map.get(child_id, set()))
    if relative_id in childrens_spouses:
        relative_gender = gender_map.get(relative_id)
        if relative_gender == "male":
            return "son_in_law"
        if relative_gender == "female":
            return "daughter_in_law"
        return "child_in_law"

    return "relative"


def get_shona_kinship(
    relationship: str,
    relative_gender: Optional[str] = None,
    person_gender: Optional[str] = None,
) -> str:
    key = relationship.lower().strip()

    base_map = {
        "self": "ini",
        "father": "baba",
        "mother": "amai",
        "parent": "mubereki",
        "grandfather": "sekuru",
        "grandmother": "ambuya",
        "grandparent": "mudzukuru mukuru",
        "son": "mwanakomana",
        "daughter": "mwanasikana",
        "child": "mwana",
        "grandson": "muzukuru",
        "granddaughter": "muzukuru",
        "grandchild": "muzukuru",
        "brother": "hanzvadzi",
        "sister": "hanzvadzi",
        "sibling": "hanzvadzi",
        "husband": "murume",
        "wife": "mukadzi",
        "spouse": "wawakaroorana naye",
        "uncle": "sekuru",
        "aunt": "tete",
        "nephew": "muzukuru",
        "niece": "muzukuru",
        "cousin": "hama",
        "father_in_law": "tezvara",
        "mother_in_law": "vamwene",
        "parent_in_law": "mubereki wemurume kana mukadzi",
        "brother_in_law": "muramu",
        "sister_in_law": "muramu",
        "sibling_in_law": "muramu",
        "son_in_law": "mukuwasha",
        "daughter_in_law": "muroora",
        "child_in_law": "mwana wemumba",
        "ancestor": "mudzinza wekare",
        "descendant": "wemudzinza",
        "relative": "hama",
    }

    # Nuance: sibling terms are speaker-aware in this project.
    if key in {"brother", "sister"} and person_gender in {"male", "female"}:
        if key == "brother":
            return "mukoma" if person_gender == "male" else "handzvadzi"
        return "handzvadzi" if person_gender == "male" else "mukoma"

    if key in {"uncle", "aunt", "parent_sibling"}:
        if relative_gender == "male":
            return "sekuru"
        if relative_gender == "female":
            return "tete"

    return base_map.get(key, relationship)


def infer_shona_kinship(db: Session, person_id: int, relative_id: int) -> str:
    relationship = infer_relationship(db, person_id, relative_id)
    person = db.query(Individual).filter(Individual.id == person_id).first()
    relative = db.query(Individual).filter(Individual.id == relative_id).first()
    relative_gender = relative.gender if relative else None
    person_gender = person.gender if person else None

    # Nuance: all of a person's mother's brothers are called sekuru.
    if relationship == "uncle":
        parent_map = _build_parent_map(db)
        gender_map = _build_gender_map(db)
        for parent_id in parent_map.get(person_id, set()):
            if gender_map.get(parent_id) == "female":  # this parent is the mother
                mother_parents = parent_map.get(parent_id, set())
                uncle_parents = parent_map.get(relative_id, set())
                if mother_parents and mother_parents.intersection(uncle_parents):
                    return "sekuru"

    # Nuance: all of a person's father's sisters are called tete.
    if relationship == "aunt":
        parent_map = _build_parent_map(db)
        gender_map = _build_gender_map(db)
        for parent_id in parent_map.get(person_id, set()):
            if gender_map.get(parent_id) == "male":  # this parent is the father
                father_parents = parent_map.get(parent_id, set())
                aunt_parents = parent_map.get(relative_id, set())
                if father_parents and father_parents.intersection(aunt_parents):
                    return "tete"

    # Nuance: a person's mother's older sisters are maiguru and younger sisters are mainini.
    if relationship == "aunt":
        parent_map = _build_parent_map(db)
        gender_map = _build_gender_map(db)
        for parent_id in parent_map.get(person_id, set()):
            if gender_map.get(parent_id) == "female":  # this parent is the mother
                mother = db.query(Individual).filter(Individual.id == parent_id).first()
                mother_parents = parent_map.get(parent_id, set())
                aunt_parents = parent_map.get(relative_id, set())
                if mother_parents and mother_parents.intersection(aunt_parents):
                    is_older = _is_older_than(relative, mother)
                    if is_older is True:
                        return "maiguru"
                    if is_older is False:
                        return "mainini"

    return get_shona_kinship(relationship, relative_gender, person_gender)