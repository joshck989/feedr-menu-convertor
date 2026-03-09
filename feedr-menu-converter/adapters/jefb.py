"""
Just Eat For Business (JEFB) adapter.

Handles two input formats:
  1. UI URL:  https://app.business.just-eat.co.uk/menus/vendors/{vendor}/{location}
  2. API URL: https://app.business.just-eat.co.uk/api/public/deliverable-menus/{vendor}/{datetime}?locationSlug={location}

The adapter detects which format was given and constructs the API URL if needed.

Response structure (verified from live Farmer J response):
  item.vendor.name                       → restaurant name
  item.content.sections[].title          → category name
  item.content.sections[].items[]        → menu items

  Per item:
    .name / .description / .price        → core fields (price is float GBP)
    .images[0].medium                    → image URL (citypantry CDN)
    .vatRateType                         → UK_STANDARD_RATE | UK_ZERO_RATE → 20 | 0
    .allergens.{key}: bool               → 14 allergens as booleans
    .allergens.notProvided               → true if no allergen data
    .dietaries.{vegetarian/vegan/halal}  → dietary booleans
    .ingredients[]                       → list of ingredient strings
    .hot                                 → isHOT flag
    .cuisine                             → cuisine tag
    .portionSize                         → 1 = individual, 6 = group/buffet
    .servingStyle                        → individual | buffet
    .type                                → SingleItem | ItemBundle

  ItemBundle items also have:
    .groups[].heading                    → option group name
    .groups[].items[]                    → sub-items (e.g. Coke / Diet Coke)
"""

import re
import json
import requests
from datetime import datetime, timezone, timedelta
from typing import List

from adapters.base import BaseAdapter
from core.data_models import MenuItem
from data.allergen_map import ALLERGENS_14

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept': 'application/json',
    'Accept-Language': 'en-GB,en;q=0.9',
}

# JEFB allergen key → our internal allergen name
JEFB_ALLERGEN_MAP = {
    'gluten':         'Gluten',
    'crustaceans':    'Crustaceans',
    'eggs':           'Eggs',
    'fish':           'Fish',
    'peanuts':        'Peanuts',
    'soybeans':       'Soybeans',
    'milk':           'Milk',
    'nuts':           'Nuts',
    'celery':         'Celery',
    'mustard':        'Mustard',
    'sesame':         'Sesame',
    'sulphurDioxide': 'Sulphur Dioxide',
    'lupin':          'Lupin',
    'molluscs':       'Molluscs',
}

VAT_RATE_MAP = {
    'UK_STANDARD_RATE': '20',
    'UK_ZERO_RATE':     '0',
    'UK_REDUCED_RATE':  '5',
}

INGREDIENT_PLACEHOLDERS = {
    'n/a', 'not required (non-food item)', 'not required', '', 'na',
}


def _build_api_url(ui_or_api_url: str) -> str:
    """
    Convert a JEFB UI URL or API URL to the canonical API endpoint.

    UI format:  .../menus/vendors/{vendor}/{location}
    API format: .../api/public/deliverable-menus/{vendor}/{datetime}?locationSlug={location}
    """
    url = ui_or_api_url.strip()

    # Already an API URL
    if '/api/public/deliverable-menus/' in url:
        return url

    # Parse vendor and location from UI URL
    match = re.search(r'/menus/vendors/([^/?\s]+)/([^/?\s]+)', url)
    if not match:
        raise ValueError(
            f"Could not parse vendor/location slug from URL:\n  {url}\n\n"
            "Expected: https://app.business.just-eat.co.uk/menus/vendors/{{vendor-slug}}/{{location-slug}}\n"
            "Example:  https://app.business.just-eat.co.uk/menus/vendors/farmer-j/st-james"
        )

    vendor   = match.group(1)
    location = match.group(2)

    # Use tomorrow at 13:00 UTC to avoid same-day notice cutoffs
    dt = (datetime.now(timezone.utc) + timedelta(days=1)).replace(
        hour=13, minute=0, second=0, microsecond=0
    )
    dt_str = dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')

    return (
        f"https://app.business.just-eat.co.uk/api/public/deliverable-menus"
        f"/{vendor}/{dt_str}?locationSlug={location}"
    )


