"""
Generates the 73-column Feedr upload CSV + Assumptions column.
Includes a summary header block in the first rows.
"""

import csv
import io
from core.data_models import PipelineResult
from core.constants import FEEDR_TEMPLATE_HEADERS
from data.allergen_map import ALLERGEN_MAP


def generate(result: PipelineResult) -> bytes:
    output = io.StringIO()
    all_headers = FEEDR_TEMPLATE_HEADERS + ['Assumptions']
    writer = csv.DictWriter(output, fieldnames=all_headers, extrasaction='ignore')
    writer.writeheader()

    # ── Summary header rows ──────────────────────────────────────────────────
    s = result.summary
    summary_lines = [
        f"=== FEEDR MENU CONVERTER — PROCESSING SUMMARY ===",
        f"Restaurant: {result.restaurant_name} | Platform: {result.platform} | Generated: {result.timestamp}",
        f"Total items: {s['total']} ({s['main_items']} menu items, {s['options']} options) | "
        f"Critical issues: {s['criticals']} | Warnings: {s['warnings']}",
        f"Allergen sources: {s['allergen_sources']} | VAT sources: {s['vat_sources']}",
    ]
    if result.global_assumptions:
        summary_lines.append("Global flags: " + " | ".join(str(a) for a in result.global_assumptions))

    for line in summary_lines:
        row = {h: '' for h in all_headers}
        row['ID'] = line
        writer.writerow(row)

    # ── Data rows ─────────────────────────────────────────────────────────────
    for item in result.items:
        row = {h: '' for h in all_headers}

        row['Name*']            = item.name
        row['Image URL']        = item.image_url
        row['isMenuItem*']      = 'YES'
        row['isOption*']        = 'YES' if item.is_option else 'NO'
        row['Long Description*']= item.description
        row['Ingredients*']     = item.description
        row['OriginalPrice*']   = item.price
        row['vatRate']          = item.vat_rate

        # Allergens
        for internal_name, feedr_col in ALLERGEN_MAP.items():
            row[feedr_col] = item.allergens.get(internal_name, 'NO')

        # Dietary
        row['Dietary: Vegan']       = 'YES' if item.dietary.get('vegan') else 'NO'
        row['Dietary: Vegetarian']  = 'YES' if item.dietary.get('vegetarian') else 'NO'

        # Nutrition (main items only)
        if item.nutrition:
            row['Nutri Info: Kcal']       = item.nutrition.get('kcal', '')
            row['Nutri Info: Protein (g)']= item.nutrition.get('protein', '')
            row['Nutri Info: Carbs (g)']  = item.nutrition.get('carbs', '')
            row['Nutri Info: Fat (g)']    = item.nutrition.get('fat', '')

        # Assumptions
        row['Assumptions'] = ' | '.join(str(a) for a in item.assumptions)

        writer.writerow(row)

    return output.getvalue().encode('utf-8')
