"""
ProcessingPipeline orchestrates all processing stages with assumption tracking.
"""

from datetime import datetime
from typing import List, Optional, Dict

from core.data_models import MenuItem, PipelineResult, Assumption
from adapters.base import BaseAdapter
from processors.allergen_processor import AllergenProcessor
from processors.vat_processor import VatProcessor
from processors.nutrition_processor import NutritionProcessor
from processors.image_processor import ImageProcessor


class ProcessingPipeline:

    def __init__(
        self,
        adapter: BaseAdapter,
        vat_csv_path: Optional[str] = None,
        vat_lookup: Optional[Dict[str, str]] = None,
    ):
        self.adapter = adapter
        self.vat_csv_path = vat_csv_path
        self.vat_lookup = vat_lookup or {}

    def run(self, source: str, uploaded_bytes=None) -> PipelineResult:
        global_assumptions: List[Assumption] = []

        # Stage 1: Extract
        if uploaded_bytes is not None and hasattr(self.adapter, 'fetch_bytes'):
            self.adapter.fetch_bytes(uploaded_bytes)
            items = self.adapter.parse()
        else:
            items = self.adapter.extract(source)

        if not items:
            raise ValueError("No menu items found. Check the source URL/file and platform selection.")

        # Stage 2: Allergens
        allergen_proc = AllergenProcessor()
        items = allergen_proc.process_all(items)

        # Stage 3: VAT
        vat_proc = VatProcessor(self.vat_lookup)
        if self.vat_csv_path:
            vat_proc.load_from_csv(self.vat_csv_path)
        items = vat_proc.process_all(items)

        # Stage 4: Nutrition
        nutrition_proc = NutritionProcessor()
        items = nutrition_proc.process_all(items)

        # Stage 5: Images
        image_proc = ImageProcessor()
        items = image_proc.process_all(items)

        # Stage 6: Data quality checks
        missing_prices = [i.name for i in items if not i.price]
        missing_names  = [i for i in items if not i.name]
        if missing_prices:
            global_assumptions.append(Assumption(
                'data_quality',
                f'{len(missing_prices)} items have no price: {", ".join(missing_prices[:5])}{"..." if len(missing_prices) > 5 else ""}',
                'warning'
            ))
        if missing_names:
            global_assumptions.append(Assumption(
                'data_quality',
                f'{len(missing_names)} items have blank names — they will be skipped',
                'critical'
            ))
            items = [i for i in items if i.name]

        # Build summary
        allergen_sources = {}
        for item in items:
            allergen_sources[item.allergen_source] = allergen_sources.get(item.allergen_source, 0) + 1
        vat_sources = {}
        for item in items:
            vat_sources[item.vat_source] = vat_sources.get(item.vat_source, 0) + 1

        summary = {
            'total':            len(items),
            'main_items':       sum(1 for i in items if not i.is_option),
            'options':          sum(1 for i in items if i.is_option),
            'allergen_sources': allergen_sources,
            'vat_sources':      vat_sources,
            'with_images':      sum(1 for i in items if i.image_url),
            'with_nutrition':   sum(1 for i in items if i.nutrition),
            'criticals':        sum(1 for i in items for a in i.assumptions if a.severity == 'critical'),
            'warnings':         sum(1 for i in items for a in i.assumptions if a.severity == 'warning'),
        }

        return PipelineResult(
            items=items,
            global_assumptions=global_assumptions,
            summary=summary,
            platform=type(self.adapter).__name__.replace('Adapter', ''),
            restaurant_name=self.adapter.restaurant_name,
            timestamp=datetime.now().strftime('%Y-%m-%d %H:%M'),
        )