def _parse_allergens(allergen_dict: dict) -> dict:
    """Convert JEFB allergen booleans → our YES/NO dict for all 14 allergens."""
    result = {a: 'NO' for a in ALLERGENS_14}
    if not allergen_dict or allergen_dict.get('notProvided'):
        return result
    for jefb_key, internal_name in JEFB_ALLERGEN_MAP.items():
        if allergen_dict.get(jefb_key):
            result[internal_name] = 'YES'
    return result


def _parse_dietaries(diet_dict: dict) -> dict:
    if not diet_dict:
        return {}
    return {
        'vegan':        bool(diet_dict.get('vegan')),
        'vegetarian':   bool(diet_dict.get('vegetarian')),
        'halal':        bool(diet_dict.get('halal')),
    }


def _format_price(price_val) -> str:
    try:
        return f'£{float(price_val):.2f}'
    except (TypeError, ValueError):
        return str(price_val) if price_val else ''


def _best_image(images: list) -> str:
    if not images:
        return ''
    img = images[0]
    return img.get('medium') or img.get('large') or img.get('thumbnail') or ''


def _clean_ingredients(ingredients: list) -> str:
    """Filter placeholder values and join to a comma-separated string."""
    cleaned = [
        i.strip() for i in ingredients
        if i and i.strip().lower() not in INGREDIENT_PLACEHOLDERS
    ]
    return ', '.join(cleaned)


def _make_item(raw: dict, category: str, is_option: bool = False) -> MenuItem:
    """Build a MenuItem from a JEFB item dict, fully populating assumption trail."""
    allergen_dict = raw.get('allergens', {})
    allergens     = _parse_allergens(allergen_dict)
    not_provided  = not allergen_dict or bool(allergen_dict.get('notProvided'))

    ingredients_str = _clean_ingredients(raw.get('ingredients', []))

    vat_type = raw.get('vatRateType', '')
    vat_rate = VAT_RATE_MAP.get(vat_type, '')

    item = MenuItem(
        name            = raw.get('name', '').strip(),
        category        = category,
        description     = raw.get('description', '').strip(),
        price           = _format_price(raw.get('price')),
        allergens       = allergens,
        allergen_source = 'unknown' if not_provided else 'source',
        vat_rate        = vat_rate,
        vat_source      = 'source' if vat_rate else 'unknown',
        image_url       = _best_image(raw.get('images', [])),
        dietary         = _parse_dietaries(raw.get('dietaries', {})),
        is_option       = is_option,
    )

    # Use ingredients as description fallback if description is empty
    if not item.description and ingredients_str:
        item.description = ingredients_str

    # ── Allergen assumption ───────────────────────────────────────────────────
    if not_provided:
        item.add_assumption(
            'allergen',
            'Allergens marked as "not provided" in JEFB — all set to NO. Manual review required.',
            'critical'
        )
    else:
        yes_allergens = [a for a, v in allergens.items() if v == 'YES']
        item.add_assumption(
            'allergen',
            f'Allergens from JEFB source data. Contains: {", ".join(yes_allergens) if yes_allergens else "none declared"}',
            'info'
        )

    # ── VAT assumption ────────────────────────────────────────────────────────
    if vat_rate:
        item.add_assumption(
            'vat',
            f'VAT {vat_rate}%: direct from JEFB vatRateType ({vat_type})',
            'info',
            'vatRate'
        )
    else:
        item.add_assumption('vat', 'VAT rate not provided by JEFB', 'warning', 'vatRate')

    # ── Image assumption ──────────────────────────────────────────────────────
    if item.image_url and 'citypantry.com' in item.image_url:
        item.add_assumption(
            'image',
            'Image hosted on citypantry.com CDN (owned by Just Eat). '
            'Reasonably stable but consider re-hosting to avoid dependency.',
            'info',
            'Image URL'
        )

    # ── Group/buffet flag ─────────────────────────────────────────────────────
    portion = raw.get('portionSize', 1)
    try:
        portion = int(portion)
    except (TypeError, ValueError):
        portion = 1
    if portion > 1:
        item.add_assumption(
            'data_quality',
            f'Buffet/group item — serves {portion} people. Price £{float(raw.get("price", 0)):.2f} is per {portion}-person portion.',
            'info'
        )

    return item


