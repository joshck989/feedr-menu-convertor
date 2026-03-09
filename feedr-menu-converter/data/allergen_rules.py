"""
Allergen data extracted from build_atis_upload.py.
ALLERGEN_CODE_MAP: maps platform allergen codes → our 14 internal names
ADDON_ALLERGENS_FUZZY: maps item name (lowercased) → set of allergen names
"""

ALLERGEN_CODE_MAP = {
    'gluten':       'Gluten',
    'eggs':         'Eggs',
    'fish':         'Fish',
    'peanuts':      'Peanuts',
    'soy_beans':    'Soybeans',
    'milk':         'Milk',
    'nuts':         'Nuts',
    'celery':       'Celery',
    'mustard':      'Mustard',
    'sesame':       'Sesame',
    'so2':          'Sulphur Dioxide',
    'lupin':        'Lupin',
    'molluscs':     'Molluscs',
    'crustaceans':  'Crustaceans',
    # aliases
    'soy':          'Soybeans',
    'sulphur_dioxide': 'Sulphur Dioxide',
    'sulphites':    'Sulphur Dioxide',
    'tree_nuts':    'Nuts',
    'shellfish':    'Crustaceans',
}

# Known allergen profiles for addon/option items by normalised name
# Keys are lowercased item names; values are sets of allergen names that are YES
ADDON_ALLERGENS_FUZZY = {
    # ── Proteins ─────────────────────────────────────────────────────────────
    'blackened chicken':                {'Gluten', 'Celery', 'Mustard'},
    'herb grilled chicken':             {'Gluten', 'Celery', 'Mustard'},
    'kefir herb chicken':               {'Gluten', 'Milk', 'Celery', 'Mustard'},
    'garlic butter steak':              {'Milk', 'Celery', 'Mustard'},
    'hot honey salmon':                 {'Fish', 'Celery', 'Mustard', 'Sesame'},
    'gochujang tofu':                   {'Gluten', 'Soybeans', 'Sesame'},
    'miso ginger sweet potato wedges':  {'Gluten', 'Soybeans', 'Sesame'},
    'umami mushrooms':                  {'Gluten', 'Soybeans'},
    'buffalo blackened chicken':        {'Gluten', 'Milk', 'Celery', 'Mustard'},
    'avocado':                          set(),
    'avo smash':                        set(),
    'avocado halves':                   set(),
    'avocado smash':                    set(),
    'parmesan':                         {'Milk'},
    'crumbled feta':                    {'Milk'},
    'soft boiled egg':                  {'Eggs'},
    # ── Grains / bases ───────────────────────────────────────────────────────
    'wholegrain rice':                  set(),
    'wholegrain brown rice':            set(),
    'chopped romaine':                  set(),
    'kale + cabbage':                   set(),
    'kale and cabbage':                 set(),
    'baby spinach':                     set(),
    'lentils':                          {'Celery'},
    # ── Vegetables ───────────────────────────────────────────────────────────
    'cherry tomatoes':                  set(),
    'black bean mix':                   set(),
    'shredded carrots':                 set(),
    'bold bean tahini chickpeas':       {'Sesame'},
    'roasted broccoli':                 set(),
    'cucumber':                         set(),
    'charred corn':                     set(),
    'edamame + pea medley':             {'Soybeans'},
    'edamame and pea medley':           {'Soybeans'},
    'pink & white slaw':                {'Mustard'},
    'pink and white slaw':              {'Mustard'},
    'pickled red onion':                {'Sulphur Dioxide'},
    'spring onion and coriander':       set(),
    'pickled red chilli':               {'Sulphur Dioxide'},
    'zero waste greens':                set(),
    'mint leaves':                      set(),
    'pickled carrots':                  {'Sulphur Dioxide'},
    'roasted new potatoes':             set(),
    'roast new potatoes':               set(),
    'coriander quinoa':                 set(),
    'harissa grains':                   {'Celery'},
    # ── Dressings ────────────────────────────────────────────────────────────
    'green goddess dressing':           {'Milk', 'Eggs', 'Celery', 'Mustard'},
    'balsamic vinaigrette':             {'Sulphur Dioxide'},
    'caesar dressing':                  {'Eggs', 'Fish', 'Milk', 'Mustard'},
    'classic caesar':                   {'Eggs', 'Fish', 'Milk', 'Mustard'},
    'miso ponzu':                       {'Gluten', 'Soybeans'},
    'apple cider vinaigrette':          {'Sulphur Dioxide'},
    'cashew satay':                     {'Nuts', 'Soybeans', 'Sesame'},
    'lime coriander':                   set(),
    'tahini':                           {'Sesame'},
    'creamy jalapeño dressing':         {'Eggs', 'Milk', 'Mustard'},
    'chipotle lime dressing':           {'Eggs', 'Milk', 'Mustard'},
    'olive oil + balsamic vinegar':     {'Sulphur Dioxide'},
    'olive oil and balsamic vinegar':   {'Sulphur Dioxide'},
    'lime wedge':                       set(),
    "i don't want a dressing":          set(),
    'i do not want a dressing':         set(),
    # ── Sauces / extras ──────────────────────────────────────────────────────
    'buffalo sauce':                    {'Gluten', 'Milk'},
    'herb yoghurt':                     {'Milk'},
    'garlic aioli':                     {'Eggs', 'Mustard'},
    'chimichurri':                      set(),
    'mushroom xo sauce':                {'Gluten', 'Soybeans', 'Crustaceans', 'Molluscs'},
    # ── Crunches / toppings ───────────────────────────────────────────────────
    'crispy shallots':                  {'Gluten'},
    'smoked almonds':                   {'Nuts'},
    'breadcrumbs':                      {'Gluten'},
    'poilâne breadcrumbs':              {'Gluten'},
    'omega seeds':                      {'Sesame'},
    'tortillas':                        {'Gluten'},
    'blanco niño chipotle tortillas':   {'Gluten'},
    'chilli lime cashews':              {'Nuts'},
    'wakame crunch':                    {'Sesame'},
    # ── Bread ────────────────────────────────────────────────────────────────
    'focaccia':                         {'Gluten', 'Milk', 'Eggs', 'Sesame'},
    'the dusty knuckle focaccia':       {'Gluten', 'Milk', 'Eggs', 'Sesame'},
    'no, i do not want bread':          set(),
    # ── Pip & Nut ────────────────────────────────────────────────────────────
    'pip & nut':                        {'Peanuts', 'Nuts'},
    'pip and nut':                      {'Peanuts', 'Nuts'},
}

# Items where allergen inference is uncertain — flag for manual review
ADDON_FUZZY_FLAGS = {
    'herb grilled chicken':   'Allergen profile assumed; verify with restaurant',
    'mushroom xo sauce':      'XO sauce typically contains shellfish — confirm with restaurant',
    'crispy shallots':        'Gluten assumed; check frying batter',
}
