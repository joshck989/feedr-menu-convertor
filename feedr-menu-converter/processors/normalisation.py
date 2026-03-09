"""
Shared text normalisation utilities.
Extracted from add_vat.py and add_nutrition.py.
"""

import re


def normalise(name: str) -> str:
    """
    Aggressively normalise a menu item name for fuzzy matching:
    - lowercase
    - strip [bracketed tags] like [NEW], [HOT], [LARGE], [50ml]
    - convert ' - ' separator to space
    - unify + and & → 'and'
    - collapse whitespace
    """
    name = name.lower().strip()
    name = re.sub(r'\[.*?\]', '', name)               # strip [anything]
    name = re.sub(r'\s+-\s+', ' ', name)              # " - " → space
    name = re.sub(r'\s*&\s*|\s*\+\s*', ' and ', name) # & / + → and
    name = re.sub(r'\s+', ' ', name).strip()
    return name


STOP_WORDS = {
    'a', 'an', 'the', 'and', 'or', 'of', 'in', 'with', 'for',
    'to', 'no', 'not', 'i', 'do', 'want',
}


def sig_words(norm: str) -> set:
    """Words longer than 2 chars that aren't stop-words."""
    return {w for w in norm.split() if len(w) > 2 and w not in STOP_WORDS}
