"""Shared constants re-exported for convenience."""
from data.allergen_map import ALLERGEN_MAP, ALLERGENS_14
from data.allergen_rules import ALLERGEN_CODE_MAP

FEEDR_TEMPLATE_HEADERS = [
    'ID', 'Name*', 'Image URL', 'isMenuItem*', 'isOption*',
    'isCCActive', 'isGMActive', 'inReviewForPublishing',
    'Long Description*', 'Short Description*', 'OriginalPrice*', 'vatRate',
    'isHOT*', 'Meal Type*', 'Ingredients*', 'Cuisines Tag*',
    'is combo item', 'Meal Time*',
    'CC: daily stock', 'GM: position', 'GM: min quantity',
    'GM: packaging type', 'GM: price per head', 'GM: category ids', 'GM: servings',
    'Allergen*: Contains Gluten', 'Allergen*: Eggs', 'Allergen*: Fish',
    'Allergen*: Peanuts', 'Allergen*: Soybeans', 'Allergen*: Milk',
    'Allergen*: Nuts', 'Allergen*: Celery', 'Allergen*: Mustard',
    'Allergen*: Sesame', 'Allergen*: Sulphites', 'Allergen*: Lupin',
    'Allergen*: Molluscs', 'Allergen*: Crustaceans',
    'Dietary: Vegan', 'Dietary: Vegetarian', 'Dietary: Halal',
    'Dietary: Kosher', 'Dietary: No refined sugar', 'Dietary: Non HFSS',
    'Nutri Info: Kj', 'Nutri Info: Kcal', 'Nutri Info: Fat (g)',
    'Nutri Info: Saturates (g)', 'Nutri Info: Polyunsaturates (g)',
    'Nutri Info: Monounsaturates (g)', 'Nutri Info: Carbs (g)',
    'Nutri Info: Sugars (g)', 'Nutri Info: Fibre (g)',
    'Nutri Info: Protein (g)', 'Nutri Info: Salt (g)',
    'Sub Allergen cereals: Barley', 'Sub Allergen cereals: Kamut',
    'Sub Allergen cereals: Oats', 'Sub Allergen cereals: Rye',
    'Sub Allergen cereals: Wheat',
    'Sub Allergen nuts: Almonds', 'Sub Allergen nuts: Brazil',
    'Sub Allergen nuts: Cashew', 'Sub Allergen nuts: Hazelnuts',
    'Sub Allergen nuts: Macadamia', 'Sub Allergen nuts: Pecan',
    'Sub Allergen nuts: Pistachio', 'Sub Allergen nuts: Walnuts',
    'Vendor Catalogue ID', 'Vendor Catalogue Selection ID',
    'Vendor Item ID', 'Vendor Variant ID',
]
