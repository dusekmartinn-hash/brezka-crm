""" 
Brezka CRM — Streamlit aplikace
Spuštění: streamlit run app.py
"""

import json
import math
import sys
import time
import urllib.parse
import uuid
from pathlib import Path
from datetime import datetime, timedelta

import folium
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from folium.plugins import HeatMap
from streamlit_folium import st_folium

# Přidej root do path
sys.path.insert(0, str(Path(__file__).parent))
from config import WORKSHOP, SHEETS

# ─────────────────────────────────────────────────────────────
#  Konfigurace stránky
# ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Brezka CRM",
    page_icon="🔨",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────
#  Ochrana heslem
# ─────────────────────────────────────────────────────────────
if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False

if not st.session_state["authenticated"]:
    st.markdown(
        '<div style="max-width:360px;margin:120px auto;text-align:center;">'
        '<div style="font-size:48px;margin-bottom:16px;">🔨</div>'
        '<h2 style="color:#1a1a2e;margin-bottom:4px;">Brezka CRM</h2>'
        '<p style="color:#718096;font-size:14px;margin-bottom:24px;">'
        'Zadej heslo pro přístup</p>'
        '</div>',
        unsafe_allow_html=True,
    )
    _pw_col1, _pw_col2, _pw_col3 = st.columns([1, 1, 1])
    with _pw_col2:
        _pw = st.text_input("Heslo", type="password", label_visibility="collapsed",
                             placeholder="Heslo...")
        if st.button("Vstoupit", type="primary", use_container_width=True):
            if _pw == "A2A2":
                st.session_state["authenticated"] = True
                st.rerun()
            else:
                st.error("Špatné heslo")
    st.stop()

# ─────────────────────────────────────────────────────────────
#  CSS Design System
# ─────────────────────────────────────────────────────────────
st.markdown("""
<style>
/* ═══════════════════════════════════════════════
   BREZKA CRM — Design System v3
   Notebook (1366 / 1440) + Desktop (1920)
   ═══════════════════════════════════════════════ */

/* ── CSS proměnné ── */
:root {
    --brand:       #e74c3c;
    --brand-dark:  #c0392b;
    --brand-light: #fef5f4;
    --navy:        #1a1a2e;
    --slate:       #2d3748;
    --muted:       #718096;
    --subtle:      #a0aec0;
    --border:      #e8e5e0;
    --surface:     #faf9f7;
    --white:       #ffffff;
    --warm-bg:     #f7f5f2;
    --warm-border: #ece8e1;
    --accent-green:#10b981;
    --radius:      12px;
    --radius-sm:   8px;
    --shadow-sm:   0 1px 3px rgba(0,0,0,0.04), 0 1px 2px rgba(0,0,0,0.03);
    --shadow-md:   0 4px 16px rgba(0,0,0,0.06), 0 2px 6px rgba(0,0,0,0.04);
    --shadow-lg:   0 10px 30px rgba(0,0,0,0.08), 0 4px 10px rgba(0,0,0,0.04);
    --transition:  all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    --sidebar-w:   240px;
    --content-max: 1560px;
}

/* ── Reset Streamlit chrome ── */
#MainMenu, footer, header,
.stDeployButton,
[data-testid="stToolbar"]   { visibility: hidden !important;
                               display: none !important; }

/* ── Typografie ── */
html, body, [class*="css"] {
    font-family: "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI",
                 Roboto, sans-serif !important;
    -webkit-font-smoothing: antialiased;
    font-size: 14px;
    color: #2d3748 !important;
}
/* Force all markdown text visible */
.stMarkdown, .stMarkdown p, .stMarkdown span,
.stMarkdown li, .stMarkdown h1, .stMarkdown h2,
.stMarkdown h3, .stMarkdown h4, .stMarkdown h5 {
    color: #2d3748 !important;
}
.stCaption, [data-testid="stCaptionContainer"] p {
    color: #718096 !important;
}
/* Subheaders, expanders, labels */
.stSubheader, [data-testid="stSubheader"] {
    color: #1a1a2e !important;
}
details summary span {
    color: #2d3748 !important;
}
label[data-testid="stWidgetLabel"] p {
    color: #2d3748 !important;
}

/* ── Hlavní layout ── */
.stApp {
    background: var(--warm-bg) !important;
}
.block-container {
    padding-top: 1.4rem !important;
    padding-bottom: 3rem !important;
    padding-left: 2.2rem !important;
    padding-right: 2.2rem !important;
    max-width: var(--content-max) !important;
}

/* ═══════════════════════════════════════════════
   SIDEBAR — nav menu styl
   ═══════════════════════════════════════════════ */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1a1a2e 0%, #16213e 100%) !important;
    border-right: none !important;
    min-width: var(--sidebar-w) !important;
    max-width: var(--sidebar-w) !important;
    box-shadow: 4px 0 20px rgba(0,0,0,0.08) !important;
}
section[data-testid="stSidebar"] > div:first-child {
    padding-top: 0 !important;
}
/* Sidebar text — base */
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span:not([data-testid]),
section[data-testid="stSidebar"] small {
    color: var(--subtle) !important;
    font-size: 12px !important;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    color: #f1f5f9 !important;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(255,255,255,0.07) !important;
    margin: 8px 0 !important;
}

/* ── Navigace: radio → nav list ── */
section[data-testid="stSidebar"] [data-testid="stRadio"] {
    width: 100% !important;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] > div {
    gap: 1px !important;
    flex-direction: column !important;
}
/* Každá položka nav */
section[data-testid="stSidebar"] [data-testid="stRadio"] label {
    display: flex !important;
    align-items: center !important;
    padding: 9px 14px !important;
    border-radius: 8px !important;
    cursor: pointer !important;
    transition: background 0.13s ease, color 0.13s ease !important;
    margin: 0 !important;
    width: 100% !important;
    box-sizing: border-box !important;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(255,255,255,0.07) !important;
}
/* Schovej radio kolečko */
section[data-testid="stSidebar"] [data-testid="stRadio"] label > div:first-child {
    display: none !important;
}
/* Text v nav položce */
section[data-testid="stSidebar"] [data-testid="stRadio"] label > div p,
section[data-testid="stSidebar"] [data-testid="stRadio"] label p {
    color: #94a3b8 !important;
    font-size: 13.5px !important;
    font-weight: 500 !important;
    line-height: 1.3 !important;
    margin: 0 !important;
    transition: color 0.13s ease !important;
}
/* Aktivní položka (checked) */
section[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) {
    background: rgba(255,255,255,0.12) !important;
    border-left: 3px solid var(--brand) !important;
    padding-left: 11px !important;
    box-shadow: inset 0 0 0 1px rgba(255,255,255,0.06);
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked) p {
    color: #f1f5f9 !important;
    font-weight: 600 !important;
}
section[data-testid="stSidebar"] [data-testid="stRadio"] label:has(input:checked):hover {
    background: rgba(255,255,255,0.15) !important;
}

/* Sidebar metriky */
section[data-testid="stSidebar"] [data-testid="metric-container"] {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(255,255,255,0.08) !important;
    border-radius: 8px !important;
    box-shadow: none !important;
    padding: 8px 12px !important;
}
section[data-testid="stSidebar"] [data-testid="stMetricValue"] {
    color: #f1f5f9 !important;
    font-size: 18px !important;
    font-weight: 700 !important;
}
section[data-testid="stSidebar"] [data-testid="stMetricLabel"] p {
    color: var(--muted) !important;
    font-size: 10px !important;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}

/* ═══════════════════════════════════════════════
   KPI METRIKY (hlavní oblast)
   ═══════════════════════════════════════════════ */
[data-testid="metric-container"] {
    background: var(--white);
    border: 1px solid var(--warm-border);
    border-radius: var(--radius);
    padding: 18px 22px 16px !important;
    box-shadow: var(--shadow-sm);
    transition: var(--transition);
    position: relative;
    overflow: hidden;
}
[data-testid="metric-container"]::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--brand) 0%, #f59e0b 100%);
    opacity: 0;
    transition: opacity 0.2s ease;
}
[data-testid="metric-container"]:hover {
    box-shadow: var(--shadow-md);
    border-color: var(--border);
    transform: translateY(-2px);
}
[data-testid="metric-container"]:hover::before {
    opacity: 1;
}
[data-testid="stMetricLabel"] p {
    font-size: 10.5px !important;
    font-weight: 700 !important;
    text-transform: uppercase;
    letter-spacing: 0.7px;
    color: var(--muted) !important;
}
[data-testid="stMetricValue"] {
    font-size: 30px !important;
    font-weight: 800 !important;
    color: var(--navy) !important;
    letter-spacing: -0.5px;
    line-height: 1.1 !important;
}
[data-testid="stMetricDelta"] {
    font-size: 11px !important;
}

/* ═══════════════════════════════════════════════
   TLAČÍTKA
   ═══════════════════════════════════════════════ */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    border: 1px solid var(--border) !important;
    transition: var(--transition) !important;
    padding: 4px 12px !important;
    height: 32px !important;
    line-height: 1 !important;
    color: var(--slate) !important;
}
.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow-md) !important;
    border-color: #94a3b8 !important;
    background: var(--surface) !important;
    color: var(--navy) !important;
}
.stButton > button:active {
    transform: translateY(0) !important;
    box-shadow: none !important;
}
.stButton > button[kind="primary"] {
    background: linear-gradient(135deg, #e74c3c 0%, #d63031 50%, #c0392b 100%) !important;
    border: none !important;
    color: white !important;
    box-shadow: 0 2px 8px rgba(231,76,60,0.25), 0 1px 3px rgba(0,0,0,0.1) !important;
    font-weight: 600 !important;
    letter-spacing: 0.2px;
}
.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 20px rgba(231,76,60,0.35), 0 2px 6px rgba(0,0,0,0.12) !important;
    background: linear-gradient(135deg, #ef5350 0%, #e74c3c 50%, #c0392b 100%) !important;
    color: white !important;
    transform: translateY(-2px) !important;
}
/* Icon tlačítka (▼ ▲ ✓ 📧) */
.stButton > button:has(> div > p:only-child) {
    padding: 2px 6px !important;
    min-height: 28px !important;
    height: 28px !important;
    font-size: 13px !important;
    color: var(--muted) !important;
    background: transparent !important;
    border-color: transparent !important;
}
.stButton > button:has(> div > p:only-child):hover {
    background: var(--surface) !important;
    border-color: var(--border) !important;
    color: var(--slate) !important;
}

/* Link tlačítka */
.stLinkButton > a {
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    padding: 4px 10px !important;
    height: 32px !important;
    transition: var(--transition) !important;
    text-decoration: none !important;
}
.stLinkButton > a:hover {
    transform: translateY(-1px);
    box-shadow: var(--shadow-md) !important;
}
.stDownloadButton > button {
    border-radius: 8px !important;
    font-weight: 500 !important;
    transition: var(--transition) !important;
}

/* ═══════════════════════════════════════════════
   TABY
   ═══════════════════════════════════════════════ */
.stTabs [data-baseweb="tab-list"] {
    background: var(--surface) !important;
    border-radius: 10px !important;
    padding: 3px !important;
    gap: 2px !important;
    border-bottom: none !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 7px !important;
    font-weight: 500 !important;
    font-size: 13px !important;
    padding: 6px 14px !important;
    color: var(--muted) !important;
    background: transparent !important;
    border: none !important;
    transition: var(--transition) !important;
}
.stTabs [data-baseweb="tab"]:hover {
    color: var(--slate) !important;
    background: rgba(0,0,0,0.04) !important;
}
.stTabs [aria-selected="true"] {
    background: var(--white) !important;
    color: var(--navy) !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.1) !important;
    font-weight: 600 !important;
}
.stTabs [data-baseweb="tab-highlight"],
.stTabs [data-baseweb="tab-border"] { display: none !important; }

/* ═══════════════════════════════════════════════
   VSTUPY (inputs, selects, textarea)
   ═══════════════════════════════════════════════ */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea textarea {
    border-radius: 8px !important;
    border: 1px solid var(--border) !important;
    font-size: 13.5px !important;
    transition: var(--transition) !important;
    padding: 6px 12px !important;
    color: #2d3748 !important;
    background: white !important;
}
/* Select/dropdown text */
div[data-baseweb="select"] span,
div[data-baseweb="select"] input {
    color: #2d3748 !important;
}
/* Checkbox labels */
.stCheckbox label span {
    color: #2d3748 !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stTextArea textarea:focus {
    border-color: var(--brand) !important;
    box-shadow: 0 0 0 3px rgba(231,76,60,0.1) !important;
    outline: none !important;
}
div[data-baseweb="select"] > div {
    border-radius: 8px !important;
    border-color: var(--border) !important;
    transition: var(--transition) !important;
}
div[data-baseweb="select"] > div:focus-within {
    border-color: var(--brand) !important;
    box-shadow: 0 0 0 3px rgba(231,76,60,0.1) !important;
}

/* ═══════════════════════════════════════════════
   ALERTY, DATAFRAMES, KONTEJNERY
   ═══════════════════════════════════════════════ */
div[data-testid="stAlert"] {
    border-radius: var(--radius) !important;
    border-left-width: 4px !important;
    font-size: 13.5px;
}
.stDataFrame > div {
    border-radius: var(--radius) !important;
    overflow: hidden;
    border: 1px solid var(--border) !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: var(--radius) !important;
    border-color: var(--warm-border) !important;
    background: var(--white) !important;
    box-shadow: var(--shadow-sm) !important;
    transition: var(--transition) !important;
}
div[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: var(--border) !important;
    box-shadow: var(--shadow-md) !important;
}
details {
    border-radius: 8px !important;
    border: 1px solid var(--border) !important;
    overflow: hidden;
}
details > summary {
    font-weight: 500 !important;
    font-size: 13.5px !important;
    padding: 10px 14px !important;
    cursor: pointer;
    transition: var(--transition) !important;
}
details > summary:hover {
    background: var(--surface) !important;
}
[data-testid="stDivider"] hr {
    border-color: var(--border) !important;
    margin: 8px 0 !important;
}
div[data-testid="stPopover"] {
    border-radius: var(--radius) !important;
}

/* ═══════════════════════════════════════════════
   SCROLLBAR (webkit)
   ═══════════════════════════════════════════════ */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: transparent; }
::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 3px;
}
::-webkit-scrollbar-thumb:hover { background: var(--muted); }

/* ═══════════════════════════════════════════════
   KOMPAKTNÍ ŘÁDKY — list škol
   ═══════════════════════════════════════════════ */
.school-row {
    display: flex;
    align-items: center;
    padding: 5px 8px;
    border-bottom: 1px solid #f1f5f9;
    transition: background 0.1s ease;
    gap: 6px;
}
.school-row:hover {
    background: #f8fafc;
}
.score-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 36px;
    height: 24px;
    border-radius: 5px;
    font-weight: 800;
    font-size: 12px;
    color: white;
    flex-shrink: 0;
    letter-spacing: -0.3px;
}

/* ═══════════════════════════════════════════════
   RESPONZIVNÍ — notebook vs desktop
   ═══════════════════════════════════════════════ */

/* Desktop XL (1920px+) — maximální prostor */
@media (min-width: 1800px) {
    :root { --sidebar-w: 260px; --content-max: 1700px; }
    .block-container {
        padding-left: 2.5rem !important;
        padding-right: 2.5rem !important;
    }
    [data-testid="stMetricValue"] { font-size: 32px !important; }
}

/* Desktop Full HD (1600-1799px) */
@media (min-width: 1600px) and (max-width: 1799px) {
    :root { --content-max: 1540px; }
    [data-testid="stMetricValue"] { font-size: 30px !important; }
}

/* Notebook HD+ (1440-1599px) */
@media (min-width: 1440px) and (max-width: 1599px) {
    :root { --sidebar-w: 235px; --content-max: 1380px; }
    .block-container {
        padding-left: 1.6rem !important;
        padding-right: 1.6rem !important;
    }
    [data-testid="stMetricValue"] { font-size: 27px !important; }
}

/* Notebook HD (1366-1439px) — nejčastější notebook */
@media (min-width: 1366px) and (max-width: 1439px) {
    :root { --sidebar-w: 230px; --content-max: 1280px; }
    .block-container {
        padding-left: 1.4rem !important;
        padding-right: 1.4rem !important;
    }
    [data-testid="stMetricValue"] { font-size: 24px !important; }
    [data-testid="stMetricLabel"] p { font-size: 10px !important; }
    [data-testid="metric-container"] { padding: 12px 14px 10px !important; }
    .stTabs [data-baseweb="tab"] {
        font-size: 12.5px !important;
        padding: 5px 11px !important;
    }
}

/* Pod 1366px */
@media (max-width: 1365px) {
    :root { --sidebar-w: 220px; --content-max: 1200px; }
    .block-container {
        padding-left: 1.2rem !important;
        padding-right: 1.2rem !important;
    }
    [data-testid="stMetricValue"] { font-size: 21px !important; }
    [data-testid="stMetricLabel"] p { font-size: 10px !important; }
    [data-testid="metric-container"] { padding: 10px 12px 8px !important; }
}
</style>
""", unsafe_allow_html=True)

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Vzdálenost dvou GPS bodů v kilometrech (Haversine)."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.asin(math.sqrt(a))


# Cesty k datům
DATA_DIR    = Path("data")
OUTPUT_DIR  = Path("output")
SCORED_CSV  = OUTPUT_DIR / "skoly_scored.csv"
VZ_CSV      = OUTPUT_DIR / "vz_alert_latest.csv"
CATALOG_JSON = DATA_DIR / "katalog.json"
NABIDKY_CSV  = DATA_DIR / "nabidky.csv"


