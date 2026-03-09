"""
Deliveroo adapter.

Deliveroo is a JavaScript SPA — no clean public API.

Strategy (in order of preference):
1. Extract __NEXT_DATA__ JSON embedded in the page HTML
2. BeautifulSoup heuristic extraction
3. Warn user and suggest using Deliveroo Partner Portal export

NOTE: Deliveroo may change their page structure at any time.
This adapter is best-effort and may require manual updating.
"""

import re
import json
import requests
from typing import List, Optional, Dict
from bs4 import BeautifulSoup

from adapters.base import BaseAdapter
from core.data_models import MenuItem, Assumption


HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/120.0.0.0 Safari/537.36'
    ),
    'Accept-Language': 'en-GB,en;q=0.9',
}


class DeliverooAdapter(BaseAdapter):

    def __init__(self):
        super().__init__()
        self._html: str = ''
        self._items_raw: list = []
        self._method_used: str = 'unknown'

    def fetch(self, source: str) -> None:
        resp = requests.get(source, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        self._html = resp.text

    def fetch_bytes(self, content: bytes) -> None:
        """Accept pre-exported HTML from Deliveroo partner portal."""
        self._html = content.decode('utf-8', errors='replace')

    def _try_next_data(self) -> Optional[list]:
        """Try to extract __NEXT_DATA__ JSON embedded in the page."""
        match = re.search(r'<script[^>]*id=["\']__NEXT_DATA__["\'][^>]*>(.*?)</script>', self._html, re.DOTALL)
        if not match:
            return None
        try:
            data = json.loads(match.group(1))
            # Navigate to menu items — structure varies by Deliveroo version
            # Common path: props.pageProps.restaurant.menu.categories[].items[]
            props = data.get('props', {}).get('pageProps', {})
            restaurant = props.get('restaurant') or props.get('data', {}).get('restaurant', {})
            if restaurant:
                self.restaurant_name = restaurant.get('name', 'Unknown')
            menu = restaurant.get('menu', {}) if restaurant else {}
            categories = menu.get('categories', []) or menu.get('menus', [])
            items = []
            for cat in categories:
                cat_name = cat.get('name', '')
                for item in cat.get('items', []):
                    items.append({
                        'name': item.get('name', ''),
                        'description': item.get('description', ''),
                        'price': item.get('price', {}).get('formattedValue', '') if isinstance(item.get('price'), dict) else str(item.get('price', '')),
                        'image': item.get('image', {}).get('url', '') if isinstance(item.get('image'), dict) else item.get('imageUrl', ''),
                        'category': cat_name,
                    })
            return items if items else None
        except (json.JSONDecodeError, KeyError, TypeError):
            return None

    def _try_beautifulsoup(self) -> list:
        """Heuristic BeautifulSoup extraction — best effort."""
        soup = BeautifulSoup(self._html, 'lxml')
        items = []
        price_pattern = re.compile(r'£\s*\d+[\.,]\d{2}')

        # Common Deliveroo class patterns
        item_selectors = [
            {'attrs': {'data-testid': re.compile(r'menu-item|itemCard')}},
            {'class': re.compile(r'MenuItemCard|menuItem|food-item', re.I)},
        ]

        for selector in item_selectors:
            candidates = soup.find_all(True, **selector)
            if candidates:
                for el in candidates:
                    name_el = el.find(['h3', 'h4', 'h2'])
                    name = name_el.get_text(strip=True) if name_el else ''
                    if not name:
                        continue
                    desc_el = el.find('p')
                    desc = desc_el.get_text(strip=True) if desc_el else ''
                    price_match = price_pattern.search(el.get_text())
                    price = price_match.group(0) if price_match else ''
                    img_el = el.find('img')
                    image = img_el.get('src', '') if img_el else ''
                    items.append({'name': name, 'description': desc, 'price': price, 'image': image, 'category': ''})
                break

        return items

    def parse(self) -> List[MenuItem]:
        if not self._html:
            raise ValueError("No HTML content loaded. Call fetch() first.")

        items_raw = self._try_next_data()
        if items_raw:
            self._method_used = 'next_data_json'
        else:
            items_raw = self._try_beautifulsoup()
            self._method_used = 'beautifulsoup_heuristic'

        if not items_raw:
            raise ValueError(
                "Could not extract menu items from Deliveroo page. "
                "The page structure may have changed, or JavaScript rendering is required. "
                "Please export your menu from the Deliveroo Partner Hub and upload as a file instead."
            )

        items = []
        for raw in items_raw:
            name = raw.get('name', '').strip()
            if not name:
                continue
            item = MenuItem(
                name=name,
                category=raw.get('category', ''),
                description=raw.get('description', ''),
                price=raw.get('price', ''),
                image_url=raw.get('image', ''),
                is_option=False,
            )
            item.add_assumption(
                'data_quality',
                f'Extracted via {self._method_used} — verify accuracy before upload',
                'warning' if self._method_used == 'beautifulsoup_heuristic' else 'info'
            )
            items.append(item)

        return items
