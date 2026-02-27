# Placeholder for kinship logic, e.g. mapping English to Shona terms
def get_shona_kinship(relationship: str, gender: str) -> str:
    mapper = {
        "father": "baba",
        "mother": "amai",
        "uncle": "sekuru" if gender == "male" else "tete",
        # Expand mapping...
    }
    return mapper.get(relationship.lower(), relationship)