# ─────────────────────────────────────────────────────────────
#  Načítání dat (cachované)
# ─────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_schools() -> pd.DataFrame:
    if not SCORED_CSV.exists():
        return pd.DataFrame()
    df = pd.read_csv(SCORED_CSV, dtype={"ico": str, "izo": str, "psc": str})
    return df


@st.cache_data(ttl=60)
def load_vz_alerts() -> pd.DataFrame:
    # Nejnovější vz_alert soubor
    files = sorted(OUTPUT_DIR.glob("vz_alert_*.csv"), reverse=True)
    if not files:
        return pd.DataFrame()
    return pd.read_csv(files[0], dtype={"platce_ico": str})


@st.cache_data(ttl=600)
def load_market_data() -> pd.DataFrame:
    cache = DATA_DIR / "market_smlouvy.csv"
    if cache.exists():
        return pd.read_csv(cache, dtype={"platce_ico": str, "dodavatel_ico": str})
    return pd.DataFrame()


@st.cache_data(ttl=300)
def load_crm() -> pd.DataFrame:
    try:
        from sheets.sheets_sync import get_crm_data
        return get_crm_data()
    except Exception:
        return pd.DataFrame()


@st.cache_data(ttl=3600)
def load_catalog() -> dict:
    """Načte katalog produktů z JSON."""
    if not CATALOG_JSON.exists():
        return {}
    with open(CATALOG_JSON, encoding="utf-8") as f:
        return json.load(f)


def load_quotes() -> pd.DataFrame:
    """Načte historii nabídek z CSV."""
    if not NABIDKY_CSV.exists():
        return pd.DataFrame(columns=[
            "cislo", "datum", "platnost_do", "skola_nazev", "skola_ico",
            "skola_email", "skola_obec", "polozky_json",
            "celkem_bez_dph", "dph", "celkem_s_dph",
            "sleva_pct", "stav", "poznamka",
        ])
    return pd.read_csv(NABIDKY_CSV, dtype=str)


def next_quote_number() -> str:
    """Vygeneruje číslo nabídky ve formátu NAB-YYYY-NNN."""
    rok = datetime.now().year
    df = load_quotes()
    if df.empty:
        return f"NAB-{rok}-001"
    # Filtruj čísla pro aktuální rok
    prefix = f"NAB-{rok}-"
    this_year = df[df["cislo"].str.startswith(prefix, na=False)]
    if this_year.empty:
        return f"{prefix}001"
    nums = this_year["cislo"].str.replace(prefix, "", regex=False).str.extract(r"(\d+)")[0].astype(int)
    return f"{prefix}{(nums.max() + 1):03d}"


def save_quote(record: dict):
    """Přidá nabídku do CSV."""
    NABIDKY_CSV.parent.mkdir(exist_ok=True)
    df = load_quotes()
    new_row = pd.DataFrame([record])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_csv(NABIDKY_CSV, index=False, encoding="utf-8-sig")


def generate_quote_html(cislo: str, skola: dict, polozky: list,
                         sleva_pct: float, platnost_dni: int,
                         poznamka: str = "") -> str:
    """
    Generuje tisknutelnou HTML nabídku.
    skola: dict s klíči nazev, obec, ico, email
    polozky: list of dict {id, nazev, popis, mnozstvi, cena_kus, cena_radek}
    """
    dnes = datetime.now().strftime("%d. %m. %Y")
    platnost = (datetime.now() + timedelta(days=platnost_dni)).strftime("%d. %m. %Y")
    dph_sazba = 21

    celkem_bez = sum(p["cena_radek"] for p in polozky)
    sleva_czk  = celkem_bez * sleva_pct / 100
    zaklad_dph = celkem_bez - sleva_czk
    dph_czk    = zaklad_dph * dph_sazba / 100
    celkem_s   = zaklad_dph + dph_czk

    rows_html = ""
    for i, p in enumerate(polozky, 1):
        rows_html += f"""
        <tr>
          <td class="num">{i}</td>
          <td><b>{p['nazev']}</b><br><small style="color:#666">{p.get('popis','')}</small></td>
          <td class="num">{p['mnozstvi']}&nbsp;{p.get('jednotka','ks')}</td>
          <td class="num">{p['cena_kus']:,.0f}&nbsp;Kč</td>
          <td class="num"><b>{p['cena_radek']:,.0f}&nbsp;Kč</b></td>
        </tr>"""

    sleva_row = ""
    if sleva_pct > 0:
        sleva_row = f"""
        <tr class="sleva-row">
          <td colspan="4" style="text-align:right;padding-right:10px;"><i>Sleva {sleva_pct:.0f} %</i></td>
          <td class="num"><i>−{sleva_czk:,.0f}&nbsp;Kč</i></td>
        </tr>"""

    poznamka_html = f'<p style="margin-top:20px;color:#555;font-size:13px;"><b>Poznámka:</b> {poznamka}</p>' if poznamka else ""

    return f"""<!DOCTYPE html>
<html lang="cs">
<head>
<meta charset="UTF-8">
<title>Nabídka {cislo}</title>
<style>
  * {{ box-sizing:border-box; margin:0; padding:0; }}
  body {{ font-family: Arial, sans-serif; font-size: 13px; color: #222; padding: 30px 40px; max-width: 900px; margin: auto; }}
  h1 {{ font-size: 22px; color: #e74c3c; margin-bottom: 4px; }}
  .meta {{ color: #555; font-size: 12px; margin-bottom: 20px; }}
  .header-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 24px; }}
  .box {{ border: 1px solid #ddd; border-radius: 6px; padding: 12px 16px; }}
  .box h3 {{ font-size: 11px; text-transform: uppercase; color: #999; margin-bottom: 8px; letter-spacing: 1px; }}
  .box p {{ line-height: 1.6; }}
  table {{ width: 100%; border-collapse: collapse; margin-top: 16px; }}
  th {{ background: #2c3e50; color: white; padding: 8px 10px; text-align: left; font-size: 12px; }}
  td {{ padding: 7px 10px; border-bottom: 1px solid #eee; vertical-align: top; }}
  tr:nth-child(even) td {{ background: #fafafa; }}
  .num {{ text-align: right; white-space: nowrap; }}
  .sleva-row td {{ background: #fff8e1 !important; }}
  .totals {{ margin-top: 16px; display: flex; justify-content: flex-end; }}
  .totals table {{ width: auto; min-width: 280px; }}
  .totals td {{ border: none; padding: 4px 10px; }}
  .totals .label {{ color: #555; }}
  .totals .big {{ font-size: 16px; font-weight: bold; color: #e74c3c; }}
  .footer {{ margin-top: 32px; font-size: 11px; color: #999; border-top: 1px solid #eee; padding-top: 12px; }}
  .badge {{ display: inline-block; background: #e74c3c; color: white; padding: 3px 12px; border-radius: 4px; font-size: 12px; font-weight: bold; margin-bottom: 6px; }}
  @media print {{
    body {{ padding: 10px; }}
    .no-print {{ display: none; }}
  }}
</style>
</head>
<body>
<div class="badge">CENOVÁ NABÍDKA</div>
<h1>Brezka — zakázková výroba školního nábytku</h1>
<p class="meta">📍 Nupaky, Praha-východ &nbsp;|&nbsp; Matyas Olmr &nbsp;|&nbsp; IČO: 12345678</p>

<div class="header-grid">
  <div class="box">
    <h3>Dodavatel</h3>
    <p><b>Brezka</b><br>Matyas Olmr<br>Nupaky, Praha-východ<br>IČO: 12345678<br>✉ matyas@brezka.cz</p>
  </div>
  <div class="box">
    <h3>Odběratel</h3>
    <p><b>{skola.get('nazev','—')}</b><br>
    {skola.get('obec','')}<br>
    {"IČO: " + skola.get('ico','') if skola.get('ico') else ''}<br>
    {"✉ " + skola.get('email','') if skola.get('email') else ''}
    </p>
  </div>
</div>

<table style="width:100%;border:none;border-collapse:collapse;margin-bottom:12px;">
<tr>
  <td style="border:none;"><b>Číslo nabídky:</b> {cislo}</td>
  <td style="border:none;"><b>Datum:</b> {dnes}</td>
  <td style="border:none;"><b>Platnost do:</b> {platnost}</td>
</tr>
</table>

<table>
  <thead>
    <tr>
      <th style="width:30px">#</th>
      <th>Popis</th>
      <th class="num">Množství</th>
      <th class="num">Cena/ks bez DPH</th>
      <th class="num">Celkem bez DPH</th>
    </tr>
  </thead>
  <tbody>
    {rows_html}
    {sleva_row}
  </tbody>
</table>

<div class="totals">
  <table>
    <tr><td class="label">Základ DPH:</td><td class="num">{zaklad_dph:,.0f}&nbsp;Kč</td></tr>
    <tr><td class="label">DPH {dph_sazba} %:</td><td class="num">{dph_czk:,.0f}&nbsp;Kč</td></tr>
    <tr style="border-top:2px solid #e74c3c;">
      <td class="label big">CELKEM K ÚHRADĚ:</td>
      <td class="num big">{celkem_s:,.0f}&nbsp;Kč</td>
    </tr>
  </table>
</div>

{poznamka_html}

<div class="footer">
  <p>Nabídka je platná do {platnost}. Ceny jsou uvedeny bez DPH ({dph_sazba} %).
  Dodací lhůta bude upřesněna po přijetí objednávky. Doprava a montáž dle dohody.
  Veškeré produkty jsou vyráběny zakázkově dle požadavků zákazníka.</p>
</div>

<p class="no-print" style="margin-top:24px;text-align:center;color:#999;font-size:11px;">
  Tisk: Ctrl+P &nbsp;|&nbsp; Uložit jako PDF: V dialogu tisku zvol "Uložit jako PDF"
</p>
</body>
</html>"""


def short_signal(u: dict) -> str:
    """Krátký signál pro kompaktní řádkové zobrazení (max ~15 znaků)."""
    sig = u.get("signal", "")
    reasons = u.get("reasons", "")
    if "Dotace" in sig:
        import re
        m = re.search(r"\d{4}", sig)
        return f"💰 dot. {m.group()}" if m else "💰 dotace"
    if "extrémně přezrálé" in sig:
        import re
        m = re.search(r"(\d+) let", sig)
        return f"🔴 {m.group()} starý" if m else "🔴 přezrálé"
    if "přezrálé" in sig:
        import re
        m = re.search(r"(\d+) let", sig)
        return f"🟡 {m.group()}" if m else "🟡 přezrálé"
    if "blíží" in sig:
        import re
        m = re.search(r"(\d+) let", sig)
        return f"⏳ {m.group()}" if m else "⏳ blíží se"
    if "poptávka" in sig.lower():
        return "🟢 poptávka"
    if "Cluster" in sig or "cluster" in reasons:
        return "🏘️ cluster"
    if "Vrchol sezóny" in sig:
        return "📅 sezóna"
    return "📋 std"


def page_header(title: str, subtitle: str = "", accent: str = "#e74c3c"):
    """Stylovaný nadpis stránky s akcentní linkou."""
    sub_html = (
        f'<p style="margin:6px 0 0 0;color:#718096;font-size:14px;font-weight:400;'
        f'line-height:1.5;">{subtitle}</p>'
        if subtitle else ""
    )
    st.markdown(
        f'<div style="margin-bottom:1.6rem;padding-bottom:1rem;'
        f'border-bottom:1px solid #ece8e1;">'
        f'<h1 style="margin:0;font-size:24px;font-weight:800;color:#1a1a2e;'
        f'letter-spacing:-0.4px;">{title}</h1>'
        f'{sub_html}'
        f'<div style="width:48px;height:3px;background:linear-gradient(90deg,{accent},transparent);'
        f'border-radius:2px;margin-top:10px;"></div>'
        f'</div>',
        unsafe_allow_html=True,
    )


def stat_card(label: str, value: str, delta: str = "", color: str = "#1a1a2e") -> str:
    """HTML karta pro vlastní metriku — vrátí HTML string."""
    delta_html = (
        f'<div style="font-size:11px;color:#718096;margin-top:3px;">{delta}</div>'
        if delta else ""
    )
    return (
        f'<div style="background:white;border:1px solid #ece8e1;border-radius:12px;'
        f'padding:16px 20px;box-shadow:0 1px 3px rgba(0,0,0,0.04),0 1px 2px rgba(0,0,0,0.03);'
        f'transition:all 0.2s ease;">'
        f'<div style="font-size:10.5px;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:0.7px;color:#718096;">{label}</div>'
        f'<div style="font-size:28px;font-weight:800;color:{color};margin-top:5px;'
        f'letter-spacing:-0.5px;">{value}</div>'
        f'{delta_html}'
        f'</div>'
    )


def get_contacted_set() -> set:
    crm = load_crm()
    if crm.empty or "ID_školy" not in crm.columns:
        return set()
    return set(crm["ID_školy"].astype(str).tolist())


# ─────────────────────────────────────────────────────────────
#  Email helper
# ─────────────────────────────────────────────────────────────
EMAIL_TEMPLATES = {
    "recent_purchase": {
        "label": "Koupili nedávno nábytek",
        "subject": "Školní nábytek na míru — Brezka, Nupaky",
        "body": """Dobrý den,

zjistil jsem, že vaše škola nedávno pořizovala školní nábytek.

Rád bych Vám představil firmu Brezka z Nupaků — specializujeme se na zakázkovou výrobu školního nábytku přímo na míru (lavice, stoly, skříně, šatní skříňky, vybavení učeben).

Pracujeme přímo s ředitelstvím škol formou poptávkového řízení — bez zbytečné byrokracie.

Mohl/a bych Vám zaslat cenovou nabídku nebo se s Vámi krátce setkat?

S pozdravem,
Matyas Olmr
Brezka — zakázková výroba školního nábytku
📍 Nupaky, Praha-východ
""",
    },
    "priority_a": {
        "label": "Priority A — obecný kontakt",
        "subject": "Školní nábytek na míru — Brezka",
        "body": """Dobrý den,

obracím se na Vás s nabídkou zakázkové výroby školního nábytku.

Firma Brezka z Nupaků (Praha-východ) vyrábí nábytek přímo pro školy — lavice, stoly, skříně a další vybavení učeben a chodeb, vše na míru a za přímé ceny (bez mezičlánků).

Rádi bychom Vám zaslali cenovou nabídku nebo se s Vámi setkali.

S pozdravem,
Matyas Olmr
Brezka — zakázková výroba školního nábytku
📍 Nupaky, Praha-východ
""",
    },
    "dotace_signal": {
        "label": "Dostali dotaci — chystají nákup",
        "subject": "Školní nábytek z dotace — Brezka",
        "body": """Dobrý den,

obrátil jsem se na Vás v souvislosti s dotací, kterou vaše škola získala na modernizaci.

Firma Brezka z Nupaků se specializuje na zakázkovou výrobu školního nábytku a rádi bychom Vám pomohli s čerpáním dotace prostřednictvím nákupu kvalitního nábytku na míru.

Nabízíme: lavice, stoly, skříně, vybavení učeben — vše dle vašich potřeb a specifikací.

Máte zájem o cenovou nabídku?

S pozdravem,
Matyas Olmr
Brezka — zakázková výroba školního nábytku
📍 Nupaky, Praha-východ
""",
    },
    "vz_overdue": {
        "label": "Přezrálá VZ (5+ let)",
        "subject": "Obnova školního nábytku — Brezka",
        "body": """Dobrý den,

oslovuji Vás s nabídkou obnovy školního nábytku.

Zaznamenal jsem, že vaše škola již delší dobu neobnovovala vybavení učeben. Firma Brezka z Nupaků vyrábí školní nábytek na zakázku a rádi bychom Vám připravili nabídku odpovídající Vašim potřebám a rozpočtu.

Pracujeme formou přímého poptávkového řízení — rychle, bez komplikací.

Mohu zaslat katalog nebo se s Vámi krátce setkat?

S pozdravem,
Matyas Olmr
Brezka — zakázková výroba školního nábytku
📍 Nupaky, Praha-východ
""",
    },
}


def make_mailto(email: str, subject: str, body: str) -> str:
    """Vytvoří mailto: link s předvyplněným předmětem a textem."""
    subject_enc = urllib.parse.quote(subject)
    body_enc    = urllib.parse.quote(body)
    return f"mailto:{email}?subject={subject_enc}&body={body_enc}"


def get_email_template(row: pd.Series) -> str:
    """Vybere vhodný email template dle signálů školy."""
    if row.get("dotace_had") == "ANO" or row.get("dotace_had") is True:
        years_since = datetime.now().year - int(row.get("dotace_last_year") or 0)
        if 1 <= years_since <= 4:
            return "dotace_signal"

    had_vz = row.get("had_vz_nabytek") == "ANO" or row.get("had_vz_nabytek") is True
    last_vz_year = row.get("last_vz_year")
    if had_vz and last_vz_year and (datetime.now().year - int(last_vz_year)) >= 5:
        return "vz_overdue"

    return "priority_a"


