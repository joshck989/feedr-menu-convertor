"""
Generic web menu adapter.
Uses BeautifulSoup + heuristics to extract menu items from any restaurant website.
Best-effort — accuracy varies by site structure.
"""

import re
import requests
from typing import List
from urllib.parse import urlparse
from bs4 import BeautifulSoup

from adapters.base import BaseAdapter
from core.data_models import MenuItem


HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
}

PRICE_RE = re.compile(r'£\s*(\d+(?:[.,]\d{1,2})?)')


def _clean(text: str) -> str:
    return re.sub(r'\s+', ' ', text).strip()


class GenericWebAdapter(BaseAdapter):
    """Heuristic menu extraction from restaurant websites."""

    def __init__(self):
        super().__init__()
        self._soup: BeautifulSoup = None

    def fetch(self, source: str) -> None:
        resp = requests.get(source, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        self._soup = BeautifulSoup(resp.text, 'lxml')
        # Try to get restaurant name from page title
        title = self._soup.find('title')
        if title:
            self.restaurant_name = _clean(title.get_text().split('|')[0].split('-')[0])

    def parse(self) -> List[MenuItem]:
        if not self._soup:
            raise ValueError("No content loaded.")

        items = []
        current_category = ''

        # Walk through all heading and paragraph elements
        # Strategy: headings near prices → category, text near price → item name
        all_elements = self._soup.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'li', 'div', 'span'])

        i = 0
        while i < len(all_elements):
            el = all_elements[i]
            text = _clean(el.get_text())

            # Update category from headings
            if el.name in ('h2', 'h3', 'h4') and text and len(text) < 60:
                current_category = text

            # Look for price patterns
            price_match = PRICE_RE.search(text)
            if price_match:
                price_str = f'£{price_match.group(1)}'
                # Name is likely in a nearby sibling or child element
                name = ''
                desc = ''

                # Check parent for structured menu items
                parent = el.parent
                if parent:
                    name_el = parent.find(['h3', 'h4', 'h5', 'strong', 'b'])
                    name = _clean(name_el.get_text()) if name_el else ''
                    if not name:
                        # Use text before price
                        before_price = text[:price_match.start()].strip()
                        if before_price and len(before_price) > 2:
                            name = before_price[:80]

                    # Description: first <p> in parent that isn't just a price
                    for p in parent.find_all('p'):
                        p_text = _clean(p.get_text())
                        if p_text and not PRICE_RE.search(p_text) and p_text != name:
                            desc = p_text[:200]
                            break

                if name and len(name) > 1:
                    items.append(MenuItem(
                        name=name,
                        category=current_category,
                        description=desc,
                        price=price_str,
                        is_option=False,
                    ))
            i += 1

        # Deduplicate by normalised name+price
        from processors.normalisation import normalise
        seen = set()
        unique = []
        for item in items:
            key = (normalise(item.name), item.price)
            if key not in seen:
                seen.add(key)
                item.add_assumption(
                    'data_quality',
                    'Extracted via heuristic web scraping — verify names, prices, and descriptions',
                    'warning'
                )
                unique.append(item)

        return unique
