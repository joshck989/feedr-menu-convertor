"""
Three-tier VAT matching with assumption tracking.
Tier 1: exact normalised name match against loaded VAT data
Tier 2: word-overlap match
Tier 3: manual override dict
"""

from typing import Dict, List, Optional
from core.data_models import MenuItem
from data.vat_overrides import MANUAL_VAT
from processors.normalisation import normalise, sig_words


class VatProcessor:
    """
    Matches VAT rates from a provided lookup dict.
    Can be initialised empty (rates unknown) or with a pre-loaded dict.
    """

    def __init__(self, vat_lookup: Optional[Dict[str, str]] = None):
        self.vat_lookup = vat_lookup or {}
        self._lookup_words = {n: sig_words(n) for n in self.vat_lookup}

    def load_from_csv(self, filepath: str):
        """Load VAT rates from a CSV file (Item, VAT Rate columns)."""
        import csv
        with open(filepath, newline='', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                item = row.get('Item', '').strip()
                rate = row.get('VAT Rate', '').strip()
                if not item or not rate:
                    continue
                try:
                    rate_val = str(int(float(rate.replace('%', ''))))
                    self.vat_lookup[normalise(item)] = rate_val
                except ValueError:
                    pass
        self._lookup_words = {n: sig_words(n) for n in self.vat_lookup}

    def match(self, item: MenuItem) -> MenuItem:
        # If the adapter already sourced VAT directly (e.g. JEFB vatRateType),
        # skip the lookup tiers — don't overwrite with 'unknown'.
        if item.vat_source == 'source' and item.vat_rate:
            return item

        raw = item.name
        norm = normalise(raw)

        # Tier 1: exact
        if norm in self.vat_lookup:
            item.vat_rate = self.vat_lookup[norm]
            item.vat_source = 'exact'
            item.add_assumption('vat', f'VAT {item.vat_rate}%: exact name match', 'info', 'vatRate')
            return item

        # Tier 2: manual override
        if raw.lower() in MANUAL_VAT:
            item.vat_rate = MANUAL_VAT[raw.lower()]
            item.vat_source = 'manual'
            item.add_assumption('vat', f'VAT {item.vat_rate}%: manual override applied', 'info', 'vatRate')
            return item

        # Tier 3: word-overlap
        tmpl_words = sig_words(norm)
        best = None
        for lnorm, lwords in self._lookup_words.items():
            if lwords and lwords.issubset(tmpl_words):
                if best is None or len(lnorm) > len(best):
                    best = lnorm
        if best:
            item.vat_rate = self.vat_lookup[best]
            item.vat_source = 'word_overlap'
            item.add_assumption('vat', f'VAT {item.vat_rate}%: inferred by word-overlap match to "{best}"', 'warning', 'vatRate')
            return item

        item.vat_source = 'unknown'
        item.add_assumption('vat', 'VAT rate unknown — not in source data', 'warning', 'vatRate')
        return item

    def process_all(self, items: List[MenuItem]) -> List[MenuItem]:
        return [self.match(item) for item in items]
