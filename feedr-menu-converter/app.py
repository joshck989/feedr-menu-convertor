"""
Feedr Menu Converter
A tool for converting restaurant menu data into the Feedr upload format.
Paste a URL, choose a platform, download two CSVs.
"""

import sys
import os

# Make sure our modules are on the path
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
from datetime import datetime

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title='Feedr Menu Converter',
    page_icon='🥗',
    layout='centered',
)

# ── CSS ───────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.main { max-width: 780px; }
.stAlert { border-radius: 8px; }
</style>
""", unsafe_allow_html=True)


def get_adapter(platform: str):
    if platform == 'Ordit':
        from adapters.ordit import OrditAdapter
        return OrditAdapter()
    elif platform == 'JEFB':
        from adapters.jefb import JEFBAdapter
        return JEFBAdapter()
    elif platform == 'Deliveroo':
        from adapters.deliveroo import DeliverooAdapter
        return DeliverooAdapter()
    else:
        from adapters.generic_web import GenericWebAdapter
        return GenericWebAdapter()


# ── Header ────────────────────────────────────────────────────────────────────
st.title('🥗 Feedr Menu Converter')
st.caption('Convert restaurant menus into the Feedr upload format. Paste a URL, choose a platform, download your CSVs.')
st.divider()

# ── Input section ────────────────────────────────────────────────────────────
platform = st.selectbox(
    'Platform',
    ['Ordit', 'JEFB', 'Deliveroo', 'Generic Web Menu'],
    help='Choose the source platform for this restaurant\'s menu'
)

PLATFORM_HINTS = {
    'Ordit':           'e.g. https://order.restaurantname.com/...',
    'JEFB':            'e.g. https://app.business.just-eat.co.uk/menus/vendors/farmer-j/st-james',
    'Deliveroo':       'e.g. https://deliveroo.co.uk/menu/London/city/restaurant-name',
    'Generic Web Menu':'e.g. https://www.restaurantname.co.uk/menu',
}

source_input = st.text_input(
    'Menu URL',
    placeholder=PLATFORM_HINTS.get(platform, 'https://...'),
    help='Paste the restaurant menu URL. The UI page URL is fine — the adapter will find the data behind it.'
)
uploaded_bytes = None
uploaded_file = None

# JEFB JSON paste fallback
jefb_json_paste = None
if platform == 'JEFB':
    with st.expander('Having trouble? Paste the JSON instead'):
        st.markdown("""
The JEFB API sometimes blocks automated requests. If you get a 403 error, do this:

