"""Abstract base class for all platform adapters."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from core.data_models import MenuItem


class BaseAdapter(ABC):
    """
    All adapters must implement fetch() and parse() to return a list of
    partially-populated MenuItem objects. Processors enrich them further.
    """

    def __init__(self):
        self.restaurant_name: str = 'Unknown Restaurant'
        self.raw_data = None

    @abstractmethod
    def fetch(self, source: str) -> None:
        """Retrieve raw data from source (URL or file path)."""

    @abstractmethod
    def parse(self) -> List[MenuItem]:
        """Convert raw data to list of MenuItem objects."""

    def extract(self, source: str) -> List[MenuItem]:
        self.fetch(source)
        return self.parse()