def compute_urgency(row: pd.Series, current_year: int = None,
                    current_month: int = None,
                    recent_obce: set = None) -> dict:
    """
    Urgency score 0–100. Faktory:
      💰 Dotace timing (+40b) · 📅 Sezóna (+20b) · 🔴 VZ gap (+35b)
      📍 Vzdálenost od dílny (+15b) · 🏘️ Cluster efekt (+10b)
      🏫 Velikost (+20b) · 🌍 Region (+5b)
      ⛔ Disqualifier: koupili < 2 roky → skóre 0
    """
    if current_year is None:
        current_year = datetime.now().year
    if current_month is None:
        current_month = datetime.now().month

    score = 0
    signals = []
    reasons = []

    had_dotace   = row.get("dotace_had") in ("ANO", True, "True", 1)
    dotace_year  = row.get("dotace_last_year")
    had_vz       = row.get("had_vz_nabytek") in ("ANO", True, "True", 1)
    last_vz_year = row.get("last_vz_year")
    zaci         = int(float(row.get("pocet_zaku", 0) or 0))
    kraj         = str(row.get("kraj", ""))
    obec         = str(row.get("obec", "") or "")
    lat          = row.get("lat")
    lon          = row.get("lon")

    # ── DISQUALIFIER ─────────────────────────────────────────
    if had_vz and last_vz_year:
        try:
            gap = current_year - int(float(last_vz_year))
            if gap < 2:
                return {
                    "urgency_score": 0,
                    "kategorie": "pockat",
                    "kategorie_label": "⚫ Počkat",
                    "signal": f"Koupili r. {int(last_vz_year)} — příliš brzy ({gap}r)",
                    "reasons": "",
                    "barva": "#94a3b8",
                }
        except (ValueError, TypeError):
            pass

    # ── 💰 DOTACE (max 40b) ──────────────────────────────────
    if had_dotace and dotace_year:
        try:
            ya = current_year - int(float(dotace_year))
            if ya == 1:
                score += 35
                signals.append(f"💰 Dotace {int(dotace_year)} — právě čerpají")
                reasons.append(f"+35b: dotace {int(dotace_year)} (loni)")
            elif ya == 2:
                score += 40
                signals.append(f"💰 Dotace {int(dotace_year)} — PŘIPRAVUJÍ NÁKUP")
                reasons.append(f"+40b: dotace {int(dotace_year)} (2 roky = ideál)")
            elif ya == 3:
                score += 30
                signals.append(f"💰 Dotace {int(dotace_year)} — poslední šance")
                reasons.append(f"+30b: dotace {int(dotace_year)} (3 roky)")
            elif ya == 4:
                score += 15
                reasons.append(f"+15b: dotace {int(dotace_year)} (4 roky, slabší)")
        except (ValueError, TypeError):
            pass

    # ── 🔴 VZ GAP (max 35b) ──────────────────────────────────
    if had_vz and last_vz_year:
        try:
            gap = current_year - int(float(last_vz_year))
            if gap >= 8:
                score += 35
                signals.append(f"🔴 Nábytek z r. {int(last_vz_year)} — {gap} let starý")
                reasons.append(f"+35b: přezrálé {gap} let")
            elif gap >= 6:
                score += 25
                signals.append(f"🟡 Nábytek {gap} let starý")
                reasons.append(f"+25b: přezrálé {gap} let")
            elif gap >= 4:
                score += 15
                signals.append(f"🟡 Obnova se blíží ({gap} let)")
                reasons.append(f"+15b: gap {gap} let")
            elif gap >= 2:
                score += 5
                reasons.append(f"+5b: gap {gap} let")
        except (ValueError, TypeError):
            pass
    elif not had_vz:
        score += 20
        signals.append("🟢 Bez VZ — nakupuje přes poptávku")
        reasons.append("+20b: bez VZ = přímá poptávka")

    # ── 📅 SEZÓNNOST (max 20b) ────────────────────────────────
    _season_pts = {1: 10, 2: 15, 3: 20, 4: 20, 5: 18, 6: 12,
                   7:  5, 8:  5, 9:  8, 10: 8, 11:  6, 12:  5}
    _sb = _season_pts.get(current_month, 5)
    score += _sb
    if _sb >= 18:
        signals.append("📅 Vrchol sezóny — ideální čas")
        reasons.append(f"+{_sb}b: vrchol sezóny (měsíc {current_month})")
    elif _sb >= 12:
        reasons.append(f"+{_sb}b: dobrá sezóna")
    else:
        reasons.append(f"+{_sb}b: mimo sezónu")

    # ── 📍 VZDÁLENOST od dílny (max 15b) ─────────────────────
    try:
        if lat is not None and lon is not None and not pd.isna(lat) and not pd.isna(lon):
            _dist = haversine_km(WORKSHOP["lat"], WORKSHOP["lon"],
                                  float(lat), float(lon))
            if _dist <= 30:
                score += 15
                signals.append(f"📍 {_dist:.0f} km od dílny")
                reasons.append(f"+15b: {_dist:.0f} km (blízko)")
            elif _dist <= 60:
                score += 8
                reasons.append(f"+8b: {_dist:.0f} km")
            elif _dist <= 100:
                score += 3
                reasons.append(f"+3b: {_dist:.0f} km")
    except (ValueError, TypeError):
        pass

    # ── 🏘️ CLUSTER EFEKT (max 10b) ───────────────────────────
    if recent_obce and obec:
        if obec.strip().lower() in {o.strip().lower() for o in recent_obce}:
            score += 10
            signals.append("🏘️ Sousední škola koupila nedávno")
            reasons.append("+10b: cluster efekt")

    # ── 🏫 VELIKOST (max 20b) ────────────────────────────────
    if zaci >= 700:
        score += 20
        signals.append(f"🏫 {zaci} žáků")
        reasons.append(f"+20b: {zaci} žáků")
    elif zaci >= 500:
        score += 16
        reasons.append(f"+16b: {zaci} žáků")
    elif zaci >= 300:
        score += 10
        reasons.append(f"+10b: {zaci} žáků")
    elif zaci >= 150:
        score += 5
        reasons.append(f"+5b: {zaci} žáků")

    # ── 🌍 REGION (max 5b) ───────────────────────────────────
    if "Praha" in kraj or "Středočeský" in kraj:
        score += 5
        reasons.append("+5b: prioritní kraj")
    elif "Jihočeský" in kraj:
        score += 3
        reasons.append("+3b: blízký kraj")

    score = min(score, 100)

    if score >= 60:
        kategorie, label, barva = "ted",      "🔴 Teď",    "#e74c3c"
    elif score >= 35:
        kategorie, label, barva = "brzy",     "🟡 Brzy",   "#f39c12"
    elif score >= 15:
        kategorie, label, barva = "pripravit","🟢 Připravit","#27ae60"
    else:
        kategorie, label, barva = "nizka",    "⚫ Nízká",  "#94a3b8"

    return {
        "urgency_score":   score,
        "kategorie":       kategorie,
        "kategorie_label": label,
        "signal":          " · ".join(signals) if signals else "Standardní kontakt",
        "reasons":         " | ".join(reasons),
        "barva":           barva,
    }


def get_signal_text(row: pd.Series) -> str:
    """Zpětná kompatibilita — vrátí signal text z urgency dict."""
    u = compute_urgency(row)
    return u["signal"]


# ─────────────────────────────────────────────────────────────
#  Mapa helper
# ─────────────────────────────────────────────────────────────
PRIORITY_COLORS = {"A": "#e74c3c", "B": "#f39c12", "C": "#95a5a6"}


def build_filtered_map(filtered_df: pd.DataFrame, show_heatmap: bool = False,
                       competitors_df: pd.DataFrame = None) -> folium.Map:
    m = folium.Map(
        location=[WORKSHOP["lat"], WORKSHOP["lon"]],
        zoom_start=8,
        tiles="CartoDB positron",
    )

    # Dílna
    folium.Marker(
        location=[WORKSHOP["lat"], WORKSHOP["lon"]],
        popup="🔨 Dílna Brezka — Nupaky",
        icon=folium.Icon(color="darkblue", icon="home", prefix="fa"),
        tooltip="Dílna Nupaky",
    ).add_to(m)

    # Školy
    schools_with_coords = filtered_df.dropna(subset=["lat", "lon"])
    for _, row in schools_with_coords.iterrows():
        priority = str(row.get("priorita", "C"))
        color    = PRIORITY_COLORS.get(priority, "#95a5a6")
        zaci     = int(row.get("pocet_zaku", 100) or 100)
        radius   = 5 if zaci < 100 else 7 if zaci < 300 else 10 if zaci < 600 else 14

        email = str(row.get("email", "") or "")
        email_link = f'<a href="mailto:{email}">{email}</a>' if email and email != "nan" else "—"

        popup_html = f"""
        <div style="font-family:Arial;min-width:220px;">
            <b style="font-size:13px;">{row.get('nazev','')}</b><br>
            <span style="color:#666;">{row.get('obec','')} · {row.get('kraj','')}</span><br>
            <hr style="margin:5px 0;">
            <b>Skóre:</b> {row.get('score_total','')} — Priorita <b style="color:{color};">{priority}</b><br>
            <b>Žáků:</b> {zaci}<br>
            <b>Přístup:</b> {row.get('pristup_label', row.get('pristup',''))}<br>
            <b>Email:</b> {email_link}<br>
            <hr style="margin:5px 0;">
            <a href="https://www.google.com/maps/dir/{WORKSHOP['lat']},{WORKSHOP['lon']}/{row.get('lat','')},{row.get('lon','')}"
               target="_blank">🗺️ Trasa z dílny</a>
        </div>
        """
        folium.CircleMarker(
            location=[row["lat"], row["lon"]],
            radius=radius,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"{row.get('nazev','')} ({zaci} žáků)",
        ).add_to(m)

    # Heatmapa konkurence
    if show_heatmap and competitors_df is not None and not competitors_df.empty:
        heat_data = competitors_df.dropna(subset=["lat","lon"])[["lat","lon"]].values.tolist()
        if heat_data:
            HeatMap(heat_data, radius=25, blur=20,
                    gradient={0.2:"blue",0.5:"lime",0.8:"yellow",1.0:"red"}).add_to(m)

    return m