1. Make sure you are logged into [app.business.just-eat.co.uk](https://app.business.just-eat.co.uk)
2. Open the API URL directly in your browser — replace `menus/vendors/farmer-j/st-james` with your restaurant's slugs:
   `https://app.business.just-eat.co.uk/api/public/deliverable-menus/`**vendor-slug**`/2026-03-12T13:00:00.000Z?locationSlug=`**location-slug**
3. You'll see a page of raw JSON text — select all (Ctrl+A / Cmd+A), copy, and paste it below.
""")
        jefb_json_paste = st.text_area(
            'Paste JSON here',
            height=120,
            placeholder='{"item": {"vendor": {"name": "..."}, ...',
            label_visibility='collapsed',
        )

# Optional VAT file
with st.expander('Optional: Upload VAT rates file'):
    vat_file = st.file_uploader(
        'VAT file (CSV with Item and VAT Rate columns)',
        type=['csv'],
        key='vat_upload',
    )

convert_btn = st.button('Convert Menu', type='primary', use_container_width=True)

# ── Processing ────────────────────────────────────────────────────────────────
if convert_btn:
    has_jefb_json = platform == 'JEFB' and jefb_json_paste and jefb_json_paste.strip()
    if not source_input and not uploaded_file and not has_jefb_json:
        st.error('Please enter a URL or paste JSON first.')
        st.stop()

    with st.spinner('Processing menu...'):
        try:
            from core.pipeline import ProcessingPipeline

            adapter = get_adapter(platform)
            pipeline = ProcessingPipeline(adapter)

            # Inject VAT lookup from uploaded file if provided
            if vat_file:
                import csv, io
                vat_content = vat_file.read().decode('utf-8-sig')
                vat_lookup = {}
                from processors.normalisation import normalise
                for row in csv.DictReader(io.StringIO(vat_content)):
                    item = row.get('Item', '').strip()
                    rate = row.get('VAT Rate', '').strip()
                    if item and rate:
                        try:
                            rate_val = str(int(float(rate.replace('%', ''))))
                            vat_lookup[normalise(item)] = rate_val
                        except ValueError:
                            pass
                pipeline.vat_lookup = vat_lookup

            # For JEFB: use pasted JSON if provided, otherwise fetch from URL
            if has_jefb_json:
                adapter.fetch_json_string(jefb_json_paste.strip())
                items = adapter.parse()
                adapter.extract = lambda source: items
                result = pipeline.run(source='pasted_json')
            else:
                result = pipeline.run(
                    source=source_input or '',
                    uploaded_bytes=uploaded_bytes
                )

            # Generate outputs
            from outputs.readable_csv import generate as gen_readable
            from outputs.feedr_template_csv import generate as gen_feedr

            readable_bytes = gen_readable(result)
            feedr_bytes    = gen_feedr(result)
            slug = result.restaurant_name.replace(' ', '_').lower()[:30]

            # Store in session state so downloads persist after button clicks
            st.session_state['result']         = result
            st.session_state['readable_bytes'] = readable_bytes
            st.session_state['feedr_bytes']    = feedr_bytes
            st.session_state['slug']           = slug

        except Exception as e:
            err_str = str(e)
            if '403' in err_str and platform == 'JEFB':
                st.error(
                    '**JEFB returned a 403 — the API requires you to be logged in.**\n\n'
                    'Use the "Having trouble? Paste the JSON instead" section above:\n'
                    '1. Log into app.business.just-eat.co.uk in your browser\n'
                    '2. Open the API URL directly (swap in your vendor/location slugs):\n'
                    '   `https://app.business.just-eat.co.uk/api/public/deliverable-menus/`**vendor**`/2026-03-12T13:00:00.000Z?locationSlug=`**location**\n'
                    '3. Copy all the text, paste it into the JSON box, and click Convert again.'
                )
            else:
                st.error(f'Something went wrong: {e}')
            import traceback
            with st.expander('Full error details'):
                st.code(traceback.format_exc())

# ── Results panel — rendered from session state so it survives download clicks ─
if 'result' in st.session_state:
    result         = st.session_state['result']
    readable_bytes = st.session_state['readable_bytes']
    feedr_bytes    = st.session_state['feedr_bytes']
    slug           = st.session_state['slug']

    st.divider()
    st.success(f'✓ {result.summary["total"]} items processed from **{result.restaurant_name}**')

    col1, col2, col3 = st.columns(3)
    col1.metric('Menu items', result.summary['main_items'])
    col2.metric('Options', result.summary['options'])
    col3.metric('Critical issues', result.summary['criticals'])

    c1, c2 = st.columns(2)
    c1.download_button(
        '⬇ Download Readable CSV',
        data=readable_bytes,
        file_name=f'{slug}_menu_readable.csv',
        mime='text/csv',
        use_container_width=True,
    )
    c2.download_button(
        '⬇ Download Feedr Upload CSV',
        data=feedr_bytes,
        file_name=f'{slug}_feedr_upload.csv',
        mime='text/csv',
        use_container_width=True,
    )

    # ── Assumption breakdown ──────────────────────────────────────────
    if result.summary['criticals']:
        criticals = [a for i in result.items for a in i.assumptions if a.severity == 'critical']
        with st.expander(f'❌ Critical issues ({result.summary["criticals"]}) — must fix before uploading'):
            for a in criticals:
                st.error(a.detail)

    if result.summary['warnings']:
        warnings = [a for i in result.items for a in i.assumptions if a.severity == 'warning']
        with st.expander(f'⚠ Warnings ({result.summary["warnings"]})'):
            for a in warnings[:50]:
                st.warning(a.detail)
            if len(warnings) > 50:
                st.caption(f'... and {len(warnings) - 50} more (see CSV)')

    with st.expander('ℹ Assumption breakdown'):
        s = result.summary
        st.markdown(f"""
**Allergen sources**
- From source data: {s['allergen_sources'].get('source', 0)}
- Inferred (fuzzy rules): {s['allergen_sources'].get('fuzzy', 0)}
- Unknown (manual review): {s['allergen_sources'].get('unknown', 0)}

**VAT matching**
- Exact match: {s['vat_sources'].get('exact', 0)}
- Word-overlap inferred: {s['vat_sources'].get('word_overlap', 0)}
- Manual override: {s['vat_sources'].get('manual', 0)}
- Unknown: {s['vat_sources'].get('unknown', 0)}

**Coverage**
- Items with images: {s['with_images']} / {s['total']}
- Items with nutrition: {s['with_nutrition']} / {s['total']}
""")

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption('Feedr Menu Converter · Built for the Feedr onboarding team')
