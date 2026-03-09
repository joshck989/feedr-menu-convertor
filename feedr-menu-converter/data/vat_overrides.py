"""
Manual VAT overrides for items where name-matching fails.
Keys: lowercased item name (with brackets), Values: '0' or '20'.
"""

MANUAL_VAT = {
    'gochujang tofu greens [new]':                  '0',
    'simply roasted - apple cider vinegar & salt [27g]': '20',
    'simply roasted - creamy jalapeño [27g]':       '20',
    'simply roasted - maple bacon [27g]':           '20',
    'coca cola - diet coke [330ml]':                '20',
    'coca cola - regular coke [330ml]':             '20',
}

# UK VAT categories for food (simplified heuristics)
HOT_FOOD_KEYWORDS = ['hot', 'soup', 'warm', 'grilled', 'fried', 'roasted', 'baked']
STANDARD_RATE_CATEGORIES = ['drinks', 'cold drinks', 'snacks', 'ancilliary']
ZERO_RATE_CATEGORIES = ['bowls', 'plates', 'salads', 'baked goods']
