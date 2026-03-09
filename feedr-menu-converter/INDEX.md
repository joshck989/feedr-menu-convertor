# Feedr Menu Converter - Code Index

## Quick Navigation

### Getting Started
1. Read README.md for overview
2. Install dependencies: pip install -r requirements.txt
3. Run: streamlit run app.py

### File Organization

#### Entry Point
- app.py - Streamlit web UI
  - Handles 4 platform selections
  - File upload interface
  - Results display with download buttons
  - Assumption breakdown expanders

#### Data Models & Configuration
- core/data_models.py - Core dataclasses
  - Assumption - Inference tracking
  - MenuItem - Menu item with full trail
  - PipelineResult - Pipeline output
  
- core/constants.py - 73-column Feedr template headers

- core/pipeline.py - Main orchestration
  - ProcessingPipeline class
  - 6-stage processing
  - Assumption aggregation

#### Data & Knowledge Bases
- data/allergen_rules.py - Allergen definitions
  - ALLERGEN_CODE_MAP - Code to name mapping (19 entries)
  - ADDON_ALLERGENS_FUZZY - Item to allergen mapping (79 entries)
  - ADDON_FUZZY_FLAGS - Uncertainty flags

- data/allergen_map.py - Allergen output mapping
  - ALLERGEN_MAP - Internal name to Feedr column
  - ALLERGENS_14 - List of 14 allergen names

- data/nutrition_dict.py - Nutrition data
  - NUTRITION - Item name to (kcal, protein, carbs, fat)

- data/vat_overrides.py - VAT rules
  - MANUAL_VAT - Hardcoded overrides
  - Category heuristics

#### Processors
- processors/normalisation.py - Text standardization
  - normalise() - Aggressive normalization
  - sig_words() - Significant word extraction

- processors/allergen_processor.py - Allergen enrichment
  - AllergenProcessor class
  - 3-tier lookup strategy:
    1. Source data
    2. Fuzzy rules
    3. All-NO (critical flag)

- processors/vat_processor.py - VAT assignment
  - VatProcessor class
  - 3-tier matching strategy:
    1. Exact name match
    2. Manual override
    3. Word-overlap

- processors/nutrition_processor.py - Nutrition lookup
  - NutritionProcessor class
  - Database lookup for known items

- processors/image_processor.py - Image URL validation
  - ImageProcessor class
  - Hotlink risk detection
  - URL format validation

#### Platform Adapters
- adapters/base.py - Abstract base class
  - BaseAdapter - Interface all adapters implement

- adapters/ordit.py - Ordit CSV handler
  - OrditAdapter class
  - Allergen code parsing
  - Column flexibility

- adapters/jefb.py - JEFB Excel/CSV
  - JEFBAdapter class
  - Excel and CSV support
  - Flexible column detection

- adapters/deliveroo.py - Deliveroo scraper
  - DeliverooAdapter class
  - NEXT_DATA JSON extraction
  - BeautifulSoup fallback

- adapters/generic_web.py - Generic website scraper
  - GenericWebAdapter class
  - Price pattern detection
  - Heuristic category assignment

#### Output Generators
- outputs/readable_csv.py - QA CSV
  - generate() - Creates human-readable CSV
  - Shows assumptions inline

- outputs/feedr_template_csv.py - Upload CSV
  - generate() - Creates 73-column Feedr format
  - Summary header block
  - All allergen columns populated

## Data Flow

User Input → Adapter → MenuItem objects → Processors → Output CSVs

Step by step:
1. fetch() - Platform-specific extraction
2. parse() - Convert to MenuItem objects
3. AllergenProcessor - 3-tier allergen lookup
4. VatProcessor - 3-tier VAT matching
5. NutritionProcessor - Nutrition data lookup
6. ImageProcessor - Image validation
7. Data quality checks - Final QA
8. PipelineResult - Aggregate assumptions
9. Output generators - Two CSV formats
10. Download CSVs

## Key Concepts

### 3-Tier Strategy
Both allergens and VAT use 3-tier matching:
1. High confidence - Source data or exact match
2. Medium confidence - Fuzzy rules or manual override
3. Low confidence - Inference or default (flagged)

### Assumption Tracking
Every inference generates an Assumption with:
- category - allergen | vat | image | nutrition | data_quality
- detail - Human-readable explanation
- severity - info | warning | critical
- field - Affected CSV column (optional)

### Normalisation
Aggressive text standardization for fuzzy matching:
- Strip brackets: [NEW], [HOT] removed
- Convert dashes: " - " to space
- Unify symbols: & + to "and"
- Case: UPPERCASE to lowercase
- Whitespace: collapse to single space

## Extension Points

### Adding a New Platform
1. Create adapters/myplatform.py
2. Extend BaseAdapter
3. Implement fetch() and parse()
4. Add to get_adapter() in app.py

### Adding Processor
1. Create class in processors/newprocessor.py
2. Implement process(item) and process_all(items)
3. Add to pipeline stages in core/pipeline.py

### Adding Allergen Rules
1. Update ADDON_ALLERGENS_FUZZY in data/allergen_rules.py
2. Add flag in ADDON_FUZZY_FLAGS if uncertain

### Adding Nutrition Data
1. Add entry to NUTRITION in data/nutrition_dict.py
2. Key is normalised item name

## Architecture Decisions

### Why 3-Tier?
- Handles both high-confidence (source) and low-confidence (unknown) data
- Allows gradual degradation with transparency
- Supports manual overrides at the middle tier

### Why Assumption Tracking?
- Regulatory requirements need audit trail
- Users need to know what's inferred vs sourced
- Enables quick manual review of risky inferences

### Why Multiple Adapters?
- Different platforms have different data structures
- Allows platform-specific parsing logic
- Makes code testable per-platform

### Why Separate Processors?
- Each processor focuses on one concern
- Easy to test, debug, extend
- Can be reordered or conditionally skipped

## Performance

- Memory: ~10MB for 1000 items
- Time: <1 second for 1000 items (no network)
- Network: 20-30 seconds for URL scraping
- CSV generation: <100ms for 1000 items

## Known Limitations

- Deliveroo structure changes require manual update
- Fuzzy matching requires exact normalization
- JEFB assumes standard column names
- Nutrition data limited to ~20 items

## Testing

All modules import successfully and pass validation tests.
See DEPLOYMENT.md for full test results.

