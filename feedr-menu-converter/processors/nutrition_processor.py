"""Enriches main menu items with nutrition data from NUTRITION dict."""

from typing import List
from core.data_models import MenuItem
from data.nutrition_dict import NUTRITION
from processors.normalisation import normalise


class NutritionProcessor:

    def process(self, item: MenuItem) -> MenuItem:
        if item.is_option:
            return item  # Don't populate nutrition for addon options

        norm = normalise(item.name)
        if norm in NUTRITION:
            kcal, protein, carbs, fat = NUTRITION[norm]
            item.nutrition = {
                'kcal': str(kcal),
                'protein': str(protein),
                'carbs': str(carbs),
                'fat': str(fat),
            }
            item.add_assumption('nutrition', f'Nutrition data from known database (kcal={kcal})', 'info')
        else:
            item.add_assumption('nutrition', 'No nutrition data available — populate manually', 'info')
        return item

    def process_all(self, items: List[MenuItem]) -> List[MenuItem]:
        return [self.process(item) for item in items]