class JEFBAdapter(BaseAdapter):
    """
    Fetches and parses a JEFB menu from a URL.

    Input: UI URL or API URL for any JEFB vendor.
    The URL pattern is extracted automatically:
      UI:  https://app.business.just-eat.co.uk/menus/vendors/{vendor}/{location}
      API: https://app.business.just-eat.co.uk/api/public/deliverable-menus/{vendor}/{datetime}?locationSlug={location}
    """

    def __init__(self):
        super().__init__()
        self._data: dict = {}

    def fetch(self, source: str) -> None:
        api_url = _build_api_url(source)
        resp = requests.get(api_url, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        self._data = resp.json()

    def fetch_bytes(self, content: bytes, filename: str = '') -> None:
        """Accept an uploaded JSON export (fallback for when URL access fails)."""
        self._data = json.loads(content.decode('utf-8'))

    def fetch_json_string(self, raw_json: str) -> None:
        """Accept a pasted JSON string directly."""
        self._data = json.loads(raw_json)

    def parse(self) -> List[MenuItem]:
        # Root is either the full response or the inner 'item' object
        item_root = self._data.get('item', self._data)

        # Restaurant name from vendor
        vendor = item_root.get('vendor', {})
        self.restaurant_name = vendor.get('name', 'Unknown Restaurant')

        # Location name for context
        location = item_root.get('vendorLocation', {})
        location_name = location.get('name', '')
        if location_name:
            self.restaurant_name = f"{self.restaurant_name} — {location_name}"

        content  = item_root.get('content', {})
        sections = content.get('sections', [])

        items: List[MenuItem] = []
        seen: set = set()

        from processors.normalisation import normalise

        for section in sections:
            if section.get('hidden'):
                continue
            category = section.get('title', '')

            for raw in section.get('items', []):
                name = raw.get('name', '').strip()
                if not name:
                    continue

                key = (normalise(name), raw.get('price'))
                if key in seen:
                    continue
                seen.add(key)

                item_type = raw.get('type', 'SingleItem')

                if item_type == 'ItemBundle':
                    # Add the bundle as a parent item
                    bundle_item = _make_item(raw, category, is_option=False)
                    bundle_item.add_assumption(
                        'data_quality',
                        'Bundle item — customers select from variants at checkout. '
                        'Variants listed as separate option rows below.',
                        'info'
                    )
                    items.append(bundle_item)

                    # Add each variant as an option row
                    for group in raw.get('groups', []):
                        group_heading = group.get('heading', '')
                        for sub_raw in group.get('items', []):
                            sub_name = sub_raw.get('name', '').strip()
                            if not sub_name:
                                continue
                            sub_key = (normalise(sub_name), sub_raw.get('price'))
                            if sub_key in seen:
                                continue
                            seen.add(sub_key)

                            opt = _make_item(sub_raw, group_heading, is_option=True)
                            opt.add_assumption(
                                'data_quality',
                                f'Variant of bundle "{name}" ({group_heading})',
                                'info'
                            )
                            items.append(opt)

                else:
                    items.append(_make_item(raw, category, is_option=False))

        if not items:
            raise ValueError(
                "No menu items found in JEFB response. "
                "Check the URL is correct and the restaurant has an active menu at this location."
            )

        return items
