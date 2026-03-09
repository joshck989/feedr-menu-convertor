"""
Ordit platform adapter.
Handles CSV exports from Ordit-powered ordering sites.
Expected columns: Meal Name, Meal Description, Price, Image URL (col AM/index 38),
allergens as pipe-separated codes in an allergens column.
"""

import csv
import io
from typing import List, Optional

from adapters.base import BaseAdapter
from core.data_models import MenuItem
from data.allergen_rules import ALLERGEN_CODE_MAP
from data.allergen_map import ALLERGENS_14
from processors.normalisation import normalise


def _parse_pipe_allergens(raw: str) -> set:
    """Parse 'so2|gluten|milk' → {'Sulphur Dioxide', 'Gluten', 'Milk'}"""
    if not raw or not raw.strip():
        return set()
    codes = [c.strip().lower() for c in raw.split('|') if c.strip()]
    allergens = set()
    for code in codes:
        if code in ALLERGEN_CODE_MAP:
            allergens.add(ALLERGEN_CODE_MAP[code])
    return allergens


class OrditAdapter(BaseAdapter):
    """
    Handles Ordit CSV export files.
    Accepts either a file path or raw CSV text.
    """

    def __init__(self):
        super().__init__()
        self._rows: List[dict] = []

    def fetch(self, source: str) -> None:
        """source: path to a CSV file or raw CSV string."""
        try:
            with open(source, newline='', encoding='utf-8-sig') as f:
                content = f.read()
        except (OSError, FileNotFoundError):
            content = source  # treat as raw CSV string

        reader = csv.DictReader(io.StringIO(content))
        self._rows = list(reader)
        if self._rows:
            # Try to infer restaurant name from first row
            for col in ('Restaurant Name', 'restaurant_name', 'Venue'):
                if col in self._rows[0]:
                    self.restaurant_name = self._rows[0][col]
                    break

    def fetch_bytes(self, content: bytes) -> None:
        """Accept uploaded file bytes from Streamlit."""
        text = content.decode('utf-8-sig')
        reader = csv.DictReader(io.StringIO(text))
        self._rows = list(reader)

    def _find_col(self, row: dict, candidates: list) -> str:
        """Return first matching column value, or empty string."""
        for c in candidates:
            if c in row and row[c].strip():
                return row[c].strip()
        return ''

    def parse(self) -> List[MenuItem]:
        items = []
        seen = set()  # dedup by name+price

        for row in self._rows:
            name = self._find_col(row, ['Meal Name', 'name', 'Name', 'item_name', 'Item Name'])
            if not name:
                continue

            price = self._find_col(row, ['Price', 'price', 'OriginalPrice', 'Meal Price'])
            desc  = self._find_col(row, ['Meal Description', 'description', 'Description', 'Long Description'])
            image = self._find_col(row, [
                'Image URL', 'image_url', 'Image',
                # Ordit column AM is index 38 — try header names
                'imageURL', 'Meal Image', 'image',
            ])
            # Fallback: try column index 38 (AM) for image
            if not image:
                cols = list(row.keys())
                if len(cols) > 38:
                    image = row[cols[38]].strip()

            allergens_raw = self._find_col(row, [
                'Allergens', 'allergens', 'Allergen Codes',
                'Meal Suitable For', 'allergen_codes',
            ])
            category = self._find_col(row, ['Category', 'category', 'Meal Type', 'Section'])
            is_option_raw = self._find_col(row, ['isOption', 'isOption*', 'is_option', 'Option'])
            is_option = is_option_raw.upper() in ('YES', 'TRUE', '1', 'OPTION')

            # Dedup
            key = (normalise(name), price)
            if key in seen:
                continue
            seen.add(key)

            # Parse allergens
            allergen_set = _parse_pipe_allergens(allergens_raw)

            # Dietary from "Meal Suitable For" column
            dietary = {}
            suitable = self._find_col(row, ['Meal Suitable For', 'dietary', 'Dietary'])
            if suitable:
                s_lower = suitable.lower()
                dietary['vegan']      = 'vegan' in s_lower
                dietary['vegetarian'] = 'vegetarian' in s_lower or 'vegan' in s_lower

            item = MenuItem(
                name=name,
                category=category,
                description=desc,
                price=price,
                image_url=image,
                is_option=is_option,
                dietary=dietary,
            )

            if allergen_set or allergens_raw:
                from processors.allergen_processor import _allergens_from_set
                item.allergens = _allergens_from_set(allergen_set)
                item.allergen_source = 'source'
                item.add_assumption('allergen', 'Allergens from source data', 'info')

            items.append(item)

        return items