# ─────────────────────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────────────────────
with st.sidebar:
    # ── Branding ──────────────────────────────────────────────
    st.markdown("""
    <div style="text-align:center;padding:16px 0 22px 0;">
        <div style="font-size:36px;line-height:1;filter:drop-shadow(0 2px 4px rgba(0,0,0,0.2));">
            🔨</div>
        <div style="font-size:18px;font-weight:800;color:#f1f5f9;
                    letter-spacing:-0.3px;margin-top:10px;">Brezka CRM</div>
        <div style="font-size:10px;color:#718096;margin-top:4px;
                    text-transform:uppercase;letter-spacing:1.2px;font-weight:500;">
            Školní nábytek · Nupaky
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    nav = st.radio(
        "Navigace",
        ["📋 Oslovování", "🏠 Přehled", "🎯 Akce dnes", "📡 Market Intel",
         "🗺️ Mapa", "📋 VZ Monitor",
         "📊 Analytika", "👥 CRM Pipeline", "📄 Nabídky"],
        label_visibility="collapsed",
    )

    st.divider()

    # ── Quick stats ───────────────────────────────────────────
    schools_df = load_schools()
    vz_df      = load_vz_alerts()

    if not schools_df.empty:
        a_count = int((schools_df["priorita"] == "A").sum()) if "priorita" in schools_df.columns else 0
        b_count = int((schools_df["priorita"] == "B").sum()) if "priorita" in schools_df.columns else 0
        total   = len(schools_df)

        col1, col2 = st.columns(2)
        col1.metric("Priorita A", a_count)
        col2.metric("Priorita B", b_count)
        st.metric("Škol celkem", total)

    if not vz_df.empty:
        skoly_count = int(vz_df["je_skola"].sum()) if "je_skola" in vz_df.columns else 0
        st.metric("Nové smlouvy", skoly_count)

    # Open quotes
    q_df = load_quotes()
    if not q_df.empty and "stav" in q_df.columns:
        open_q = (q_df["stav"].isin(["Připravena", "Odesláno", "Reakce"])).sum()
        if open_q:
            st.metric("Otevřené nabídky", int(open_q))

    st.divider()

    # ── Footer ────────────────────────────────────────────────
    dnes = datetime.now().strftime("%d.%m.%Y")
    data_date = "—"
    if SCORED_CSV.exists():
        data_date = datetime.fromtimestamp(SCORED_CSV.stat().st_mtime).strftime("%d.%m.")

    st.markdown(
        f'<div style="font-size:11px;color:#334155;text-align:center;'
        f'padding:4px 0;line-height:1.8;">'
        f'📅 {dnes}<br>🗄️ Data: {data_date}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ─────────────────────────────────────────────────────────────
#  STRÁNKY
# ─────────────────────────────────────────────────────────────

# ══════════════════════════════════════════════════════════════
#  📋 OSLOVOVÁNÍ — týmový outreach
# ══════════════════════════════════════════════════════════════
if nav == "📋 Oslovování":

    # ── Konfigurace týmu ─────────────────────────────────────
    if "team_members" not in st.session_state:
        st.session_state["team_members"] = ["Matyáš", "Lukáš", "Jiřina"]
    if "outreach_log" not in st.session_state:
        st.session_state["outreach_log"] = []  # list of {izo, person, date, typ}

    TEAM = st.session_state["team_members"]
    _olog = st.session_state["outreach_log"]

    today = datetime.now().date()
    week_start = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    # ── Počty per osoba ──────────────────────────────────────
    def _count_by(person, since):
        return sum(1 for o in _olog if o["person"] == person
                   and datetime.strptime(o["date"], "%Y-%m-%d").date() >= since)

    page_header("📋 Týmové oslovování",
                "Přiřaď školu → pošli email → označ jako osloveno")

    # ── Dashboard — tabulka s rozpadem stavů ────────────────
    _STAVY_DASH = [
        ("Osloveno",         "🔵", "#3b82f6"),
        ("Jednáme",          "🟡", "#f59e0b"),
        ("Nabídka",          "🟣", "#8b5cf6"),
        ("Ozvat se později", "⏳", "#64748b"),
        ("Nemají zájem",     "🔴", "#ef4444"),
        ("Vyhráno 🎉",       "🏆", "#22c55e"),
    ]

    # Header
    _th = ''.join(
        f'<th style="font-size:10px;font-weight:700;color:#a0aec0;text-transform:uppercase;'
        f'letter-spacing:0.4px;padding:6px 8px;text-align:center;white-space:nowrap;"'
        f' title="{s}">{icon}</th>'
        for s, icon, _ in _STAVY_DASH
    )
    # Rows
    _tbody = ""
    for _tn in TEAM:
        _person_log = [o for o in _olog if o["person"] == _tn]
        _cnt_today = _count_by(_tn, today)
        _cnt_week = _count_by(_tn, week_start)
        _cnt_total = len(_person_log)
        _today_clr = "#22c55e" if _cnt_today >= 5 else "#f59e0b" if _cnt_today >= 1 else "#94a3b8"

        # Stav counts
        _stav_cells = ""
        for _sn, _si, _sc in _STAVY_DASH:
            _sc_cnt = sum(1 for o in _person_log if o.get("stav", "Osloveno") == _sn)
            _sc_txt = f'<span style="color:{_sc};font-weight:700;">{_sc_cnt}</span>' if _sc_cnt else '<span style="color:#e2e8f0;">0</span>'
            _stav_cells += f'<td style="text-align:center;padding:8px 6px;font-size:13px;">{_sc_txt}</td>'

        _tbody += f"""
        <tr style="border-bottom:1px solid #f1ede8;">
            <td style="padding:10px 14px;font-size:14px;font-weight:700;color:#1a1a2e;
                white-space:nowrap;">{_tn}</td>
            <td style="text-align:center;padding:8px 10px;">
                <span style="font-size:20px;font-weight:800;color:{_today_clr};">{_cnt_today}</span>
                <span style="font-size:10px;color:#a0aec0;margin-left:2px;">dnes</span>
            </td>
            <td style="text-align:center;padding:8px 10px;font-size:13px;color:#2d3748;font-weight:600;">
                {_cnt_week}</td>
            <td style="text-align:center;padding:8px 10px;font-size:13px;color:#718096;">
                {_cnt_total}</td>
            {_stav_cells}
        </tr>"""

    st.markdown(
        f'<div style="background:white;border:1px solid #ece8e1;border-radius:12px;'
        f'box-shadow:0 1px 3px rgba(0,0,0,0.04);overflow:hidden;margin-bottom:16px;">'
        f'<table style="width:100%;border-collapse:collapse;">'
        f'<thead><tr style="border-bottom:2px solid #ece8e1;">'
        f'<th style="text-align:left;padding:10px 14px;font-size:10px;font-weight:700;'
        f'color:#a0aec0;text-transform:uppercase;letter-spacing:0.5px;">Člen</th>'
        f'<th style="text-align:center;padding:6px 8px;font-size:10px;font-weight:700;'
        f'color:#a0aec0;text-transform:uppercase;letter-spacing:0.4px;">Dnes</th>'
        f'<th style="text-align:center;padding:6px 8px;font-size:10px;font-weight:700;'
        f'color:#a0aec0;text-transform:uppercase;letter-spacing:0.4px;">Týden</th>'
        f'<th style="text-align:center;padding:6px 8px;font-size:10px;font-weight:700;'
        f'color:#a0aec0;text-transform:uppercase;letter-spacing:0.4px;">Celkem</th>'
        f'{_th}'
        f'</tr></thead>'
        f'<tbody>{_tbody}</tbody>'
        f'</table></div>',
        unsafe_allow_html=True)

    # ── Správa týmu ──────────────────────────────────────────
    with st.expander("⚙️ Správa týmu"):
        _new_member = st.text_input("Přidat člena", placeholder="Jméno...")
        if st.button("➕ Přidat", key="add_member") and _new_member.strip():
            if _new_member.strip() not in TEAM:
                st.session_state["team_members"].append(_new_member.strip())
                st.rerun()
        if len(TEAM) > 1:
            _del = st.selectbox("Odebrat člena", ["—"] + TEAM)
            if st.button("🗑️ Odebrat", key="del_member") and _del != "—":
                st.session_state["team_members"].remove(_del)
                st.rerun()

    st.divider()

    # ── Filtry ───────────────────────────────────────────────
    if schools_df.empty:
        st.error("Data škol nenalezena. Spusť: `python main.py`")
        st.stop()

    _oslovene_izo = {o["izo"] for o in _olog}

    _f1, _f2, _f3, _f4, _f5, _f6 = st.columns([2.2, 1.1, 0.9, 1.0, 1.0, 0.6])
    with _f1:
        _os_search = st.text_input("🔍", placeholder="Název školy, obec, IČO...",
                                    label_visibility="collapsed", key="os_search")
    with _f2:
        _kraje = sorted(schools_df["kraj"].dropna().unique().tolist())
        _os_kraj = st.selectbox("Kraj", ["Vše"] + _kraje,
                                 label_visibility="collapsed", key="os_kraj")
    with _f3:
        _os_size = st.selectbox("Velikost", ["Vše", "500+", "300–500", "100–300", "Pod 100"],
                                 label_visibility="collapsed", key="os_size")
    with _f4:
        _os_status = st.selectbox("Kontakt", ["Neoslovené", "Vše", "Oslovené"],
                                   label_visibility="collapsed", key="os_status")
    with _f5:
        _os_stav = st.selectbox("Stav", ["Vše", "Osloveno", "Jednáme", "Nabídka",
                                          "Ozvat se později", "Nemají zájem", "Vyhráno 🎉"],
                                 label_visibility="collapsed", key="os_stav")
    with _f6:
        _os_limit = st.selectbox("Řádků", [50, 100, 200, 500],
                                  label_visibility="collapsed", key="os_limit")

    # Filtrování
    _tbl = schools_df.copy()
    if _os_search:
        _sq = _os_search.lower()
        _tbl = _tbl[
            _tbl["nazev"].str.lower().str.contains(_sq, na=False) |
            _tbl["obec"].str.lower().str.contains(_sq, na=False) |
            _tbl["ico"].astype(str).str.contains(_sq, na=False)
        ]
    if _os_kraj != "Vše":
        _tbl = _tbl[_tbl["kraj"] == _os_kraj]
    if _os_size == "500+":
        _tbl = _tbl[pd.to_numeric(_tbl["pocet_zaku"], errors="coerce") >= 500]
    elif _os_size == "300–500":
        _zk = pd.to_numeric(_tbl["pocet_zaku"], errors="coerce")
        _tbl = _tbl[(_zk >= 300) & (_zk < 500)]
    elif _os_size == "100–300":
        _zk = pd.to_numeric(_tbl["pocet_zaku"], errors="coerce")
        _tbl = _tbl[(_zk >= 100) & (_zk < 300)]
    elif _os_size == "Pod 100":
        _tbl = _tbl[pd.to_numeric(_tbl["pocet_zaku"], errors="coerce") < 100]

    if _os_status == "Neoslovené":
        _tbl = _tbl[~_tbl["izo"].astype(str).isin(_oslovene_izo)]
    elif _os_status == "Oslovené":
        _tbl = _tbl[_tbl["izo"].astype(str).isin(_oslovene_izo)]

    # Filtr dle stavu (jen pro oslovené)
    if _os_stav != "Vše":
        _stav_izo = {o["izo"] for o in _olog if o.get("stav") == _os_stav}
        _tbl = _tbl[_tbl["izo"].astype(str).isin(_stav_izo)]

    _tbl = _tbl.head(_os_limit)

    st.caption(f"Zobrazuji {len(_tbl)} škol"
               + (f" · \"{_os_search}\"" if _os_search else ""))

    # ── Header tabulky ───────────────────────────────────────
    st.markdown(
        '<div style="display:grid;'
        'grid-template-columns:1fr 120px 80px 50px 50px 50px 50px 160px;'
        'gap:4px;padding:6px 10px;background:white;border:1px solid #ece8e1;'
        'border-radius:12px 12px 0 0;border-bottom:2px solid #ece8e1;'
        'font-size:10px;font-weight:700;color:#a0aec0;text-transform:uppercase;'
        'letter-spacing:0.7px;">'
        '<div>Škola</div><div>Obec</div><div>Žáků</div>'
        '<div>🌐</div><div>📧</div><div>📞</div><div>👤</div>'
        '<div>Přiřadit → ✓</div>'
        '</div>',
        unsafe_allow_html=True)

    # ── Řádky tabulky ────────────────────────────────────────
    for _ri, (_, _rr) in enumerate(_tbl.iterrows()):
        _izo = str(_rr.get("izo", ""))
        _is_done = _izo in _oslovene_izo
        _done_by = next((o["person"] for o in reversed(_olog) if o["izo"] == _izo), None)

        _nazev = str(_rr.get("nazev", ""))
        _obec = str(_rr.get("obec", ""))
        _zaci = int(float(_rr.get("pocet_zaku", 0) or 0))
        _email = str(_rr.get("email", "") or "")
        _web = str(_rr.get("web", "") or "")
        _tel = str(_rr.get("telefon", "") or "")
        _reditel = str(_rr.get("reditel", "") or "")
        _ico = str(_rr.get("ico", "") or "")

        # Barva řádku
        _row_bg = "#f0fdf4" if _is_done else ("white" if _ri % 2 == 0 else "#faf9f7")

        _rc = st.columns([3.5, 1.2, 0.7, 0.4, 0.4, 0.4, 0.4, 1.6])

        with _rc[0]:
            _status_dot = f'<span style="color:#22c55e;font-size:8px;">●</span> ' if _is_done else ""
            _done_label = f' <span style="color:#22c55e;font-size:11px;">({_done_by})</span>' if _done_by else ""
            st.markdown(
                f'<div style="font-size:13px;font-weight:600;padding-top:5px;'
                f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'
                f'color:{"#64748b" if _is_done else "#1a1a2e"};" title="{_nazev}">'
                f'{_status_dot}{_nazev}{_done_label}</div>',
                unsafe_allow_html=True)

        with _rc[1]:
            st.markdown(
                f'<div style="font-size:12px;color:#718096;padding-top:6px;'
                f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'
                f'{_obec}</div>',
                unsafe_allow_html=True)

        with _rc[2]:
            st.markdown(
                f'<div style="font-size:12px;color:#718096;padding-top:6px;">'
                f'{_zaci}</div>',
                unsafe_allow_html=True)

        # 🌐 Web (search fallback if no URL)
        with _rc[3]:
            if _web and _web not in ("nan", "None", ""):
                _web_url = _web if _web.startswith("http") else f"https://{_web}"
                st.link_button("🌐", _web_url, use_container_width=True)
            else:
                _search_url = f"https://www.google.com/search?q={urllib.parse.quote(_nazev + ' ' + _obec)}"
                st.link_button("🔍", _search_url, use_container_width=True,
                               help="Hledat školu na Google")

        # 📧 Email
        with _rc[4]:
            if _email and _email not in ("nan", "None", ""):
                _tmpl = EMAIL_TEMPLATES.get(
                    get_email_template(_rr), EMAIL_TEMPLATES["priority_a"])
                _body = _tmpl["body"]
                st.link_button("📧", make_mailto(_email, _tmpl["subject"], _body),
                               use_container_width=True)
            else:
                st.button("📧", key=f"oe_{_ri}", disabled=True, use_container_width=True)

        # 📞 Telefon
        with _rc[5]:
            if _tel and _tel not in ("nan", "None", ""):
                st.link_button("📞", f"tel:{_tel}", use_container_width=True)
            else:
                st.button("📞", key=f"ot_{_ri}", disabled=True, use_container_width=True)

        # 👤 Ředitel (popover)
        with _rc[6]:
            with st.popover("👤"):
                st.markdown(f"**{_reditel}**" if _reditel and _reditel != "nan" else "—")
                if _ico and _ico != "nan":
                    _ares_url = f"https://ares.gov.cz/ekonomicke-subjekty/res/{_ico}"
                    st.markdown(
                        f'<a href="{_ares_url}" target="_blank" '
                        f'style="font-size:12px;color:#3b82f6;text-decoration:none;">'
                        f'🏢 IČO: {_ico} → ARES</a>',
                        unsafe_allow_html=True)

        # Oslovit — přiřazení osoby + stav
        with _rc[7]:
            if _is_done:
                # Najdi aktuální stav z logu
                _entry = next((o for o in reversed(_olog) if o["izo"] == _izo), {})
                _curr_stav = _entry.get("stav", "Osloveno")
                _stav_key = f"ostav_{_izo}"
                _STAVY = ["Osloveno", "Jednáme", "Nabídka", "Ozvat se později",
                          "Nemají zájem", "Vyhráno 🎉"]
                _STAV_COLORS = {
                    "Osloveno": "#3b82f6", "Jednáme": "#f59e0b",
                    "Nabídka": "#8b5cf6", "Ozvat se později": "#64748b",
                    "Nemají zájem": "#ef4444", "Vyhráno 🎉": "#22c55e",
                }
                _stav_clr = _STAV_COLORS.get(_curr_stav, "#64748b")
                st.markdown(
                    f'<div style="font-size:11px;color:{_stav_clr};font-weight:700;'
                    f'padding-top:2px;">{_done_by}</div>',
                    unsafe_allow_html=True)
                _new_stav = st.selectbox(
                    "stav", _STAVY,
                    index=_STAVY.index(_curr_stav) if _curr_stav in _STAVY else 0,
                    label_visibility="collapsed", key=_stav_key)
                if _new_stav != _curr_stav:
                    # Aktualizuj stav v logu
                    for _o in reversed(_olog):
                        if _o["izo"] == _izo:
                            _o["stav"] = _new_stav
                            break
                    st.rerun()
            else:
                _btn_key = f"obtn_{_izo}"
                _sel_key = f"osel_{_izo}"
                _sel_person = st.selectbox(
                    "kdo", ["—"] + TEAM,
                    label_visibility="collapsed", key=_sel_key)
                if _sel_person != "—":
                    if st.button("✓", key=_btn_key, use_container_width=True):
                        st.session_state["outreach_log"].append({
                            "izo": _izo,
                            "person": _sel_person,
                            "date": today.strftime("%Y-%m-%d"),
                            "nazev": _nazev,
                            "stav": "Osloveno",
                        })
                        del st.session_state[_sel_key]
                        st.rerun()


# ══════════════════════════════════════════════════════════════
#  🏠 PŘEHLED (Dashboard)
# ══════════════════════════════════════════════════════════════
elif nav == "🏠 Přehled":

    # Lokalizovaný pozdrav
    _hour = datetime.now().hour
    _greeting = "Dobré ráno" if _hour < 11 else "Dobré odpoledne" if _hour < 17 else "Dobrý večer"
    _day_cz = ["pondělí","úterý","středu","čtvrtek","pátek","sobotu","neděli"][datetime.now().weekday()]
    _date_str = datetime.now().strftime(f"%-d. %-m. %Y")
    page_header(f"🏠 {_greeting}, Matyasi",
                f"Dnes je {_day_cz} {_date_str} · tady je přehled situace")

    crm_df    = load_crm()
    quotes_df = load_quotes()
    vz_df     = load_vz_alerts()

    today       = datetime.now().date()
    week_start  = today - timedelta(days=today.weekday())
    month_start = today.replace(day=1)

    # ── Parse CRM dates ───────────────────────────────────────
    crm_dates = pd.Series(dtype="object")
    if not crm_df.empty:
        for _col in ["Datum kontaktu", "datum", "Datum", "date"]:
            if _col in crm_df.columns:
                crm_dates = pd.to_datetime(crm_df[_col], format="%d.%m.%Y",
                                           errors="coerce").dt.date
                break

    contacted_today = int((crm_dates == today).sum())       if len(crm_dates) else 0
    contacted_week  = int((crm_dates >= week_start).sum())  if len(crm_dates) else 0
    contacted_month = int((crm_dates >= month_start).sum()) if len(crm_dates) else 0

    # ── Parse nabídky data ────────────────────────────────────
    open_quotes   = 0
    won_value_czk = 0.0
    expiring_soon = 0
    if not quotes_df.empty:
        if "stav" in quotes_df.columns:
            open_quotes = int(quotes_df["stav"].isin(
                ["Připravena", "Odesláno", "Reakce"]).sum())
        if "celkem_s_dph" in quotes_df.columns and "stav" in quotes_df.columns:
            won_mask = quotes_df["stav"] == "Vyhráno"
            won_value_czk = float(
                pd.to_numeric(quotes_df.loc[won_mask, "celkem_s_dph"],
                              errors="coerce").sum())
        if "platnost_do" in quotes_df.columns and "stav" in quotes_df.columns:
            _platnost = pd.to_datetime(quotes_df["platnost_do"],
                                       errors="coerce").dt.date
            _open_m   = quotes_df["stav"].isin(["Připravena", "Odesláno", "Reakce"])
            expiring_soon = int((
                _open_m &
                (_platnost >= today) &
                (_platnost <= today + timedelta(days=14))
            ).sum())

    # ── KPI bar ───────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Osloveno dnes",    contacted_today,
              delta=f"↑ {contacted_week} tento týden" if contacted_week else None)
    k2.metric("Osloveno měsíc",   contacted_month)
    k3.metric("Otevřené nabídky", open_quotes,
              delta=f"⏰ {expiring_soon} expirují" if expiring_soon else None,
              delta_color="inverse" if expiring_soon else "normal")
    k4.metric("Vyhráno Kč",
              f"{won_value_czk/1000:.0f}k" if won_value_czk >= 1000 else
              (f"{won_value_czk:,.0f}" if won_value_czk else "—"))
    k5.metric("Škol v DB", len(schools_df) if not schools_df.empty else 0)

    # ── Denní cíl + streak ────────────────────────────────────
    DAILY_GOAL = 5
    _goal_pct = min(contacted_today / DAILY_GOAL, 1.0) if DAILY_GOAL else 0
    _goal_clr = "#22c55e" if _goal_pct >= 1.0 else "#f59e0b" if _goal_pct >= 0.5 else "#e74c3c"
    _goal_txt = ("🎉 Splněno!" if _goal_pct >= 1.0
                 else f"📍 {contacted_today}/{DAILY_GOAL} — ještě {DAILY_GOAL - contacted_today}")
    # Streak — kolik dní v řadě oslovil alespoň 1 školu
    _streak = 0
    if len(crm_dates):
        for _si in range(1, 60):
            _sd = today - timedelta(days=_si)
            if _sd.weekday() >= 5:
                continue  # skip víkendy
            if int((crm_dates == _sd).sum()) > 0:
                _streak += 1
            else:
                break
    _streak_txt = f"🔥 {_streak}d streak" if _streak > 0 else ""
    st.markdown(
        f'<div style="background:white;border:1px solid #ece8e1;border-radius:12px;'
        f'padding:10px 20px;display:flex;align-items:center;gap:16px;margin-top:-2px;'
        f'box-shadow:0 1px 3px rgba(0,0,0,0.03);">'
        f'<span style="font-size:12px;font-weight:700;color:#1a1a2e;white-space:nowrap;'
        f'text-transform:uppercase;letter-spacing:0.5px;">Denní cíl</span>'
        f'<div style="flex:1;background:#ece8e1;border-radius:6px;height:8px;overflow:hidden;">'
        f'<div style="width:{_goal_pct*100:.0f}%;background:{_goal_clr};height:100%;'
        f'border-radius:6px;transition:width 0.4s cubic-bezier(0.4,0,0.2,1);"></div></div>'
        f'<span style="font-size:12px;color:#718096;white-space:nowrap;">{_goal_txt}</span>'
        f'<span style="font-size:13px;color:#f59e0b;white-space:nowrap;font-weight:700;">'
        f'{_streak_txt}</span>'
        f'</div>',
        unsafe_allow_html=True)

    # ── Info strip (nabídky + intel) — kompaktní horizontální ──
    _strip_items = []
    # Expirující nabídky
    _exp_q_list = []
    if not quotes_df.empty and "platnost_do" in quotes_df.columns and "stav" in quotes_df.columns:
        _exp_q = quotes_df.copy()
        _exp_q["_p"] = pd.to_datetime(_exp_q["platnost_do"], errors="coerce").dt.date
        _exp_q = _exp_q[
            _exp_q["stav"].isin(["Připravena", "Odesláno", "Reakce"]) &
            _exp_q["_p"].notna() &
            (_exp_q["_p"] >= today) &
            (_exp_q["_p"] <= today + timedelta(days=30))
        ].sort_values("_p")
        _exp_q_list = list(_exp_q.iterrows())

    # Market intel count
    _intel_cnt = 0
    if not vz_df.empty:
        if "je_skola" in vz_df.columns and "je_nabytek" in vz_df.columns:
            _intel_cnt = int((vz_df["je_skola"] & vz_df["je_nabytek"]).sum())
        elif "je_skola" in vz_df.columns:
            _intel_cnt = int(vz_df["je_skola"].sum())

    # ── Horizontální info strip ──────────────────────────────
    _has_activity = False
    days_30 = [today - timedelta(days=i) for i in range(29, -1, -1)]
    act_rows = []
    for _d in days_30:
        _crm = int((crm_dates == _d).sum()) if len(crm_dates) else 0
        _q = 0
        if not quotes_df.empty and "datum" in quotes_df.columns:
            _q = int((pd.to_datetime(quotes_df["datum"], errors="coerce").dt.date == _d).sum())
        act_rows.append({"datum": _d, "Oslovení": _crm, "Nabídky": _q})
    act_df = pd.DataFrame(act_rows)
    act_df["datum"] = pd.to_datetime(act_df["datum"])
    _has_activity = act_df[["Oslovení", "Nabídky"]].sum().sum() > 0

    # Rozhodnutí o layoutu: chart + side info NEBO jen info strip
    if _has_activity:
        _ch_left, _ch_right = st.columns([3, 1.2], gap="medium")
        with _ch_left:
            _fig_trend = px.bar(
                act_df.melt(id_vars="datum", value_vars=["Oslovení", "Nabídky"]),
                x="datum", y="value", color="variable",
                color_discrete_map={"Oslovení": "#e74c3c", "Nabídky": "#3b82f6"},
                labels={"datum": "", "value": "", "variable": ""},
                height=160,
            )
            _fig_trend.update_layout(
                margin=dict(l=0, r=0, t=4, b=0),
                legend=dict(orientation="h", y=1.15, x=0, font_size=11),
                plot_bgcolor="white", paper_bgcolor="white",
                bargap=0.25,
                xaxis=dict(showgrid=False, tickformat="%-d.%-m.", tickfont_size=10),
                yaxis=dict(showgrid=True, gridcolor="#f1f5f9", tickformat="d",
                           tickfont_size=10),
            )
            st.plotly_chart(_fig_trend, use_container_width=True,
                            config={"displayModeBar": False})
        with _ch_right:
            if _exp_q_list:
                st.markdown(
                    '<div style="font-size:12px;font-weight:700;color:#0f172a;'
                    'text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;">'
                    '⏰ Expirující nabídky</div>',
                    unsafe_allow_html=True)
                for _qi, (_, _q) in enumerate(_exp_q_list[:3]):
                    _plat = _q.get("_p", today)
                    _days = (_plat - today).days if _plat else 0
                    _uc = ("#ef4444" if _days <= 7 else "#f59e0b" if _days <= 14 else "#3b82f6")
                    _val = pd.to_numeric(_q.get("celkem_s_dph", 0), errors="coerce")
                    st.markdown(
                        f'<div style="padding:4px 0;border-bottom:1px solid #f1f5f9;font-size:12px;">'
                        f'<span style="background:{_uc};color:white;padding:1px 5px;'
                        f'border-radius:3px;font-size:10px;font-weight:700;">{_days}d</span> '
                        f'<b>{str(_q.get("skola_nazev","—"))[:22]}</b>'
                        f'<span style="color:#64748b;"> · {_val:,.0f} Kč</span></div>',
                        unsafe_allow_html=True)
            if _intel_cnt:
                st.markdown(
                    f'<div style="background:#f0f9ff;border:1px solid #bae6fd;'
                    f'border-radius:8px;padding:10px 12px;margin-top:8px;'
                    f'font-size:12px;color:#0369a1;">'
                    f'📡 <b>{_intel_cnt}</b> nových smluv → <b>Market Intel</b></div>',
                    unsafe_allow_html=True)
            # Follow-up připomínky
            _followups = []
            if not crm_df.empty:
                for _fc in ["Datum kontaktu", "datum", "Datum", "date"]:
                    if _fc in crm_df.columns:
                        _fu_dates = pd.to_datetime(crm_df[_fc], format="%d.%m.%Y",
                                                    errors="coerce").dt.date
                        _fu_mask = (_fu_dates <= today - timedelta(days=7)) & (_fu_dates >= today - timedelta(days=30))
                        _fu_df = crm_df[_fu_mask]
                        _stav_col = next((c for c in ["Stav", "stav", "status"] if c in crm_df.columns), None)
                        if _stav_col:
                            _fu_df = _fu_df[_fu_df[_stav_col].isin(["Osloveno", "Nezvedli"])]
                        for _, _fur in _fu_df.head(5).iterrows():
                            _fu_name = _fur.get("Název školy", _fur.get("nazev", "—"))
                            _fu_d = _fu_dates[_fur.name]
                            _fu_age = (today - _fu_d).days if _fu_d else 0
                            _followups.append((_fu_age, str(_fu_name)[:25]))
                        break

            if _followups:
                st.markdown(
                    '<div style="font-size:12px;font-weight:700;color:#0f172a;'
                    'text-transform:uppercase;letter-spacing:0.5px;margin-top:10px;'
                    'margin-bottom:4px;">🔄 Follow-up</div>',
                    unsafe_allow_html=True)
                for _fu_age, _fu_name in sorted(_followups, key=lambda x: -x[0])[:4]:
                    _fu_clr = "#ef4444" if _fu_age >= 14 else "#f59e0b"
                    st.markdown(
                        f'<div style="padding:3px 0;font-size:12px;border-bottom:1px solid #f1f5f9;">'
                        f'<span style="background:{_fu_clr};color:white;padding:1px 5px;'
                        f'border-radius:3px;font-size:10px;font-weight:700;">{_fu_age}d</span> '
                        f'{_fu_name}</div>',
                        unsafe_allow_html=True)
            elif not _exp_q_list and not _intel_cnt:
                st.markdown(
                    '<div style="background:#f8fafc;border:1px solid #e2e8f0;'
                    'border-radius:8px;padding:14px;text-align:center;color:#94a3b8;'
                    'font-size:12px;">Žádné urgentní události</div>',
                    unsafe_allow_html=True)
    else:
        # Bez aktivity — kompaktní info strip místo velkého grafu
        _info_cols = []
        if _intel_cnt:
            _info_cols.append(
                f'<div style="flex:1;background:#f0f9ff;border:1px solid #bae6fd;'
                f'border-radius:8px;padding:12px 16px;font-size:13px;color:#0369a1;">'
                f'📡 <b>{_intel_cnt} nových smluv</b> ze škol → záložka <b>Market Intel</b></div>')
        _info_cols.append(
            '<div style="flex:1;background:#f8fafc;border:1px solid #e2e8f0;'
            'border-radius:8px;padding:12px 16px;font-size:13px;color:#64748b;">'
            '📈 Zatím žádná aktivita v CRM. Začni oslovovat školy níže.</div>')
        st.markdown(
            '<div style="display:flex;gap:12px;margin-bottom:4px;">'
            + ''.join(_info_cols) + '</div>',
            unsafe_allow_html=True)

    st.divider()

    # ══ PRIORITNÍ ŠKOLY (full width) ═════════════════════════
    _hc, _pc = st.columns([8, 0.4])
    with _hc:
        st.markdown(
            '<h3 style="font-size:16px;font-weight:700;color:#0f172a;'
            'margin:0 0 4px 0;">🎯 Prioritní školy k oslovení</h3>',
            unsafe_allow_html=True)
    with _pc:
        st.markdown('<div style="margin-top:2px;"></div>', unsafe_allow_html=True)
        with st.popover("❓"):
            st.markdown("""
**Urgency score — jak se počítá**

| Faktor | Max bodů |
|--------|----------|
| 💰 Dotace 2 roky zpět | +40b |
| 🔴 Nábytek 8+ let starý | +35b |
| 📅 Sezóna (březen–duben = peak) | +20b |
| 📍 Do 30 km od dílny | +15b |
| 🟢 Bez VZ — přímá poptávka | +20b |
| 🏘️ Sousední škola koupila | +10b |
| 🏫 500+ žáků | +16–20b |
| 🌍 Praha / Středočeský kraj | +5b |

**⛔ Disqualifier:** koupili < 2 roky → skóre 0
            """)

    if schools_df.empty:
        st.info("Spusť pipeline: `python main.py`")
    else:
        # ── Compute recent_obce pro cluster efekt ─────────
        _recent_obce: set = set()
        if not vz_df.empty and not schools_df.empty:
            _vz_skoly = vz_df[vz_df.get("je_skola", pd.Series(
                False, index=vz_df.index))] if "je_skola" in vz_df.columns else pd.DataFrame()
            if not _vz_skoly.empty and "platce_ico" in _vz_skoly.columns:
                _vz_icos = set(_vz_skoly["platce_ico"].dropna().astype(str))
                _matched = schools_df[schools_df["ico"].astype(str).isin(_vz_icos)]
                _recent_obce = set(_matched["obec"].dropna().str.strip().str.lower())

        _contacted  = get_contacted_set()
        _curr_year  = datetime.now().year
        _curr_month = datetime.now().month
        _candidates = []
        for _, _row in schools_df.iterrows():
            _izo = str(_row.get("izo", ""))
            if _izo in _contacted:
                continue
            _u = compute_urgency(_row, _curr_year, _curr_month, _recent_obce)
            if _u["kategorie"] in ("pockat", "nizka"):
                continue
            _candidates.append((_u["urgency_score"], _u, _row))
        _candidates.sort(key=lambda x: -x[0])

        if not _candidates:
            st.markdown(
                '<div style="background:#f0fdf4;border:1px solid #bbf7d0;'
                'border-radius:8px;padding:14px;text-align:center;color:#166534;">'
                '🎉 Všechny prioritní školy jsou osloveny</div>',
                unsafe_allow_html=True)

        # ── Search + filtry ──────────────────────────────────
        _sf1, _sf2, _sf3, _sf4 = st.columns([3, 1.2, 1.2, 0.8])
        with _sf1:
            _search_q = st.text_input(
                "🔍 Hledat", placeholder="Název školy, obec...",
                label_visibility="collapsed", key="dash_search")
        with _sf2:
            _kraje = sorted({str(r.get("kraj", "")) for _, _, r in _candidates if r.get("kraj")})
            _filt_kraj = st.selectbox("Kraj", ["Vše"] + _kraje,
                                      label_visibility="collapsed", key="dash_kraj")
        with _sf3:
            _filt_signal = st.selectbox("Signál", [
                "Vše", "🔴 Teď (60+)", "🟡 Brzy (35–59)", "🟢 Připravit (15–34)"
            ], label_visibility="collapsed", key="dash_signal")
        with _sf4:
            _show_n = st.selectbox("Zobrazit", [30, 50, 100], label_visibility="collapsed",
                                   key="dash_n")

        # Filtruj kandidáty
        _filtered = _candidates
        if _search_q:
            _sq = _search_q.lower()
            _filtered = [
                (s, u, r) for s, u, r in _filtered
                if _sq in str(r.get("nazev", "")).lower()
                or _sq in str(r.get("obec", "")).lower()
                or _sq in str(r.get("izo", "")).lower()
            ]
        if _filt_kraj != "Vše":
            _filtered = [(s, u, r) for s, u, r in _filtered
                         if str(r.get("kraj", "")) == _filt_kraj]
        if _filt_signal == "🔴 Teď (60+)":
            _filtered = [(s, u, r) for s, u, r in _filtered if s >= 60]
        elif _filt_signal == "🟡 Brzy (35–59)":
            _filtered = [(s, u, r) for s, u, r in _filtered if 35 <= s < 60]
        elif _filt_signal == "🟢 Připravit (15–34)":
            _filtered = [(s, u, r) for s, u, r in _filtered if 15 <= s < 35]

        # Počet výsledků
        st.caption(f"Zobrazuji {min(len(_filtered), _show_n)} z {len(_filtered)} škol"
                   + (f" · hledání: \"{_search_q}\"" if _search_q else ""))

        # ── Kompaktní řádky — full width ─────────────────────
        st.markdown(
            '<div style="display:grid;grid-template-columns:44px 1fr 1fr 32px 32px 32px;'
            'gap:6px;padding:6px 10px;background:white;border:1px solid #ece8e1;'
            'border-radius:12px 12px 0 0;border-bottom:2px solid #ece8e1;'
            'font-size:10px;font-weight:700;color:#a0aec0;text-transform:uppercase;'
            'letter-spacing:0.7px;">'
            '<div>Sk.</div><div>Škola</div><div>Parametry</div>'
            '<div></div><div></div><div></div>'
            '</div>',
            unsafe_allow_html=True)

        for _idx, (_score, _u, _row) in enumerate(_filtered[:_show_n]):
            _exp_key = f"dash_s_{_idx}"
            _is_exp  = st.session_state.get(_exp_key, False)
            _note_key = f"dash_note_{_idx}"
            _show_note = st.session_state.get(_note_key, False)

            # Řádek — full width s lepšími proporcemi
            _c1, _c2, _c3, _c4, _c5, _c6 = st.columns(
                [0.35, 3.0, 2.4, 0.22, 0.22, 0.22])

            with _c1:
                _clr = _u["barva"]
                st.markdown(
                    f'<div style="background:{_clr};color:white;border-radius:6px;'
                    f'padding:2px 0;font-weight:800;font-size:12px;'
                    f'text-align:center;margin-top:6px;line-height:1.5;'
                    f'min-width:36px;">'
                    f'{_score}</div>',
                    unsafe_allow_html=True)

            with _c2:
                _nazev = str(_row.get("nazev", ""))
                st.markdown(
                    f'<div style="font-size:13.5px;font-weight:600;padding-top:5px;'
                    f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'
                    f'color:#1e293b;" title="{_nazev}">{_nazev}</div>',
                    unsafe_allow_html=True)

            with _c3:
                _zaci = int(float(_row.get("pocet_zaku", 0) or 0))
                _sig  = short_signal(_u)
                _obec = str(_row.get("obec", ""))[:18]
                st.markdown(
                    f'<div style="font-size:12px;color:#64748b;padding-top:6px;'
                    f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">'
                    f'{_obec} · {_zaci} žáků · {_sig}</div>',
                    unsafe_allow_html=True)

            with _c4:
                _email = str(_row.get("email", "") or "")
                if _email and _email not in ("nan", "None", ""):
                    _tmpl = EMAIL_TEMPLATES.get(
                        get_email_template(_row), EMAIL_TEMPLATES["priority_a"])
                    _body = _tmpl["body"].replace(
                        "[název školy]", str(_row.get("nazev", "")))
                    st.link_button(
                        "📧", make_mailto(_email, _tmpl["subject"], _body),
                        use_container_width=True)
                else:
                    st.button("📧", key=f"nem_{_idx}", disabled=True,
                              use_container_width=True)

            with _c5:
                if st.button("✓", key=f"dd_{_idx}", use_container_width=True,
                             help="Označit jako osloveno"):
                    st.session_state[_note_key] = True
                    st.rerun()

            with _c6:
                if st.button("▲" if _is_exp else "▼",
                             key=f"dt_{_idx}", use_container_width=True,
                             help="Detail školy"):
                    st.session_state[_exp_key] = not _is_exp
                    st.rerun()

            # ── Poznámka při označení ✓ ──────────────────────
            if _show_note:
                with st.container(border=True):
                    st.markdown(
                        f'<div style="font-size:13px;font-weight:600;color:#0f172a;'
                        f'margin-bottom:4px;">✓ Označit: {_nazev}</div>',
                        unsafe_allow_html=True)
                    _nc1, _nc2 = st.columns([2, 1])
                    with _nc1:
                        _note_typ = st.selectbox(
                            "Typ kontaktu", ["📧 Email", "📞 Telefon", "🤝 Osobně",
                                              "📋 Jiné"],
                            label_visibility="collapsed", key=f"ntype_{_idx}")
                    with _nc2:
                        _note_stav = st.selectbox(
                            "Stav", ["Osloveno", "Nezvedli", "Ozvou se",
                                     "Nemají zájem", "Schůzka"],
                            label_visibility="collapsed", key=f"nstav_{_idx}")
                    _note_txt = st.text_input(
                        "Poznámka", placeholder="Volný text — co se řešilo...",
                        label_visibility="collapsed", key=f"ntxt_{_idx}")
                    _nb1, _nb2 = st.columns(2)
                    with _nb1:
                        if st.button("💾 Uložit", key=f"nsave_{_idx}",
                                     type="primary", use_container_width=True):
                            try:
                                from sheets.sheets_sync import upsert_crm_contact
                                _poz = f"{_note_typ} · {_note_txt}" if _note_txt else _note_typ
                                upsert_crm_contact(
                                    _row, stav=_note_stav,
                                    poznamka=f"{_poz} ({datetime.now().strftime('%d.%m.%Y')})")
                                st.toast(f"✅ {_nazev} — {_note_stav}")
                                st.session_state[_note_key] = False
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as _e:
                                st.error(str(_e))
                    with _nb2:
                        if st.button("✕ Zrušit", key=f"ncanc_{_idx}",
                                     use_container_width=True):
                            st.session_state[_note_key] = False
                            st.rerun()

            # ── Rozrolovaný detail ────────────────────────
            if _is_exp:
                with st.container():
                    st.markdown(
                        '<div style="background:#f8fafc;border-left:3px solid #e74c3c;'
                        'padding:10px 16px;font-size:13px;margin-bottom:4px;">',
                        unsafe_allow_html=True)
                    _d1, _d2, _d3, _d4 = st.columns(4)
                    _d1.markdown(
                        f"**IZO:** `{_row.get('izo','—')}`")
                    _d2.markdown(
                        f"**Kraj:** {_row.get('kraj','—')}")
                    _d3.markdown(
                        f"**Přístup:** {_row.get('pristup','—')}")
                    _d4.markdown(
                        f"**Email:** {_row.get('email','—')}")
                    if _u.get("reasons"):
                        st.caption("📊 " + _u["reasons"])
                    st.markdown('</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  🎯 AKCE DNES
# ══════════════════════════════════════════════════════════════
elif nav == "🎯 Akce dnes":
    page_header("🎯 Akce dnes",
                "Školy seřazené dle šance na úspěch · urgency score 0–100 · transparentní důvody")

    col_main, col_side = st.columns([3, 1])

    with col_side:
        st.subheader("Filtry")
        show_ted     = st.checkbox("🔴 Oslovit teď (60+)", value=True)
        show_brzy    = st.checkbox("🟡 Oslovit brzy (35–59)", value=True)
        show_prep    = st.checkbox("🟢 Připravit kontakt (15–34)", value=False)
        top_n        = st.slider("Max zobrazených", 5, 50, 15)
        hide_contacted = st.checkbox("Skrýt již oslovené", value=True)

        st.divider()
        st.caption("""
**Jak funguje urgency score:**
- 💰 Dotace 2r zpět = +40b *(nejsilnější signál)*
- 🔴 Přezrálé 8+ let = +35b
- 🟡 Přezrálé 5-7 let = +25b
- 🟢 Bez VZ (poptávka) = +20b
- 🏫 500+ žáků = +16-20b
- 📍 Praha/Stč = +5b
- ⚫ Koupili < 2 roky = vyřazeni
        """)

        st.divider()
        st.subheader("Email šablona")
        email_template_key = st.selectbox(
            "Šablona",
            list(EMAIL_TEMPLATES.keys()),
            format_func=lambda k: EMAIL_TEMPLATES[k]["label"],
            label_visibility="collapsed",
        )

    with col_main:
        if schools_df.empty:
            st.error("Data škol nenalezena.")
            st.stop()

        contacted = get_contacted_set() if hide_contacted else set()

        # ── Vypočítej urgency pro všechny školy ───────────────
        current_year = datetime.now().year

        # ── Vypočítej urgency pro VŠECHNY školy (pro správné metriky) ──
        all_candidates = []
        waiting_count  = 0
        low_count      = 0

        for _, row in schools_df.iterrows():
            izo = str(row.get("izo", ""))
            if izo in contacted:
                continue
            u = compute_urgency(row, current_year)
            if u["kategorie"] == "pockat":
                waiting_count += 1
                continue
            if u["kategorie"] == "nizka":
                low_count += 1
                continue
            all_candidates.append({
                "urgency_score":   u["urgency_score"],
                "kategorie":       u["kategorie"],
                "kategorie_label": u["kategorie_label"],
                "signal":          u["signal"],
                "reasons":         u.get("reasons", ""),
                "barva":           u["barva"],
                "nazev":           str(row.get("nazev", "")),
                "obec":            str(row.get("obec", "")),
                "kraj":            str(row.get("kraj", "")),
                "email":           str(row.get("email", "") or ""),
                "izo":             izo,
                "score_total":     row.get("score_total", 0),
                "priorita":        str(row.get("priorita", "C")),
                "zaci":            int(float(row.get("pocet_zaku", 0) or 0)),
                "template":        get_email_template(row),
                "_row":            row,
            })

        # Celkové počty (před omezením top_n a filtry viditelnosti)
        ted_total  = sum(1 for i in all_candidates if i["kategorie"] == "ted")
        brzy_total = sum(1 for i in all_candidates if i["kategorie"] == "brzy")
        prep_total = sum(1 for i in all_candidates if i["kategorie"] == "pripravit")

        # Metriky — celé portfolio
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("🔴 Oslovit teď",  ted_total,
                  help="Dotace 1-3 roky + velká škola. Bez dotačních dat = 0.")
        m2.metric("🟡 Oslovit brzy", brzy_total,
                  help="Přezrálé 5+ let nebo střední školy bez VZ")
        m3.metric("🟢 Připravit",    prep_total,
                  help="Menší školy, poptávkový potenciál")
        m4.metric("⚫ Přeskočit",    waiting_count + low_count,
                  help=f"Počkat (koupili < 2r): {waiting_count} · Nízká priorita: {low_count}")

        if ted_total == 0:
            st.info(
                "💡 **Tip:** Kategorie 🔴 'Oslovit teď' se zobrazí po spuštění pipeline s dotačními daty "
                "(`python main.py --skip-vz`). Nyní skóre závisí jen na velikosti školy a regionu."
            )

        # Filtr dle viditelnosti a limit
        action_items = [
            i for i in all_candidates
            if (i["kategorie"] == "ted"      and show_ted)
            or (i["kategorie"] == "brzy"     and show_brzy)
            or (i["kategorie"] == "pripravit" and show_prep)
        ]
        action_items.sort(key=lambda x: -x["urgency_score"])
        action_items = action_items[:top_n]

        if not action_items:
            st.markdown(
                '<div style="text-align:center;padding:40px 20px;color:#94a3b8;">'
                '<div style="font-size:40px;">🎯</div>'
                '<div style="font-size:15px;margin-top:10px;font-weight:600;color:#64748b;">'
                'Žádné školy pro zvolené filtry</div>'
                '<div style="font-size:13px;margin-top:4px;">'
                'Rozšiř filtry vpravo nebo spusť pipeline s dotačními daty</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            st.subheader(f"📌 {len(action_items)} škol k oslovení")

            for item in action_items:
                with st.container(border=True):
                    col_info, col_score, col_btns = st.columns([3, 1, 1])

                    with col_info:
                        # Badge kategorie
                        st.markdown(
                            f'<span style="background:{item["barva"]};color:white;'
                            f'padding:2px 10px;border-radius:4px;font-size:11px;font-weight:bold;">'
                            f'{item["kategorie_label"]}</span>&nbsp;&nbsp;'
                            f'<b style="font-size:15px;color:#1a1a2e;">{item["nazev"]}</b>',
                            unsafe_allow_html=True,
                        )
                        st.caption(f"📍 {item['obec']} · {item['kraj']} · {item['zaci']} žáků")
                        st.caption(f"💡 {item['signal']}")
                        # Transparentní scoring breakdown
                        with st.expander("📊 Proč tato škola?", expanded=False):
                            st.caption(f"**Urgency score: {item['urgency_score']}/100**")
                            if item["reasons"]:
                                for r in item["reasons"].split(" | "):
                                    st.caption(f"  {r}")
                            st.caption(f"CRM skóre: {item['score_total']}")

                    with col_score:
                        score = item["urgency_score"]
                        color = item["barva"]
                        st.markdown(
                            f'<div style="text-align:center;padding:6px 4px;">'
                            f'<div style="font-size:32px;font-weight:800;color:{color};'
                            f'line-height:1;">{score}</div>'
                            f'<div style="font-size:10px;color:#94a3b8;margin-top:1px;">/ 100</div>'
                            f'<div style="margin-top:8px;background:#f1f5f9;border-radius:4px;'
                            f'height:5px;overflow:hidden;">'
                            f'<div style="width:{score}%;height:100%;background:{color};'
                            f'border-radius:4px;transition:width 0.3s;"></div>'
                            f'</div>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )

                    with col_btns:
                        tmpl = EMAIL_TEMPLATES.get(item["template"], EMAIL_TEMPLATES["priority_a"])
                        email = item["email"]

                        if email and email not in ("nan", "", "None"):
                            body_filled = tmpl["body"].replace("[název školy]", item["nazev"])
                            mailto = make_mailto(email, tmpl["subject"], body_filled)
                            st.link_button("📧 Napsat email", mailto, use_container_width=True)
                        else:
                            st.caption("📧 Email neznámý")

                        btn_key = f"done_{item['izo']}_{item['nazev'][:8]}"
                        if st.button("✅ Osloveno", key=btn_key,
                                     use_container_width=True, type="secondary"):
                            try:
                                from sheets.sheets_sync import upsert_crm_contact
                                result = upsert_crm_contact(
                                    item["_row"],
                                    stav="Osloveno",
                                    poznamka=f"Osloveno přes CRM {datetime.now().strftime('%d.%m.%Y')}",
                                )
                                st.success("✅ Zaznamenáno!")
                                st.cache_data.clear()
                                st.rerun()
                            except Exception as e:
                                st.error(f"Chyba: {e}")

        # ── Odkaz na Intel záložku ────────────────────────────
        st.divider()
        st.markdown(
            '<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;'
            'padding:12px 16px;font-size:13px;color:#64748b;">'
            '📡 Přehled nových smluv a konkurence najdeš v záložce <b>📡 Market Intel</b>'
            '</div>',
            unsafe_allow_html=True,
        )


# ══════════════════════════════════════════════════════════════
#  📡 MARKET INTEL
# ══════════════════════════════════════════════════════════════
elif nav == "📡 Market Intel":
    page_header("📡 Market Intel",
                "Kdo nedávno koupil nábytek · kdo to dodal · kdy je správný čas zavolat",
                accent="#1e293b")

    vz_df      = load_vz_alerts()
    market_df  = load_market_data()

    # ── KPI ──────────────────────────────────────────────────
    _i_df = pd.DataFrame()
    if not vz_df.empty:
        _i_df = vz_df.copy()
        if "je_skola" in _i_df.columns:
            _i_df = _i_df[_i_df["je_skola"]]

    _total_val   = pd.to_numeric(_i_df["hodnota_czk"], errors="coerce").sum() if not _i_df.empty and "hodnota_czk" in _i_df.columns else 0
    _competitors = _i_df["dodavatel"].nunique() if not _i_df.empty and "dodavatel" in _i_df.columns else 0
    _skol        = _i_df["platce"].nunique()    if not _i_df.empty and "platce"    in _i_df.columns else 0
    _nabytek_cnt = int(_i_df["je_nabytek"].sum()) if not _i_df.empty and "je_nabytek" in _i_df.columns else 0

    ik1, ik2, ik3, ik4 = st.columns(4)
    ik1.metric("Škol v alertu",      _skol)
    ik2.metric("Z toho nábytek",     _nabytek_cnt)
    ik3.metric("Celková hodnota",     f"{_total_val/1e6:.1f} M Kč" if _total_val >= 1e6 else f"{_total_val:,.0f} Kč")
    ik4.metric("Různí dodavatelé",   _competitors)

    st.divider()

    # ── Filtry ────────────────────────────────────────────────
    fc1, fc2, fc3 = st.columns([2, 2, 1])
    with fc1:
        _show_only_nabytek = st.checkbox("Jen smlouvy s nábytkem v předmětu", value=True)
    with fc2:
        _min_val = st.number_input("Min. hodnota (Kč)", value=0, step=50000,
                                   format="%d")
    with fc3:
        _sort_by = st.selectbox("Řadit dle", ["Hodnota ↓", "Datum ↓", "Škola A→Z"])

    # ── Filtruj data ─────────────────────────────────────────
    _display = _i_df.copy()
    if _show_only_nabytek and "je_nabytek" in _display.columns:
        _display = _display[_display["je_nabytek"]]
    if _min_val > 0 and "hodnota_czk" in _display.columns:
        _display = _display[pd.to_numeric(_display["hodnota_czk"], errors="coerce") >= _min_val]
    if not _display.empty and "hodnota_czk" in _display.columns:
        if _sort_by == "Hodnota ↓":
            _display = _display.sort_values("hodnota_czk", ascending=False)
        elif _sort_by == "Datum ↓":
            _display = _display.sort_values("datum", ascending=False)
        elif _sort_by == "Škola A→Z":
            _display = _display.sort_values("platce")

    if _display.empty:
        st.markdown(
            '<div style="text-align:center;padding:40px;color:#94a3b8;">'
            '<div style="font-size:36px;">📡</div>'
            '<div style="margin-top:10px;font-size:14px;">Žádná data.<br>'
            'Aktualizuj VZ Monitor v záložce <b>📋 VZ Monitor</b>.</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f'<div style="font-size:12px;color:#94a3b8;margin-bottom:8px;">'
            f'Zobrazuji {len(_display)} smluv</div>',
            unsafe_allow_html=True,
        )

        # ── Header řádků ───────────────────────���─────────────
        st.markdown(
            '<div style="display:grid;'
            'grid-template-columns:110px 1fr 140px 120px 30px;'
            'gap:4px;padding:4px 8px;background:#f8fafc;'
            'border-radius:6px 6px 0 0;border:1px solid #e2e8f0;border-bottom:none;'
            'font-size:11px;font-weight:600;color:#94a3b8;text-transform:uppercase;'
            'letter-spacing:0.5px;">'
            '<div>Hodnota</div><div>Škola</div>'
            '<div>Dodavatel</div><div>Datum</div><div></div>'
            '</div>',
            unsafe_allow_html=True,
        )

        for _ii, (_, _ir) in enumerate(_display.iterrows()):
            _ikey = f"intel_row_{_ii}"
            _iexp = st.session_state.get(_ikey, False)
            _ival = float(pd.to_numeric(_ir.get("hodnota_czk", 0), errors="coerce") or 0)
            _bg   = "white" if _ii % 2 == 0 else "#fafafa"

            _ic1, _ic2, _ic3, _ic4, _ic5 = st.columns([0.9, 2.8, 1.4, 1.0, 0.28])

            with _ic1:
                # Hodnota s barevným kódováním dle velikosti
                _vc = "#e74c3c" if _ival >= 500_000 else "#f59e0b" if _ival >= 200_000 else "#64748b"
                st.markdown(
                    f'<div style="font-size:12px;font-weight:700;color:{_vc};'
                    f'padding-top:7px;text-align:right;">{_ival/1000:.0f}k Kč</div>',
                    unsafe_allow_html=True,
                )

            with _ic2:
                _platce = str(_ir.get("platce", ""))
                st.markdown(
                    f'<div style="font-size:13px;font-weight:600;padding-top:6px;'
                    f'color:#1e293b;'
                    f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;" '
                    f'title="{_platce}">{_platce}</div>',
                    unsafe_allow_html=True,
                )

            with _ic3:
                _dod = str(_ir.get("dodavatel", "") or "—")[:22]
                _dod_color = "#e74c3c" if any(
                    k in _dod.lower() for k in ["brezka", "matyas", "olmr"]
                ) else "#475569"
                st.markdown(
                    f'<div style="font-size:11px;color:{_dod_color};padding-top:8px;'
                    f'overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">'
                    f'{_dod}</div>',
                    unsafe_allow_html=True,
                )

            with _ic4:
                st.markdown(
                    f'<div style="font-size:11px;color:#94a3b8;padding-top:8px;">'
                    f'{str(_ir.get("datum",""))}</div>',
                    unsafe_allow_html=True,
                )

            with _ic5:
                if st.button("▲" if _iexp else "▼",
                             key=f"itog_{_ii}", use_container_width=True):
                    st.session_state[_ikey] = not _iexp
                    st.rerun()

            # ── Detail ────────────────────────��──────────────
            if _iexp:
                st.markdown(
                    '<div style="background:#f8fafc;border-left:3px solid #1e293b;'
                    'margin:-2px 0 2px 0;padding:10px 16px;font-size:13px;">',
                    unsafe_allow_html=True,
                )
                _xc1, _xc2, _xc3 = st.columns([2, 2, 1])
                _xc1.markdown(
                    f"**Předmět:** {str(_ir.get('predmet',''))[:80]}  \n"
                    f"**Dodavatel:** {_ir.get('dodavatel','—')}"
                )
                _xc2.markdown(
                    f"**Hodnota:** {_ival:,.0f} Kč  \n"
                    f"**IČO školy:** {_ir.get('platce_ico','—')}"
                )
                with _xc3:
                    if _ir.get("odkaz"):
                        st.link_button("🔗 Smlouva",
                                       str(_ir.get("odkaz", "")),
                                       use_container_width=True)
                    if st.button("💾 Do CRM",
                                 key=f"iadd_{_ii}", use_container_width=True):
                        try:
                            from sheets.sheets_sync import upsert_crm_contact
                            upsert_crm_contact(
                                pd.Series({
                                    "izo":   _ir.get("platce_ico", ""),
                                    "nazev": _ir.get("platce", ""),
                                    "ico":   _ir.get("platce_ico", ""),
                                }),
                                stav="Odloženo",
                                poznamka=(
                                    f"Intel: {str(_ir.get('predmet',''))[:60]}"
                                    f" za {_ival:,.0f} Kč ({_ir.get('datum','')})"
                                ),
                            )
                            st.toast("💾 Přidáno do CRM!")
                        except Exception as _e:
                            st.error(str(_e))
                st.markdown('</div>', unsafe_allow_html=True)

    # ── Odkaz na analytiku ───────────────────────────────────
    if not market_df.empty:
        st.divider()
        st.markdown(
            '<div style="background:#f0fdf4;border:1px solid #bbf7d0;border-radius:8px;'
            'padding:14px 18px;font-size:13px;color:#166534;">'
            '📊 Podrobná analýza dodavatelů, tržních podílů a trendů → záložka '
            '<b>📊 Analytika</b></div>',
            unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
#  🗺️ MAPA
# ══════════════════════════════════════════════════════════════
elif nav == "🗺️ Mapa":
    page_header("🗺️ Interaktivní mapa škol",
                "Priorita A/B/C · filtruj dle kraje, velikosti a přístupu", accent="#3b82f6")

    if schools_df.empty:
        st.error("Data škol nenalezena. Spusť nejdřív: `python main.py`")
        st.stop()

    # ── Filtry ────────────────────────────────────────────────
    with st.expander("🔧 Filtry", expanded=True):
        fcol1, fcol2, fcol3, fcol4 = st.columns(4)

        with fcol1:
            kraje = ["Vše"] + sorted(schools_df["kraj"].dropna().unique().tolist())
            selected_kraj = st.selectbox("Kraj", kraje)

        with fcol2:
            selected_priority = st.multiselect(
                "Priorita", ["A", "B", "C"], default=["A", "B"]
            )

        with fcol3:
            max_zaci = int(schools_df["pocet_zaku"].max() or 1000)
            zaci_range = st.slider(
                "Počet žáků", 0, max_zaci, (100, max_zaci)
            )

        with fcol4:
            selected_approach = st.multiselect(
                "Přístup", ["PM", "VZ", "OBA"],
                default=["PM", "VZ", "OBA"],
            )

        show_heatmap = st.checkbox("Zobrazit heatmapu truhlářství (konkurence)", value=False)

    # Aplikuj filtry
    filtered = schools_df.copy()
    if selected_kraj != "Vše":
        filtered = filtered[filtered["kraj"] == selected_kraj]
    if selected_priority:
        filtered = filtered[filtered["priorita"].isin(selected_priority)]
    if selected_approach and "pristup" in filtered.columns:
        filtered = filtered[filtered["pristup"].isin(selected_approach)]
    filtered = filtered[
        (filtered["pocet_zaku"] >= zaci_range[0]) &
        (filtered["pocet_zaku"] <= zaci_range[1])
    ]

    col_map, col_stats = st.columns([3, 1])

    with col_stats:
        st.metric("Škol v filtru", len(filtered))
        st.metric("Z toho geokódováno",
                  int(filtered["lat"].notna().sum()) if "lat" in filtered.columns else 0)

        if "priorita" in filtered.columns:
            counts = filtered["priorita"].value_counts()
            for p, color in [("A", "🔴"), ("B", "🟡"), ("C", "⚫")]:
                st.write(f"{color} Priorita {p}: **{counts.get(p, 0)}**")

        st.divider()
        if "pristup" in filtered.columns:
            st.write("**Přístup:**")
            for p in ["PM", "VZ", "OBA"]:
                cnt = (filtered["pristup"] == p).sum()
                if cnt:
                    st.write(f"· {p}: {cnt}")

    with col_map:
        if filtered.empty or "lat" not in filtered.columns:
            st.warning("Žádné školy pro zvolené filtry.")
        else:
            with st.spinner("Generuji mapu..."):
                comp_df = None
                if show_heatmap:
                    comp_cache = DATA_DIR / "all_competitors.csv"
                    if comp_cache.exists():
                        comp_df = pd.read_csv(comp_cache)

                fmap = build_filtered_map(filtered, show_heatmap, comp_df)
                st_folium(fmap, width=850, height=550, returned_objects=[])

    # Tabulka pod mapou
    st.subheader(f"Školy ({len(filtered)})")
    show_cols = [c for c in ["rank","nazev","obec","kraj","pocet_zaku",
                              "score_total","priorita","pristup","email"]
                 if c in filtered.columns]
    st.dataframe(
        filtered[show_cols].head(200),
        use_container_width=True,
        hide_index=True,
        column_config={
            "score_total": st.column_config.ProgressColumn("Skóre", max_value=100),
            "priorita":    st.column_config.TextColumn("P."),
            "email":       st.column_config.LinkColumn("Email", display_text="📧"),
        },
    )


# ══════════════════════════════════════════════════════════════
#  📋 VZ MONITOR
# ══════════════════════════════════════════════════════════════
elif nav == "📋 VZ Monitor":
    page_header("📋 VZ Monitor",
                "Registr smluv (Hlídač státu) · nákupy nábytku školami · smlouvy ≥ 50 000 Kč",
                accent="#8b5cf6")

    # ── Tlačítko aktualizace ──────────────────────────────────
    col_btn, col_info = st.columns([2, 3])
    with col_btn:
        days_back = st.selectbox("Období", [30, 60, 90, 180], index=2,
                                 format_func=lambda d: f"Posledních {d} dní")
        do_refresh = st.button("🔄 Aktualizovat data", type="primary", use_container_width=True)

    if do_refresh:
        with st.spinner("Stahuji nové smlouvy z Hlídače státu..."):
            try:
                from scrapers.vz_scraper import run_vz_monitor
                new_vz = run_vz_monitor(days_back=days_back, schools_df=schools_df)

                if not new_vz.empty:
                    # Ulož jako latest
                    new_vz.to_csv(OUTPUT_DIR / "vz_alert_latest.csv", index=False, encoding="utf-8-sig")
                    new_vz.to_csv(
                        OUTPUT_DIR / f"vz_alert_{datetime.now().strftime('%Y%m%d')}.csv",
                        index=False, encoding="utf-8-sig",
                    )

                    skoly_new  = int(new_vz["je_skola"].sum()) if "je_skola" in new_vz.columns else 0
                    nabytek_new = int(new_vz["je_nabytek"].sum()) if "je_nabytek" in new_vz.columns else 0

                    st.success(
                        f"✅ Aktualizováno! **{len(new_vz)}** smluv · "
                        f"**{skoly_new}** škol · **{nabytek_new}** s nábytkem v předmětu"
                    )

                    # Sync do Sheets
                    try:
                        from sheets.sheets_sync import sync_vz_monitor
                        sync_vz_monitor(new_vz)
                        st.caption("✔️ Synchronizováno do Google Sheets")
                    except Exception:
                        st.caption("⚠️ Sheets sync selhal")

                    st.cache_data.clear()
                else:
                    st.info("Žádné nové smlouvy v zadaném období.")
            except Exception as e:
                st.error(f"Chyba: {e}")

    # ── Zobrazení dat ─────────────────────────────────────────
    vz_df = load_vz_alerts()

    if vz_df.empty:
        st.info("Klikni na **Aktualizovat data** pro načtení smluv.")
    else:
        # Metriky
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.metric("Celkem smluv", len(vz_df))
        mc2.metric("Školy",
                   int(vz_df["je_skola"].sum()) if "je_skola" in vz_df.columns else "—")
        mc3.metric("Nábytek v předmětu",
                   int(vz_df["je_nabytek"].sum()) if "je_nabytek" in vz_df.columns else "—")
        total_val = vz_df["hodnota_czk"].sum() if "hodnota_czk" in vz_df.columns else 0
        mc4.metric("Celková hodnota", f"{total_val:,.0f} Kč")

        st.divider()

        # Filtry
        show_only_skoly   = st.checkbox("Jen školy", value=True)
        show_only_nabytek = st.checkbox("Jen nábytek v předmětu", value=False)

        display_vz = vz_df.copy()
        if show_only_skoly and "je_skola" in display_vz.columns:
            display_vz = display_vz[display_vz["je_skola"]]
        if show_only_nabytek and "je_nabytek" in display_vz.columns:
            display_vz = display_vz[display_vz["je_nabytek"]]

        st.subheader(f"Smlouvy ({len(display_vz)})")

        show_vz_cols = [c for c in ["platce","predmet","hodnota_czk","datum",
                                     "dodavatel","odkaz","skola_priorita","skola_score"]
                        if c in display_vz.columns]

        st.dataframe(
            display_vz[show_vz_cols],
            use_container_width=True,
            hide_index=True,
            column_config={
                "hodnota_czk":    st.column_config.NumberColumn("Hodnota Kč", format="%,.0f"),
                "odkaz":          st.column_config.LinkColumn("Odkaz", display_text="🔗"),
                "skola_priorita": st.column_config.TextColumn("P. školy"),
                "skola_score":    st.column_config.NumberColumn("Skóre školy"),
            },
        )


# ══════════════════════════════════════════════════════════════
#  📊 ANALYTIKA
# ══════════════════════════════════════════════════════════════
elif nav == "📊 Analytika":
    page_header("📊 Analýza trhu",
                "Kdo dostává zakázky na školní nábytek? Tržní podíly · trend · příležitosti",
                accent="#10b981")

    col_load, _ = st.columns([2, 3])
    with col_load:
        do_analyze = st.button("🔄 Načíst/obnovit tržní data (posledních 3 roky)",
                               type="primary", use_container_width=True)

    if do_analyze:
        with st.spinner("Stahuji historická data smluv... (může trvat 1-2 min)"):
            try:
                from scrapers.analytics_scraper import fetch_market_smlouvy
                market_df = fetch_market_smlouvy(years_back=3)
                st.success(f"✅ Načteno {len(market_df)} smluv")
                st.cache_data.clear()
            except Exception as e:
                st.error(f"Chyba: {e}")

    market_df = load_market_data()

    if market_df.empty:
        st.info("Klikni **Načíst tržní data** pro stažení historických smluv.")
        st.stop()

    from scrapers.analytics_scraper import analyze_suppliers
    analysis = analyze_suppliers(market_df)

    if not analysis:
        st.warning("Analýza selhala.")
        st.stop()

    # ── KPI ───────────────────────────────────────────────────
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Smluv se školami",    analysis.get("total_contracts", 0))
    m2.metric("Celková hodnota",      f"{analysis.get('total_value_czk',0)/1e6:.1f} M Kč")
    m3.metric("Průměrná smlouva",     f"{analysis.get('avg_value_czk',0):,.0f} Kč")
    m4.metric("Aktivních škol",       analysis.get("active_schools", 0))

    st.divider()

    tab_supp, tab_trend, tab_detail = st.tabs(
        ["🏆 Top dodavatelé", "📈 Trend po letech", "🔍 Detail smluv"]
    )

    with tab_supp:
        top = analysis.get("top_suppliers", pd.DataFrame())
        if not top.empty:
            st.subheader("Kdo dostává nejvíce zakázek na školní nábytek?")

            top_display = top.head(15).copy()
            top_display["celkova_hodnota_m"] = (top_display["celkova_hodnota"] / 1_000_000).round(2)
            top_display["prumerna_hodnota_k"] = (top_display["prumerna_hodnota"] / 1_000).round(0)

            # Bar chart — počet zakázek
            fig1 = px.bar(
                top_display.head(15),
                x="pocet_zakazek",
                y="dodavatel",
                orientation="h",
                color="trzni_podil_pct",
                color_continuous_scale="Reds",
                labels={"pocet_zakazek": "Počet zakázek", "dodavatel": "",
                        "trzni_podil_pct": "Tržní podíl %"},
                title="Top dodavatelé — počet zakázek",
                height=500,
            )
            fig1.update_layout(yaxis={"categoryorder": "total ascending"})
            st.plotly_chart(fig1, use_container_width=True)

            # Pie chart — hodnota
            fig2 = px.pie(
                top_display.head(10),
                values="celkova_hodnota",
                names="dodavatel",
                title="Tržní podíl (hodnota smluv) — Top 10",
                hole=0.4,
            )
            st.plotly_chart(fig2, use_container_width=True)

            # Tabulka
            st.subheader("Detail top dodavatelů")
            st.dataframe(
                top_display[["dodavatel","pocet_zakazek","celkova_hodnota_m",
                              "prumerna_hodnota_k","trzni_podil_pct",
                              "prvni_zakazka","posledni_zakazka"]].rename(columns={
                    "dodavatel":          "Dodavatel",
                    "pocet_zakazek":      "Zakázek",
                    "celkova_hodnota_m":  "Celkem (M Kč)",
                    "prumerna_hodnota_k": "Průměr (tis. Kč)",
                    "trzni_podil_pct":    "Podíl %",
                    "prvni_zakazka":      "První",
                    "posledni_zakazka":   "Poslední",
                }),
                use_container_width=True,
                hide_index=True,
            )

    with tab_trend:
        trend = analysis.get("yearly_trend", pd.DataFrame())
        if not trend.empty:
            fig3 = px.bar(
                trend, x="rok", y="pocet",
                title="Počet smluv na školní nábytek po letech",
                labels={"rok": "Rok", "pocet": "Počet smluv"},
                color="hodnota",
                color_continuous_scale="Blues",
                text="pocet",
            )
            st.plotly_chart(fig3, use_container_width=True)

            fig4 = px.line(
                trend, x="rok", y="hodnota",
                title="Celková hodnota smluv po letech (Kč)",
                labels={"rok": "Rok", "hodnota": "Hodnota (Kč)"},
                markers=True,
            )
            st.plotly_chart(fig4, use_container_width=True)

    with tab_detail:
        raw = analysis.get("raw_df", pd.DataFrame())
        if not raw.empty:
            st.subheader(f"Všechny smlouvy ({len(raw)})")

            search = st.text_input("🔍 Hledat (dodavatel, škola, předmět...)")
            if search:
                mask = raw.apply(lambda r: search.lower() in str(r).lower(), axis=1)
                raw = raw[mask]

            show_raw_cols = [c for c in ["datum","platce","predmet","hodnota_czk","dodavatel"]
                             if c in raw.columns]
            st.dataframe(
                raw[show_raw_cols].sort_values("datum", ascending=False).head(500),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "hodnota_czk": st.column_config.NumberColumn("Hodnota Kč", format="%,.0f"),
                },
            )


# ══════════════════════════════════════════════════════════════
#  👥 CRM PIPELINE
# ══════════════════════════════════════════════════════════════
elif nav == "👥 CRM Pipeline":
    page_header("👥 CRM Pipeline",
                "Stav obchodních příležitostí · sleduj školy od prvního kontaktu po vyhranou zakázku",
                accent="#f59e0b")

    col_refresh, _ = st.columns([2, 3])
    with col_refresh:
        if st.button("🔄 Obnovit ze Sheets", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

    crm_df = load_crm()

    if crm_df.empty:
        st.info("CRM je prázdné. Oslovi první školy v sekci **🎯 Akce dnes**.")
        st.stop()

    # Pipeline stages
    STAGES = ["Nový", "Osloveno", "Reakce", "Nabídka", "Vyhráno", "Prohráno", "Odloženo"]
    STAGE_COLORS = {
        "Nový":     "#64748b",
        "Osloveno": "#3b82f6",
        "Reakce":   "#8b5cf6",
        "Nabídka":  "#f59e0b",
        "Vyhráno":  "#22c55e",
        "Prohráno": "#ef4444",
        "Odloženo": "#94a3b8",
    }

    # Metriky dle stavu — vizuální kanban pruh
    if "Stav pipeline" in crm_df.columns:
        stage_counts = crm_df["Stav pipeline"].value_counts()

        # Vizuální progress funnel
        total_active = sum(stage_counts.get(s, 0) for s in ["Nový","Osloveno","Reakce","Nabídka"])
        cols = st.columns(len(STAGES))
        for i, stage in enumerate(STAGES):
            cnt = int(stage_counts.get(stage, 0))
            color = STAGE_COLORS.get(stage, "#64748b")
            with cols[i]:
                st.markdown(
                    f'<div style="background:white;border:1px solid #e8edf2;border-radius:10px;'
                    f'padding:12px 8px;text-align:center;border-top:3px solid {color};">'
                    f'<div style="font-size:22px;font-weight:700;color:{color};">{cnt}</div>'
                    f'<div style="font-size:11px;color:#64748b;margin-top:2px;font-weight:500;">{stage}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

        st.divider()

        # Kanban pohled (simplifikovaný)
        selected_stage = st.selectbox("Zobrazit stav", ["Vše"] + STAGES)

        display_crm = crm_df if selected_stage == "Vše" else crm_df[
            crm_df["Stav pipeline"] == selected_stage
        ]

        st.subheader(f"Záznamy ({len(display_crm)})")
        st.dataframe(
            display_crm,
            use_container_width=True,
            hide_index=True,
        )

    else:
        st.dataframe(crm_df, use_container_width=True, hide_index=True)

    st.divider()
    st.markdown(
        "📝 Pro úpravu CRM dat přejdi přímo do "
        "[Google Sheets]"
        f"(https://docs.google.com/spreadsheets/d/1hlWlg9gYoUpept82xaHeoyOqEuhsIDMMKPe7v1O7Jsc/edit#gid=0)"
    )


# ══════════════════════════════════════════════════════════════
#  📄 NABÍDKY
# ══════════════════════════════════════════════════════════════
elif nav == "📄 Nabídky":
    page_header("📄 Generátor nabídek",
                "Vyber školu · přidej produkty z katalogu · nastav slevu → tisknutelná HTML/PDF nabídka",
                accent="#e74c3c")

    catalog = load_catalog()
    if not catalog:
        st.error(f"Katalog produktů nenalezen: `{CATALOG_JSON}`. Zkontroluj soubor.")
        st.stop()

    # Sestavíme flat dict produktů {id: produkt_dict}
    all_products: dict[str, dict] = {}
    for kat in catalog.get("kategorie", []):
        for p in kat.get("produkty", []):
            all_products[p["id"]] = {**p, "kategorie": kat["nazev"]}

    tab_nova, tab_historie = st.tabs(["✏️ Nová nabídka", "📚 Historie nabídek"])

    # ──────────────────────────────────────────────────────────
    with tab_nova:
        col_form, col_preview = st.columns([3, 2])

        # Inicializace session state pro košík
        if "nabidka_items" not in st.session_state:
            st.session_state.nabidka_items = []   # list of {id, nazev, popis, jednotka, mnozstvi, cena_kus}

        # ── LEVÝ sloupec: formulář ─────────────────────────────
        with col_form:

            # 1. Škola
            st.subheader("1. Škola / zákazník")
            skola_source = st.radio(
                "Zdroj", ["Ze seznamu škol", "Zadat ručně"],
                horizontal=True, label_visibility="collapsed",
            )

            skola_info = {}
            if skola_source == "Ze seznamu škol" and not schools_df.empty:
                skola_options = schools_df[["nazev", "obec", "ico", "email", "izo"]].dropna(
                    subset=["nazev"]
                ).drop_duplicates(subset=["nazev"])
                skola_labels = skola_options["nazev"] + " (" + skola_options["obec"].fillna("") + ")"
                idx = st.selectbox(
                    "Vyber školu", range(len(skola_labels)),
                    format_func=lambda i: skola_labels.iloc[i],
                    label_visibility="collapsed",
                )
                skola_row = skola_options.iloc[idx]
                skola_info = {
                    "nazev": str(skola_row.get("nazev", "")),
                    "obec":  str(skola_row.get("obec", "")),
                    "ico":   str(skola_row.get("ico", "") or ""),
                    "email": str(skola_row.get("email", "") or ""),
                    "izo":   str(skola_row.get("izo", "") or ""),
                }
                # Možnost přepsat email
                skola_info["email"] = st.text_input(
                    "Email zákazníka", value=skola_info["email"],
                    placeholder="reditel@zsexample.cz",
                )
            else:
                skola_info["nazev"] = st.text_input("Název školy / zákazníka", placeholder="ZŠ Příklad")
                skola_info["obec"]  = st.text_input("Obec", placeholder="Praha")
                skola_info["ico"]   = st.text_input("IČO (volitelné)")
                skola_info["email"] = st.text_input("Email", placeholder="reditel@zsexample.cz")
                skola_info["izo"]   = ""

            st.divider()

            # 2. Podmínky nabídky
            st.subheader("2. Podmínky")
            cond_col1, cond_col2 = st.columns(2)
            with cond_col1:
                sleva_pct = st.number_input("Sleva (%)", min_value=0.0, max_value=50.0,
                                            value=0.0, step=1.0, format="%.0f")
            with cond_col2:
                platnost_dni = st.selectbox("Platnost", [30, 45, 60, 90],
                                            format_func=lambda d: f"{d} dní")
            poznamka = st.text_area("Poznámka k nabídce (volitelně)", height=70,
                                    placeholder="Doprava v ceně pro objednávky nad 50 000 Kč...")

            st.divider()

            # 3. Produkty — přidávání
            st.subheader("3. Produkty")

            # Filtr kategorie
            kategorie_list = ["Vše"] + [k["nazev"] for k in catalog.get("kategorie", [])]
            sel_kat = st.selectbox("Kategorie", kategorie_list, label_visibility="collapsed")

            if sel_kat == "Vše":
                filtered_products = list(all_products.values())
            else:
                filtered_products = [p for p in all_products.values() if p["kategorie"] == sel_kat]

            prod_labels = [f"{p['id']} — {p['nazev']} ({p['cena_bez_dph']:,} Kč/{p['jednotka']})"
                           for p in filtered_products]
            if not prod_labels:
                st.warning("Žádné produkty v kategorii.")
            else:
                sel_prod_idx = st.selectbox(
                    "Vyber produkt", range(len(prod_labels)),
                    format_func=lambda i: prod_labels[i],
                    label_visibility="collapsed",
                )
                selected_product = filtered_products[sel_prod_idx]

                add_col1, add_col2, add_col3 = st.columns([2, 2, 1])
                with add_col1:
                    mnozstvi = st.number_input(
                        f"Množství ({selected_product['jednotka']})",
                        min_value=selected_product.get("min_mnozstvi", 1),
                        value=max(1, selected_product.get("min_mnozstvi", 1)),
                        step=1,
                    )
                with add_col2:
                    cena_override = st.number_input(
                        "Cena/ks bez DPH (Kč)",
                        min_value=0,
                        value=int(selected_product["cena_bez_dph"]),
                        step=100,
                    )
                with add_col3:
                    st.write("")
                    st.write("")
                    if st.button("➕ Přidat", use_container_width=True, type="primary"):
                        # Zkontroluj duplicitu — pokud stejné ID, jen navýš množství
                        existing = next(
                            (i for i, x in enumerate(st.session_state.nabidka_items)
                             if x["id"] == selected_product["id"] and x["cena_kus"] == cena_override),
                            None,
                        )
                        if existing is not None:
                            st.session_state.nabidka_items[existing]["mnozstvi"] += mnozstvi
                            st.session_state.nabidka_items[existing]["cena_radek"] = (
                                st.session_state.nabidka_items[existing]["mnozstvi"]
                                * st.session_state.nabidka_items[existing]["cena_kus"]
                            )
                        else:
                            st.session_state.nabidka_items.append({
                                "id":       selected_product["id"],
                                "nazev":    selected_product["nazev"],
                                "popis":    selected_product.get("popis", ""),
                                "jednotka": selected_product.get("jednotka", "ks"),
                                "mnozstvi": mnozstvi,
                                "cena_kus": cena_override,
                                "cena_radek": mnozstvi * cena_override,
                            })
                        st.rerun()

            # Košík — editovatelná tabulka položek
            st.divider()
            st.markdown("**Položky nabídky:**")

            if not st.session_state.nabidka_items:
                st.info("Zatím žádné položky — přidej produkty výše.")
            else:
                to_remove = None
                for idx_item, item in enumerate(st.session_state.nabidka_items):
                    ic1, ic2, ic3, ic4 = st.columns([3, 1, 1, 0.5])
                    with ic1:
                        st.markdown(f"**{item['nazev']}**")
                        st.caption(f"{item['id']} · {item['popis'][:60]}")
                    with ic2:
                        new_mnoz = st.number_input(
                            "ks", value=item["mnozstvi"], min_value=1,
                            key=f"mnoz_{idx_item}", label_visibility="collapsed",
                        )
                        if new_mnoz != item["mnozstvi"]:
                            st.session_state.nabidka_items[idx_item]["mnozstvi"] = new_mnoz
                            st.session_state.nabidka_items[idx_item]["cena_radek"] = new_mnoz * item["cena_kus"]
                            st.rerun()
                    with ic3:
                        st.markdown(
                            f'<div style="text-align:right;padding-top:8px;">'
                            f'<b>{item["cena_radek"]:,.0f} Kč</b><br>'
                            f'<span style="color:#888;font-size:11px;">'
                            f'{item["cena_kus"]:,} × {item["mnozstvi"]} {item["jednotka"]}</span>'
                            f'</div>',
                            unsafe_allow_html=True,
                        )
                    with ic4:
                        if st.button("🗑️", key=f"rm_{idx_item}", help="Odebrat položku"):
                            to_remove = idx_item
                if to_remove is not None:
                    st.session_state.nabidka_items.pop(to_remove)
                    st.rerun()

                st.divider()

                # Reset košíku
                if st.button("🗑️ Vymazat celý košík", use_container_width=False):
                    st.session_state.nabidka_items = []
                    st.rerun()

        # ── PRAVÝ sloupec: cenový souhrn + akce ───────────────
        with col_preview:
            st.subheader("Souhrn")

            items = st.session_state.nabidka_items
            celkem_bez = sum(p["cena_radek"] for p in items)
            sleva_czk  = celkem_bez * sleva_pct / 100
            zaklad_dph = celkem_bez - sleva_czk
            dph_czk    = zaklad_dph * 0.21
            celkem_s   = zaklad_dph + dph_czk

            if items:
                # Škola info box
                if skola_info.get("nazev"):
                    st.markdown(
                        f'<div style="background:#f8f9fa;border-left:4px solid #e74c3c;'
                        f'padding:10px 14px;border-radius:4px;margin-bottom:12px;">'
                        f'<b>{skola_info["nazev"]}</b><br>'
                        f'<span style="color:#666;">{skola_info.get("obec","")}</span>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )

                # Cenový souhrn
                st.markdown(
                    f"""<div style="background:#fff;border:1px solid #ddd;border-radius:8px;padding:16px;">
                    <table style="width:100%;border:none;font-size:14px;">
                    <tr><td>Celkem bez DPH:</td><td style="text-align:right;">{celkem_bez:,.0f} Kč</td></tr>
                    {"<tr><td style='color:#e67e22;'>Sleva " + f"{sleva_pct:.0f}" + " %:</td><td style='text-align:right;color:#e67e22;'>−" + f"{sleva_czk:,.0f}" + " Kč</td></tr>" if sleva_pct > 0 else ""}
                    <tr><td>Základ DPH:</td><td style="text-align:right;">{zaklad_dph:,.0f} Kč</td></tr>
                    <tr><td>DPH 21 %:</td><td style="text-align:right;">{dph_czk:,.0f} Kč</td></tr>
                    <tr style="border-top:2px solid #e74c3c;">
                      <td><b style="font-size:15px;">CELKEM:</b></td>
                      <td style="text-align:right;"><b style="font-size:18px;color:#e74c3c;">{celkem_s:,.0f} Kč</b></td>
                    </tr>
                    </table></div>""",
                    unsafe_allow_html=True,
                )

                st.markdown("")

                # Počet položek
                total_ks = sum(p["mnozstvi"] for p in items)
                st.caption(f"📦 {len(items)} druhů · {total_ks} ks celkem · platnost {platnost_dni} dní")

                st.divider()

                # Tlačítka akcí
                if not skola_info.get("nazev"):
                    st.warning("Vyplň název školy.")
                else:
                    cislo = next_quote_number()

                    # Generovat HTML
                    if st.button("📄 Generovat nabídku (HTML)", type="primary",
                                 use_container_width=True):
                        html = generate_quote_html(
                            cislo=cislo,
                            skola=skola_info,
                            polozky=items,
                            sleva_pct=sleva_pct,
                            platnost_dni=platnost_dni,
                            poznamka=poznamka,
                        )
                        st.download_button(
                            label=f"⬇️ Stáhnout {cislo}.html (otevřít v prohlížeči → Ctrl+P → PDF)",
                            data=html.encode("utf-8"),
                            file_name=f"{cislo}.html",
                            mime="text/html",
                            use_container_width=True,
                        )
                        st.success(f"✅ Nabídka {cislo} připravena ke stažení!")

                    # Uložit do evidence
                    if st.button("💾 Uložit do evidence", use_container_width=True):
                        record = {
                            "cislo":          cislo,
                            "datum":          datetime.now().strftime("%Y-%m-%d"),
                            "platnost_do":    (datetime.now() + timedelta(days=platnost_dni)).strftime("%Y-%m-%d"),
                            "skola_nazev":    skola_info.get("nazev", ""),
                            "skola_ico":      skola_info.get("ico", ""),
                            "skola_email":    skola_info.get("email", ""),
                            "skola_obec":     skola_info.get("obec", ""),
                            "polozky_json":   json.dumps(items, ensure_ascii=False),
                            "celkem_bez_dph": round(celkem_bez, 2),
                            "dph":            round(dph_czk, 2),
                            "celkem_s_dph":   round(celkem_s, 2),
                            "sleva_pct":      sleva_pct,
                            "stav":           "Připravena",
                            "poznamka":       poznamka,
                        }
                        save_quote(record)
                        st.success(f"✅ Uloženo jako {cislo}")
                        # Resetuj košík
                        st.session_state.nabidka_items = []
                        st.cache_data.clear()
                        st.rerun()

                    # Mailto s odkazem na nabídku
                    if skola_info.get("email"):
                        subject = f"Cenová nabídka {cislo} — Brezka školní nábytek"
                        body = (
                            f"Dobrý den,\n\nv příloze zasílám cenovou nabídku č. {cislo} "
                            f"na školní nábytek pro {skola_info['nazev']}.\n\n"
                            f"Celková cena s DPH: {celkem_s:,.0f} Kč\n"
                            f"Platnost nabídky: {platnost_dni} dní\n\n"
                            f"V případě dotazů jsem k dispozici.\n\n"
                            f"S pozdravem,\nMatyas Olmr\nBrezka — Nupaky"
                        )
                        mailto = make_mailto(skola_info["email"], subject, body)
                        st.link_button("📧 Napsat průvodní email", mailto, use_container_width=True)

            else:
                st.info("👈 Přidej produkty z levého panelu.")

                # Rychlé tipy
                st.markdown("**Nejčastější sady:**")
                quick_sets = [
                    ("🏫 Třída 25 žáků", ["LAV-2M", "ZID-5"], [13, 25]),
                    ("🪑 Jídelna 40 míst", ["STL-JID", "ZID-JID"], [10, 40]),
                    ("📚 Chodba 6 skříněk", ["SAT-SKR"], [6]),
                ]
                for label, ids, amounts in quick_sets:
                    if st.button(label, use_container_width=True):
                        st.session_state.nabidka_items = []
                        for pid, amt in zip(ids, amounts):
                            if pid in all_products:
                                p = all_products[pid]
                                st.session_state.nabidka_items.append({
                                    "id":       p["id"],
                                    "nazev":    p["nazev"],
                                    "popis":    p.get("popis", ""),
                                    "jednotka": p.get("jednotka", "ks"),
                                    "mnozstvi": amt,
                                    "cena_kus": p["cena_bez_dph"],
                                    "cena_radek": amt * p["cena_bez_dph"],
                                })
                        st.rerun()

    # ──────────────────────────────────────────────────────────
    with tab_historie:
        st.subheader("Historie nabídek")

        quotes_df = load_quotes()

        if quotes_df.empty:
            st.markdown(
                '<div style="text-align:center;padding:48px 20px;color:#94a3b8;">'
                '<div style="font-size:48px;">📄</div>'
                '<div style="font-size:16px;margin-top:12px;font-weight:600;color:#64748b;">'
                'Zatím žádné uložené nabídky</div>'
                '<div style="font-size:13px;margin-top:6px;">Vytvoř první nabídku v záložce ✏️ Nová nabídka</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        else:
            # ── Metriky ─────────────────────────────────────────
            hm1, hm2, hm3, hm4, hm5 = st.columns(5)
            hm1.metric("Celkem", len(quotes_df))

            if "stav" in quotes_df.columns:
                open_q  = quotes_df["stav"].isin(["Připravena","Odesláno","Reakce"]).sum()
                won     = (quotes_df["stav"] == "Vyhráno").sum()
                lost    = (quotes_df["stav"] == "Prohráno").sum()
                hm2.metric("Otevřené", int(open_q))
                hm3.metric("Vyhráno ✅", int(won))
                hm4.metric("Prohráno ❌", int(lost))

            if "celkem_s_dph" in quotes_df.columns:
                vals = pd.to_numeric(quotes_df["celkem_s_dph"], errors="coerce")
                won_mask = quotes_df["stav"] == "Vyhráno" if "stav" in quotes_df.columns else pd.Series(False, index=quotes_df.index)
                won_val  = vals[won_mask].sum()
                hm5.metric("Vyhráno Kč", f"{won_val:,.0f}")

            st.divider()

            # Filtr stavu
            if "stav" in quotes_df.columns:
                stavy = ["Vše"] + quotes_df["stav"].dropna().unique().tolist()
                sel_stav = st.selectbox("Filtr stavu", stavy)
                if sel_stav != "Vše":
                    quotes_df = quotes_df[quotes_df["stav"] == sel_stav]

            # Tabulka
            show_q_cols = [c for c in [
                "cislo", "datum", "skola_nazev", "skola_obec",
                "celkem_s_dph", "sleva_pct", "stav", "platnost_do", "poznamka"
            ] if c in quotes_df.columns]

            edited = st.data_editor(
                quotes_df[show_q_cols].sort_values("datum", ascending=False),
                use_container_width=True,
                hide_index=True,
                column_config={
                    "cislo":         st.column_config.TextColumn("Číslo", width="small"),
                    "datum":         st.column_config.TextColumn("Datum", width="small"),
                    "skola_nazev":   st.column_config.TextColumn("Škola"),
                    "skola_obec":    st.column_config.TextColumn("Obec", width="small"),
                    "celkem_s_dph":  st.column_config.NumberColumn("Celkem Kč", format="%,.0f"),
                    "sleva_pct":     st.column_config.NumberColumn("Sleva %", format="%.0f"),
                    "stav":          st.column_config.SelectboxColumn(
                        "Stav", width="small",
                        options=["Připravena", "Odesláno", "Reakce", "Přijato",
                                 "Vyhráno", "Prohráno", "Odloženo"],
                    ),
                    "platnost_do":   st.column_config.TextColumn("Platnost do", width="small"),
                    "poznamka":      st.column_config.TextColumn("Poznámka"),
                },
                num_rows="fixed",
            )

            if st.button("💾 Uložit změny stavů", use_container_width=False):
                # Merge editovaných dat zpět do plného DF
                full_df = load_quotes()
                for col in show_q_cols:
                    if col in edited.columns and col in full_df.columns:
                        # Updatuj podle čísla nabídky
                        merge = edited.set_index("cislo")[col] if "cislo" in edited.columns else None
                        if merge is not None:
                            full_df = full_df.set_index("cislo")
                            full_df.update(merge.rename(col))
                            full_df = full_df.reset_index()
                full_df.to_csv(NABIDKY_CSV, index=False, encoding="utf-8-sig")
                st.success("✅ Uloženo!")
                st.rerun()

            # Regenerovat nabídku z historie
            st.divider()
            st.markdown("**Regenerovat nabídku:**")
            regen_cislo = st.selectbox(
                "Vybrat nabídku k regeneraci",
                quotes_df["cislo"].tolist() if "cislo" in quotes_df.columns else [],
                label_visibility="collapsed",
            )
            if regen_cislo and st.button("📄 Regenerovat HTML", use_container_width=False):
                q_row = load_quotes()
                q_row = q_row[q_row["cislo"] == regen_cislo]
                if not q_row.empty:
                    q = q_row.iloc[0]
                    try:
                        polozky_regen = json.loads(str(q.get("polozky_json", "[]")))
                        skola_regen = {
                            "nazev": str(q.get("skola_nazev", "")),
                            "obec":  str(q.get("skola_obec", "")),
                            "ico":   str(q.get("skola_ico", "")),
                            "email": str(q.get("skola_email", "")),
                        }
                        datum_vytvoreni = str(q.get("datum", ""))
                        platnost_do     = str(q.get("platnost_do", ""))
                        # Platnost ve dnech (zpětný výpočet)
                        try:
                            dni_regen = (
                                datetime.strptime(platnost_do, "%Y-%m-%d")
                                - datetime.strptime(datum_vytvoreni, "%Y-%m-%d")
                            ).days
                        except Exception:
                            dni_regen = 30

                        html_regen = generate_quote_html(
                            cislo=regen_cislo,
                            skola=skola_regen,
                            polozky=polozky_regen,
                            sleva_pct=float(q.get("sleva_pct", 0) or 0),
                            platnost_dni=dni_regen,
                            poznamka=str(q.get("poznamka", "") or ""),
                        )
                        st.download_button(
                            label=f"⬇️ Stáhnout {regen_cislo}.html",
                            data=html_regen.encode("utf-8"),
                            file_name=f"{regen_cislo}.html",
                            mime="text/html",
                        )
                    except Exception as e:
                        st.error(f"Chyba při regeneraci: {e}")
