# Feedr Menu Converter

A Streamlit application for converting restaurant menu data from multiple platforms into the Feedr upload format.

## Installation

```bash
pip install -r requirements.txt
```

## Running the App

```bash
streamlit run app.py
```

## Supported Platforms

- **Ordit** - CSV exports from Ordit-powered ordering sites
- **JEFB** - CSV/Excel file uploads
- **Deliveroo** - URL scraping with __NEXT_DATA__ JSON extraction + BeautifulSoup fallback
- **Generic Web Menu** - Heuristic extraction from any restaurant website

## Architecture

### Data Flow

1. **Adapter Layer** (`adapters/`) - Platform-specific data extraction
   - OrditAdapter: CSV parsing with allergen code mapping
   - JEFBAdapter: Excel/CSV with flexible column detection
   - DeliverooAdapter: JavaScript SPA with JSON + heuristic fallback
   - GenericWebAdapter: Website scraping with price pattern detection

2. **Processing Pipeline** (`core/pipeline.py`) - 6-stage enrichment
   - Stage 1: Extract items from source
   - Stage 2: Allergen enrichment (3-tier lookup)
   - Stage 3: VAT rate assignment (3-tier matching)
   - Stage 4: Nutrition data lookup
   - Stage 5: Image URL validation
   - Stage 6: Data quality checks

3. **Processors** (`processors/`)
   - **AllergenProcessor**: Source data → Fuzzy rules → Unknown (critical flag)
   - **VatProcessor**: Exact match → Manual override → Word-overlap inference
   - **NutritionProcessor**: Database lookup for known items
   - **ImageProcessor**: URL validation + hotlinking risk detection
   - **Normalisation**: Aggressive text standardization for fuzzy matching

4. **Output Generators** (`outputs/`)
   - **Readable CSV**: QA-friendly format with assumptions visible
   - **Feedr Template CSV**: 73-column format ready for upload

### Assumption Tracking

Every inference is tracked with:
- **Category**: allergen | vat | image | nutrition | data_quality
- **Severity**: info | warning | critical
- **Detail**: Human-readable explanation

## Data Files

### `data/allergen_rules.py`
- 14-allergen mapping (internal names ↔ Feedr columns)
- Fuzzy lookup for ~100 known addon items
- Uncertainty flags for manual review

### `data/nutrition_dict.py`
- Known nutrition data for ~20 common ATIS menu items
- (kcal, protein_g, carbs_g, fat_g) tuples

### `data/vat_overrides.py`
- Manual VAT overrides for items where matching fails
- UK VAT category heuristics

## Example Usage

```python
from adapters.ordit import OrditAdapter
from core.pipeline import ProcessingPipeline

adapter = OrditAdapter()
pipeline = ProcessingPipeline(adapter)
result = pipeline.run("path/to/menu.csv")

# Access results
print(f"Processed {len(result.items)} items")
print(f"Critical issues: {len(result.criticals)}")

# Generate outputs
from outputs.feedr_template_csv import generate
feedr_csv = generate(result)
```

## Key Features

- **Multi-platform support** with platform-agnostic MenuItem model
- **Assumption tracking** - every inference is logged with severity level
- **3-tier matching strategies** for allergens and VAT rates
- **Fuzzy matching** with stop-word filtering and word-overlap detection
- **Hotlinking detection** for CDN-hosted images
- **Data quality flags** for missing prices, blank names, etc.

## Output CSVs

### Readable CSV
Human-readable QA format with:
- Item details (name, category, price)
- Allergens (contains / free from)
- VAT info and source
- Nutrition data
- Full assumption trail

### Feedr Upload CSV
Production-ready format with:
- 73 required Feedr columns
- All allergen fields (14 allergens + sub-allergens)
- Dietary flags (vegan, vegetarian, etc.)
- Nutrition fields
- Assumptions column for reference

## Known Limitations

- Deliveroo page structure changes break extraction (requires manual update)
- JEFB adapter assumes standard column names (Name, Price, Category, etc.)
- Allergen fuzzy matching requires exact item name normalization
- Nutrition data only available for ~20 ATIS menu items

## Built for Feedr onboarding team
