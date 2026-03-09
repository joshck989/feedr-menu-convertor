"""
Three-tier allergen lookup with full assumption tracking.
Tier 1: exact name match against source data allergens
Tier 2: fuzzy rule lookup (ADDON_ALLERGENS_FUZZY)
Tier 3: all-NO default + critical flag
"""

from typing import List, Dict, Tuple
from core.data_models import MenuItem
from data.allergen_map import ALLERGENS_14
from data.allergen_rules import ADDON_ALLERGENS_FUZZY, ADDON_FUZZY_FLAGS
from processors.normalisation import normalise


def _allergens_from_set(active: set) -> Dict[str, str]:
    return {a: ('YES' if a in active else 'NO') for a in ALLERGENS_14}


def _allergens_all_no() -> Dict[str, str]:
    return {a: 'NO' for a in ALLERGENS_14}


class AllergenProcessor:
    """Enriches MenuItem allergen fields using three-tier strategy."""

    def process(self, item: MenuItem, source_allergen_set: set = None) -> MenuItem:
        """
        source_allergen_set: set of allergen names already parsed from the data source.
        If provided → Tier 1 (use directly).
        Otherwise → Tier 2/3.
        """
        if source_allergen_set is not None:
            item.allergens = _allergens_from_set(source_allergen_set)
            item.allergen_source = 'source'
            item.add_assumption(
                'allergen',
                'Allergens taken directly from source data',
                'info'
            )
            return item

        norm = normalise(item.name)

        # Tier 2: fuzzy lookup
        if norm in ADDON_ALLERGENS_FUZZY:
            active = ADDON_ALLERGENS_FUZZY[norm]
            item.allergens = _allergens_from_set(active)
            item.allergen_source = 'fuzzy'
            pos = [a for a in active] if active else ['none']
            item.add_assumption(
                'allergen',
                f'Allergens inferred from known ingredient rules: {", ".join(pos) if active else "none"}',
                'warning' if norm in ADDON_FUZZY_FLAGS else 'info'
            )
            if norm in ADDON_FUZZY_FLAGS:
                item.add_assumption(
                    'allergen',
                    f'VERIFY: {ADDON_FUZZY_FLAGS[norm]}',
                    'warning'
                )
        else:
            # Tier 3: unknown
            item.allergens = _allergens_all_no()
            item.allergen_source = 'unknown'
            item.add_assumption(
                'allergen',
                'No allergen data available — all set to NO. Manual review required.',
                'critical'
            )

        return item

    def process_all(self, items: List[MenuItem]) -> List[MenuItem]:
        for item in items:
            # source_allergen_set is expected to be pre-populated on MenuItem
            # by the adapter if available; we pass None to trigger fuzzy path
            # unless the adapter set item.allergen_source = 'source'
            if item.allergen_source != 'source':
                self.process(item)
        return items
