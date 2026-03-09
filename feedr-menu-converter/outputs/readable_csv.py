"""Generates the human-readable QA CSV."""

import csv
import io
from core.data_models import PipelineResult


def generate(result: PipelineResult) -> bytes:
    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'Name', 'Category', 'Price', 'Type',
        'Description',
        'Contains Allergens', 'Free From',
        'Vegan', 'Vegetarian',
        'VAT Rate', 'VAT Source',
        'Image URL',
        'Kcal', 'Protein (g)', 'Carbs (g)', 'Fat (g)',
        'Assumptions',
    ])

    for item in result.items:
        yes_allergens = [a for a, v in item.allergens.items() if v == 'YES']
        no_allergens  = [a for a, v in item.allergens.items() if v == 'NO']
        assumptions   = ' | '.join(str(a) for a in item.assumptions)

        writer.writerow([
            item.name,
            item.category,
            item.price,
            'Option' if item.is_option else 'Menu Item',
            item.description[:200] if item.description else '',
            ', '.join(yes_allergens) or 'none declared',
            ', '.join(no_allergens[:5]) + ('...' if len(no_allergens) > 5 else ''),
            'YES' if item.dietary.get('vegan') else '',
            'YES' if item.dietary.get('vegetarian') else '',
            f"{item.vat_rate}%" if item.vat_rate else '',
            item.vat_source,
            item.image_url,
            item.nutrition.get('kcal', ''),
            item.nutrition.get('protein', ''),
            item.nutrition.get('carbs', ''),
            item.nutrition.get('fat', ''),
            assumptions,
        ])

    return output.getvalue().encode('utf-8')
