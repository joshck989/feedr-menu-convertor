"""
ALLERGEN_MAP: our 14 internal allergen names → Feedr template column names.
Extracted from map_to_template.py.
"""

ALLERGEN_MAP = {
    'Gluten':         'Allergen*: Contains Gluten',
    'Eggs':           'Allergen*: Eggs',
    'Fish':           'Allergen*: Fish',
    'Peanuts':        'Allergen*: Peanuts',
    'Soybeans':       'Allergen*: Soybeans',
    'Milk':           'Allergen*: Milk',
    'Nuts':           'Allergen*: Nuts',
    'Celery':         'Allergen*: Celery',
    'Mustard':        'Allergen*: Mustard',
    'Sesame':         'Allergen*: Sesame',
    'Sulphur Dioxide':'Allergen*: Sulphites',
    'Lupin':          'Allergen*: Lupin',
    'Molluscs':       'Allergen*: Molluscs',
    'Crustaceans':    'Allergen*: Crustaceans',
}

ALLERGENS_14 = list(ALLERGEN_MAP.keys())
