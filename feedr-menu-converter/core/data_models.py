"""Core data models for the Feedr Menu Converter pipeline."""

from dataclasses import dataclass, field
from typing import Optional, List, Dict


@dataclass
class Assumption:
    """A single assumption or inference made during processing."""
    category: str    # 'allergen' | 'vat' | 'image' | 'nutrition' | 'data_quality'
    detail: str      # Human-readable explanation
    severity: str    # 'info' | 'warning' | 'critical'
    field: str = ''  # Affected CSV column name (optional)

    def __str__(self):
        icon = {'info': 'i', 'warning': '!', 'critical': 'X'}.get(self.severity, '')
        return f"[{self.severity.upper()}] {self.detail}"


@dataclass
class MenuItem:
    """
    Normalised menu item carrying all data + a full assumption trail.
    Grows as it passes through each processor.
    """
    name: str
    category: str                     = ''
    description: str                  = ''
    price: str                        = ''
    allergens: Dict[str, str]         = field(default_factory=dict)   # {Gluten: 'YES'/'NO', ...}
    allergen_source: str              = 'unknown'   # 'source' | 'fuzzy' | 'inferred' | 'unknown'
    vat_rate: str                     = ''
    vat_source: str                   = 'unknown'   # 'exact' | 'word_overlap' | 'manual' | 'unknown'
    image_url: str                    = ''
    nutrition: Dict[str, str]         = field(default_factory=dict)
    dietary: Dict[str, bool]          = field(default_factory=dict)
    is_option: bool                   = False
    assumptions: List[Assumption]     = field(default_factory=list)

    def add_assumption(self, category: str, detail: str, severity: str, field: str = ''):
        self.assumptions.append(Assumption(category, detail, severity, field))


@dataclass
class PipelineResult:
    """Final output of the full processing pipeline."""
    items: List[MenuItem]
    global_assumptions: List[Assumption]
    summary: Dict
    platform: str
    restaurant_name: str
    timestamp: str

    @property
    def criticals(self) -> List:
        all_a = [a for item in self.items for a in item.assumptions] + self.global_assumptions
        return [a for a in all_a if a.severity == 'critical']

    @property
    def warnings(self) -> List:
        all_a = [a for item in self.items for a in item.assumptions] + self.global_assumptions
        return [a for a in all_a if a.severity == 'warning']
