"""Validates image URLs and flags hotlinking risks."""

from typing import List
from core.data_models import MenuItem

# CDN patterns known to be volatile / hotlink-risky
RISKY_CDN_PATTERNS = [
    'ordit',
    'ordit-images',
    's3.amazonaws.com',
    'cloudfront.net/restaurants',
]


class ImageProcessor:

    def process(self, item: MenuItem) -> MenuItem:
        url = item.image_url.strip() if item.image_url else ''
        if not url:
            item.add_assumption('image', 'No image URL — upload manually to a stable host', 'warning', 'Image URL')
            return item

        if not url.startswith(('http://', 'https://')):
            item.add_assumption('image', f'Invalid image URL format: {url[:60]}', 'critical', 'Image URL')
            return item

        for pattern in RISKY_CDN_PATTERNS:
            if pattern in url.lower():
                item.add_assumption(
                    'image',
                    f'Hotlinking risk: URL uses {pattern} CDN. If they change hosting, images will break. Consider re-hosting.',
                    'warning',
                    'Image URL'
                )
                return item

        item.add_assumption('image', 'Image URL appears valid', 'info', 'Image URL')
        return item

    def process_all(self, items: List[MenuItem]) -> List[MenuItem]:
        return [self.process(item) for item in items]
