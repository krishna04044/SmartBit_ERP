import streamlit as st
import streamlit.components.v1 as components
import os
import base64

from database.db import init_db
from utils.auth import get_current_user, render_login, logout_user, ROLES

from modules.dashboard import render_dashboard
from modules.products import render_products
from modules.inventory import render_inventory
from modules.customers import render_customers
from modules.suppliers import render_suppliers
from modules.sales import render_sales
from modules.purchases import render_purchases
from modules.expenses import render_expenses
from modules.finance import render_finance
from modules.employees import render_employees
from modules.users import render_users
from modules.reports import render_reports

# ----------------- PAGE CONFIGURATION -----------------
st.set_page_config(
    page_title="SmartBiz ERP — Precision Management",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database tables and seed data
init_db()

# Load logo asset
LOGO_PATH = os.path.join(os.path.dirname(__file__), 'assets', 'logo.jpg')
if not os.path.exists(LOGO_PATH):
    LOGO_PATH = os.path.join(os.path.dirname(__file__), 'static', 'logo.jpg')

LOGO_B64 = ""
if os.path.exists(LOGO_PATH):
    with open(LOGO_PATH, "rb") as _f:
        LOGO_B64 = base64.b64encode(_f.read()).decode('utf-8')

# Theme State Management (Default: Obsidian Rail Precision Dark)
if 'theme_mode' not in st.session_state:
    st.session_state.theme_mode = 'dark'

is_dark = (st.session_state.theme_mode == 'dark')

# ==================== THEME INJECTION (OBSIDIAN RAIL / LIMEPRESS) ====================
if is_dark:
    # ── OBSIDIAN RAIL (PRECISION DARK) ──
    st.html('''
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Geist+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
    /* ===== OBSIDIAN RAIL TOKENS ===== */
    :root {
      --color-primary:   #f5f6f7;
      --color-secondary: #8b8e93;
      --color-accent:    #5fe3b1;
      --color-neutral:   #1a1c1e;
      --color-surface:   #0c0d0f;
      --color-hairline:  rgba(245,246,247,0.08);
      --font-display:    'Inter', sans-serif;
      --font-body:       'Inter', sans-serif;
      --font-mono:       'Geist Mono', monospace;
      --radius-sm:       4px;
      --radius-md:       6px;
      --radius-lg:       8px;
    }

    * {
      font-feature-settings: "calt" 1;
      box-sizing: border-box;
    }

    html, body, [class*="css"], .stApp {
      background-color: #0c0d0f !important;
      color: #f5f6f7 !important;
      font-family: 'Inter', sans-serif !important;
      font-weight: 400 !important;
      -webkit-font-smoothing: antialiased;
    }

    .main, .stMainBlockContainer, .block-container,
    [data-testid="stMain"], [data-testid="stAppViewContainer"] > section:first-child {
      background-color: #0c0d0f !important;
      color: #f5f6f7 !important;
      padding-top: 1.5rem !important;
    }

    /* ── Streamlit Header Bar ── */
    header[data-testid="stHeader"] {
      background: transparent !important;
      z-index: 100 !important;
    }

    /* ── Hide Deploy Button ── */
    [data-testid="stAppDeployButton"],
    .stDeployButton,
    div:has(> [data-testid="stAppDeployButton"]),
    div[data-testid="stToolbar"] button:first-child:not([data-testid="stMainMenu"]) {
      display: none !important;
      visibility: hidden !important;
      opacity: 0 !important;
      pointer-events: none !important;
    }

    /* ── Typography & Prose ── */
    p, span, small, li, div, b, strong, em, .stMarkdown, .stMarkdown p {
      color: #f5f6f7;
      font-family: 'Inter', sans-serif;
    }
    .stCaption, [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p, .stCaption p {
      color: #8b8e93 !important;
      font-family: 'Inter', sans-serif !important;
      font-size: 0.85rem !important;
    }

    /* ── Headlines ── */
    h1, [data-testid="stHeadingWithActionElements"] h1, h1 * {
      font-family: 'Inter', sans-serif !important;
      color: #f5f6f7 !important;
      font-weight: 600 !important;
      line-height: 1.12 !important;
      letter-spacing: -0.025em !important;
      font-size: 2.25rem !important;
      margin-bottom: 0.3rem !important;
    }

    h2, [data-testid="stHeadingWithActionElements"] h2, h2 * {
      font-family: 'Inter', sans-serif !important;
      color: #f5f6f7 !important;
      font-weight: 600 !important;
      line-height: 1.25 !important;
      letter-spacing: -0.012em !important;
      font-size: 1.45rem !important;
      margin-top: 1.2rem !important;
      margin-bottom: 0.4rem !important;
    }

    h3, [data-testid="stHeadingWithActionElements"] h3, h3 * {
      font-family: 'Inter', sans-serif !important;
      color: #f5f6f7 !important;
      font-weight: 600 !important;
      line-height: 1.3 !important;
      letter-spacing: -0.01em !important;
      font-size: 1.2rem !important;
    }

    h4, h5, h6, h4 *, h5 *, h6 * {
      font-family: 'Inter', sans-serif !important;
      color: #f5f6f7 !important;
      font-weight: 600 !important;
    }

    /* ── Metric Cards ── */
    div[data-testid="metric-container"],
    [data-testid="stMetric"] {
      background: #1a1c1e !important;
      border: 1px solid rgba(245,246,247,0.08) !important;
      box-shadow: rgba(0,0,0,0.20) 0 1px 2px !important;
      border-radius: 8px !important;
      padding: 16px 20px !important;
      transition: transform 180ms ease, border-color 180ms ease !important;
    }
    div[data-testid="metric-container"]:hover,
    [data-testid="stMetric"]:hover {
      border-color: rgba(245,246,247,0.16) !important;
      transform: translateY(-1px) !important;
    }
    [data-testid="stMetricLabel"] > div,
    [data-testid="stMetricLabel"] label,
    [data-testid="stMetricLabel"] p,
    div[data-testid="metric-container"] label {
      color: #8b8e93 !important;
      font-size: 0.6875rem !important;
      text-transform: uppercase !important;
      letter-spacing: 0.06em !important;
      font-family: 'Geist Mono', monospace !important;
      font-weight: 500 !important;
    }
    [data-testid="stMetricValue"] > div,
    [data-testid="stMetricValue"] p,
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
      color: #f5f6f7 !important;
      font-family: 'Geist Mono', monospace !important;
      font-size: 1.75rem !important;
      line-height: 1.0 !important;
      font-weight: 600 !important;
      font-variant-numeric: tabular-nums !important;
      margin-top: 6px !important;
      margin-bottom: 4px !important;
    }
    [data-testid="stMetricDelta"] {
      font-family: 'Geist Mono', monospace !important;
      font-size: 0.75rem !important;
      font-variant-numeric: tabular-nums !important;
      font-weight: 500 !important;
    }

    /* ── Form Containers ── */
    [data-testid="stForm"] {
      background: #1a1c1e !important;
      border: 1px solid rgba(245,246,247,0.08) !important;
      border-radius: 8px !important;
      padding: 24px !important;
      box-shadow: rgba(0,0,0,0.20) 0 1px 2px !important;
    }

    /* ── Form Labels & Widget Headings ── */
    label,
    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] *,
    label[data-testid="stWidgetLabel"] p,
    label[data-testid="stWidgetLabel"] span,
    label[data-testid="stWidgetLabel"] div {
      color: #f5f6f7 !important;
      font-family: 'Inter', sans-serif !important;
      font-size: 0.875rem !important;
      font-weight: 500 !important;
      letter-spacing: -0.005em !important;
    }

    /* ── Radio & Checkbox Buttons ── */
    [data-testid="stRadio"] label,
    [data-testid="stRadio"] label *,
    [data-testid="stRadio"] div[role="radiogroup"] label *,
    [data-testid="stCheckbox"] label,
    [data-testid="stCheckbox"] label *,
    [data-testid="stCheckbox"] span,
    [data-testid="stCheckbox"] p {
      color: #f5f6f7 !important;
      font-family: 'Inter', sans-serif !important;
      font-size: 0.875rem !important;
      font-weight: 400 !important;
    }
    [data-testid="stRadio"] input:checked + div {
      border-color: #5fe3b1 !important;
      background-color: #5fe3b1 !important;
    }

    /* ── Form Inputs & Textareas ── */
    input[type="text"], input[type="password"], input[type="email"],
    input[type="number"], textarea, [data-baseweb="input"] input {
      background-color: #0c0d0f !important;
      border: 1px solid rgba(245,246,247,0.14) !important;
      border-radius: 6px !important;
      color: #f5f6f7 !important;
      font-family: 'Inter', sans-serif !important;
      font-size: 0.875rem !important;
      padding: 9px 12px !important;
    }
    input:focus, textarea:focus, [data-baseweb="input"]:focus-within {
      border-color: #5fe3b1 !important;
      box-shadow: 0 0 0 3px rgba(95,227,177,0.15) !important;
      outline: none !important;
    }
    ::placeholder,
    input::placeholder,
    textarea::placeholder {
      color: #8b8e93 !important;
      opacity: 0.85 !important;
      font-family: 'Inter', sans-serif !important;
    }

    /* ── Number Input Controls ── */
    [data-testid="stNumberInput"] input {
      font-family: 'Geist Mono', monospace !important;
      font-variant-numeric: tabular-nums !important;
      color: #f5f6f7 !important;
    }
    [data-testid="stNumberInput"] button {
      background-color: #1a1c1e !important;
      border: 1px solid rgba(245,246,247,0.14) !important;
      color: #f5f6f7 !important;
    }
    [data-testid="stNumberInput"] button:hover {
      background-color: #24272a !important;
      border-color: rgba(95,227,177,0.4) !important;
    }
    [data-testid="stNumberInput"] button svg {
      fill: #f5f6f7 !important;
    }

    /* ── Selectbox ── */
    [data-baseweb="select"] > div,
    [data-baseweb="select"] {
      background-color: #0c0d0f !important;
      border: 1px solid rgba(245,246,247,0.14) !important;
      border-radius: 6px !important;
    }
    [data-baseweb="select"] span,
    [data-baseweb="select"] div,
    [data-baseweb="select"] input {
      color: #f5f6f7 !important;
      font-family: 'Inter', sans-serif !important;
    }
    [data-baseweb="popover"], [data-baseweb="menu"] {
      background-color: #1a1c1e !important;
      border-radius: 8px !important;
      border: 1px solid rgba(245,246,247,0.14) !important;
    }
    [data-baseweb="option"], [data-baseweb="option"] * {
      background-color: #1a1c1e !important;
      color: #f5f6f7 !important;
      font-size: 0.85rem !important;
    }
    [data-baseweb="option"]:hover, [data-baseweb="option"]:hover * {
      background-color: rgba(95,227,177,0.12) !important;
      color: #5fe3b1 !important;
    }

    /* ── Primary Action Buttons ── */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"],
    .stFormSubmitButton > button {
      background-color: #5fe3b1 !important;
      border: 1px solid #5fe3b1 !important;
      border-radius: 6px !important;
      font-family: 'Inter', sans-serif !important;
      font-weight: 600 !important;
      font-size: 0.8125rem !important;
      padding: 9px 18px !important;
      box-shadow: 0 1px 3px rgba(0,0,0,0.3) !important;
      transition: all 180ms cubic-bezier(0.32, 0.72, 0, 1) !important;
    }
    .stButton > button[kind="primary"] *,
    .stButton > button[data-testid="stBaseButton-primary"] *,
    .stFormSubmitButton > button * {
      color: #0c0d0f !important;
      font-family: 'Inter', sans-serif !important;
      font-weight: 600 !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="stBaseButton-primary"]:hover,
    .stFormSubmitButton > button:hover {
      background-color: #72ebb9 !important;
      box-shadow: 0 0 20px -4px rgba(95,227,177,0.5) !important;
    }

    /* ── Secondary & Regular Buttons ── */
    .stButton > button[kind="secondary"],
    .stButton > button[data-testid="stBaseButton-secondary"],
    .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not(.stFormSubmitButton button) {
      background-color: #1a1c1e !important;
      border: 1px solid rgba(245,246,247,0.12) !important;
      border-radius: 6px !important;
      font-family: 'Inter', sans-serif !important;
      font-weight: 500 !important;
      font-size: 0.8125rem !important;
      padding: 9px 18px !important;
      transition: all 180ms ease !important;
    }
    .stButton > button[kind="secondary"] *,
    .stButton > button[data-testid="stBaseButton-secondary"] *,
    .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not(.stFormSubmitButton button) * {
      color: #f5f6f7 !important;
      font-family: 'Inter', sans-serif !important;
      font-weight: 500 !important;
    }
    .stButton > button[kind="secondary"]:hover,
    .stButton > button[data-testid="stBaseButton-secondary"]:hover,
    .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not(.stFormSubmitButton button):hover {
      background-color: #24272a !important;
      border-color: rgba(95,227,177,0.4) !important;
    }
    .stButton > button[kind="secondary"]:hover *,
    .stButton > button[data-testid="stBaseButton-secondary"]:hover *,
    .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not(.stFormSubmitButton button):hover * {
      color: #5fe3b1 !important;
    }

    /* ── Outline & Download Buttons ── */
    [data-testid="stDownloadButton"] > button {
      background: transparent !important;
      border: 1px solid rgba(245,246,247,0.14) !important;
      border-radius: 6px !important;
      padding: 9px 18px !important;
      font-family: 'Inter', sans-serif !important;
      font-weight: 500 !important;
      font-size: 0.8125rem !important;
      transition: all 180ms ease !important;
    }
    [data-testid="stDownloadButton"] > button * {
      color: #f5f6f7 !important;
    }
    [data-testid="stDownloadButton"] > button:hover {
      border-color: rgba(245,246,247,0.3) !important;
      background: rgba(245,246,247,0.04) !important;
    }

    /* ── Dataframes ── */
    [data-testid="stDataFrame"] {
      border: 1px solid rgba(245,246,247,0.08) !important;
      box-shadow: rgba(0,0,0,0.20) 0 1px 2px !important;
      border-radius: 8px !important;
      overflow: hidden !important;
      background: #1a1c1e !important;
    }
    [data-testid="stDataFrame"] th {
      background: #141517 !important;
      color: #8b8e93 !important;
      font-family: 'Geist Mono', monospace !important;
      font-size: 0.72rem !important;
      font-weight: 600 !important;
      text-transform: uppercase !important;
      letter-spacing: 0.06em !important;
    }
    [data-testid="stDataFrame"] td {
      color: #f5f6f7 !important;
      font-family: 'Geist Mono', monospace !important;
      font-size: 0.8125rem !important;
      font-variant-numeric: tabular-nums !important;
    }

    /* ── Expanders ── */
    details, [data-testid="stExpander"] {
      background: #1a1c1e !important;
      border: 1px solid rgba(245,246,247,0.08) !important;
      box-shadow: rgba(0,0,0,0.20) 0 1px 2px !important;
      border-radius: 8px !important;
      padding: 8px 16px !important;
    }
    details summary, [data-testid="stExpander"] summary, details summary * {
      color: #f5f6f7 !important;
      font-family: 'Inter', sans-serif !important;
      font-weight: 600 !important;
      font-size: 0.95rem !important;
    }

    /* ── Alerts ── */
    [data-testid="stAlert"], div[role="alert"] {
      border-radius: 8px !important;
      border: 1px solid rgba(245,246,247,0.08) !important;
      border-left: 3px solid #5fe3b1 !important;
      background: #1a1c1e !important;
    }
    [data-testid="stAlert"] *, div[role="alert"] * {
      color: #f5f6f7 !important;
      font-family: 'Inter', sans-serif !important;
    }

    /* ── Obsidian Underline Tabs ── */
    [data-baseweb="tab-list"] {
      background: transparent !important;
      border-bottom: 1px solid rgba(245,246,247,0.08) !important;
      border-radius: 0 !important;
      padding: 0 !important;
      gap: 16px !important;
      margin-bottom: 16px !important;
    }
    [data-baseweb="tab"] {
      background: transparent !important;
      border: none !important;
      border-bottom: 2px solid transparent !important;
      border-radius: 0 !important;
      padding: 8px 4px !important;
    }
    [data-baseweb="tab"], [data-baseweb="tab"] * {
      color: #8b8e93 !important;
      font-family: 'Inter', sans-serif !important;
      font-weight: 500 !important;
      font-size: 0.875rem !important;
    }
    [data-baseweb="tab"]:hover, [data-baseweb="tab"]:hover * {
      color: #f5f6f7 !important;
    }
    [aria-selected="true"][data-baseweb="tab"] {
      background: transparent !important;
      border-bottom: 2px solid #5fe3b1 !important;
      box-shadow: none !important;
    }
    [aria-selected="true"][data-baseweb="tab"],
    [aria-selected="true"][data-baseweb="tab"] * {
      color: #f5f6f7 !important;
      font-weight: 600 !important;
    }

    /* ── Sidebar ── */
    section[data-testid="stSidebar"],
    [data-testid="stSidebar"] {
      background-color: #0c0d0f !important;
      border-right: 1px solid rgba(245,246,247,0.08) !important;
    }

    .nav-header {
      color: #8b8e93;
      font-family: 'Geist Mono', monospace;
      font-size: 0.68rem;
      font-weight: 600;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      margin-top: 8px;
      margin-bottom: 10px;
      padding-left: 6px;
    }

    section[data-testid="stSidebar"] .stButton {
      margin-bottom: 4px !important;
      width: 100% !important;
    }

    section[data-testid="stSidebar"] .stButton > button {
      width: 100% !important;
      display: flex !important;
      justify-content: flex-start !important;
      align-items: center !important;
      text-align: left !important;
      padding: 8px 14px !important;
      border-radius: 6px !important;
    }

    /* Inactive Sidebar Nav Items */
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"],
    section[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"],
    section[data-testid="stSidebar"] .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not(#sidebar_logout_btn) {
      background-color: #1a1c1e !important;
      border: 1px solid rgba(245,246,247,0.08) !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"] *,
    section[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"] *,
    section[data-testid="stSidebar"] .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not(#sidebar_logout_btn) * {
      color: #f5f6f7 !important;
      font-family: 'Inter', sans-serif !important;
      font-weight: 500 !important;
      font-size: 0.85rem !important;
      justify-content: flex-start !important;
      text-align: left !important;
    }

    section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover,
    section[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"]:hover,
    section[data-testid="stSidebar"] .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not(#sidebar_logout_btn):hover {
      background-color: #24272a !important;
      border-color: rgba(95,227,177,0.3) !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover *,
    section[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"]:hover *,
    section[data-testid="stSidebar"] .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not(#sidebar_logout_btn):hover * {
      color: #5fe3b1 !important;
    }

    /* Active Sidebar Nav Item */
    section[data-testid="stSidebar"] .stButton > button[kind="primary"],
    section[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] {
      background-color: #5fe3b1 !important;
      border: 1px solid #5fe3b1 !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] *,
    section[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] * {
      color: #0c0d0f !important;
      font-family: 'Inter', sans-serif !important;
      font-weight: 600 !important;
      font-size: 0.85rem !important;
      justify-content: flex-start !important;
      text-align: left !important;
    }

    /* Sign Out button */
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:last-child .stButton > button {
      background-color: transparent !important;
      border: 1px dashed rgba(245,246,247,0.16) !important;
      justify-content: center !important;
      text-align: center !important;
      border-radius: 6px !important;
      margin-top: 10px !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:last-child .stButton > button * {
      color: #8b8e93 !important;
      text-align: center !important;
      justify-content: center !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:last-child .stButton > button:hover {
      background-color: rgba(232,122,95,0.12) !important;
      border-color: #e87a5f !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:last-child .stButton > button:hover * {
      color: #e87a5f !important;
    }

    /* ===== NEO TOGGLE: Theme trigger button hidden ===== */
    [data-testid="stColumn"]:last-child [data-testid="stVerticalBlock"] {
      display: flex !important;
      flex-direction: column !important;
      align-items: flex-end !important;
      justify-content: center !important;
      padding: 0 !important;
      margin: 0 !important;
    }
    [data-testid="stColumn"]:last-child .stButton {
      display: none !important;
    }
    [data-testid="stColumn"]:last-child [data-testid="stElementContainer"] {
      padding: 0 !important;
      margin: 0 !important;
    }

    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #0c0d0f; }
    ::-webkit-scrollbar-thumb { background: #1a1c1e; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #5fe3b1; }
    </style>
    ''')
else:
    # ── BRIGHT MODE (MATCHING OBSIDIAN PRECISION GEOMETRY & TYPOGRAPHY) ──
    st.html('''
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Geist+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <style>
    /* ===== BRIGHT PRECISION TOKENS ===== */
    :root {
      --color-primary:   #0f172a;
      --color-secondary: #64748b;
      --color-accent:    #059669;
      --color-neutral:   #ffffff;
      --color-surface:   #f8fafc;
      --color-hairline:  rgba(15,23,42,0.08);
      --font-display:    'Inter', sans-serif;
      --font-body:       'Inter', sans-serif;
      --font-mono:       'Geist Mono', monospace;
      --radius-sm:       4px;
      --radius-md:       6px;
      --radius-lg:       8px;
    }

    * {
      font-feature-settings: "calt" 1;
      box-sizing: border-box;
    }

    html, body, [class*="css"], .stApp {
      background-color: #f4f6f1 !important;
      color: #0e0f0c !important;
      font-family: 'Inter', sans-serif !important;
      font-weight: 400 !important;
      -webkit-font-smoothing: antialiased;
    }

    .main, .stMainBlockContainer, .block-container,
    [data-testid="stMain"], [data-testid="stAppViewContainer"] > section:first-child {
      background-color: #f4f6f1 !important;
      color: #0e0f0c !important;
      padding-top: 1.5rem !important;
    }

    /* ── Streamlit Header Bar ── */
    header[data-testid="stHeader"] {
      background: transparent !important;
      z-index: 100 !important;
    }

    /* ── Hide Deploy Button ── */
    [data-testid="stAppDeployButton"],
    .stDeployButton,
    div:has(> [data-testid="stAppDeployButton"]),
    div[data-testid="stToolbar"] button:first-child:not([data-testid="stMainMenu"]) {
      display: none !important;
      visibility: hidden !important;
      opacity: 0 !important;
      pointer-events: none !important;
    }

    /* ── Typography & Prose ── */
    p, span, small, li, div, b, strong, em, .stMarkdown, .stMarkdown p {
      color: #0e0f0c;
      font-family: 'Inter', sans-serif;
    }
    .stCaption, [data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p, .stCaption p {
      color: #454745 !important;
      font-family: 'Inter', sans-serif !important;
      font-size: 0.85rem !important;
    }

    /* ── Headlines (Calm Authority Inter 600) ── */
    h1, [data-testid="stHeadingWithActionElements"] h1, h1 * {
      font-family: 'Inter', sans-serif !important;
      color: #0e0f0c !important;
      font-weight: 600 !important;
      line-height: 1.12 !important;
      letter-spacing: -0.025em !important;
      font-size: 2.25rem !important;
      margin-bottom: 0.3rem !important;
    }

    h2, [data-testid="stHeadingWithActionElements"] h2, h2 * {
      font-family: 'Inter', sans-serif !important;
      color: #0e0f0c !important;
      font-weight: 600 !important;
      line-height: 1.25 !important;
      letter-spacing: -0.012em !important;
      font-size: 1.45rem !important;
      margin-top: 1.2rem !important;
      margin-bottom: 0.4rem !important;
    }

    h3, [data-testid="stHeadingWithActionElements"] h3, h3 * {
      font-family: 'Inter', sans-serif !important;
      color: #0e0f0c !important;
      font-weight: 600 !important;
      line-height: 1.3 !important;
      letter-spacing: -0.01em !important;
      font-size: 1.2rem !important;
    }

    h4, h5, h6, h4 *, h5 *, h6 * {
      font-family: 'Inter', sans-serif !important;
      color: #0e0f0c !important;
      font-weight: 600 !important;
    }

    /* ── Metric Cards ── */
    div[data-testid="metric-container"],
    [data-testid="stMetric"] {
      background: #ffffff !important;
      border: 1px solid rgba(14,15,12,0.10) !important;
      box-shadow: rgba(14,15,12,0.03) 0 1px 3px !important;
      border-radius: 8px !important;
      padding: 16px 20px !important;
      transition: transform 180ms ease, border-color 180ms ease !important;
    }
    div[data-testid="metric-container"]:hover,
    [data-testid="stMetric"]:hover {
      border-color: rgba(14,15,12,0.22) !important;
      transform: translateY(-1px) !important;
    }
    [data-testid="stMetricLabel"] > div,
    [data-testid="stMetricLabel"] label,
    [data-testid="stMetricLabel"] p,
    div[data-testid="metric-container"] label {
      color: #454745 !important;
      font-size: 0.6875rem !important;
      text-transform: uppercase !important;
      letter-spacing: 0.06em !important;
      font-family: 'Geist Mono', monospace !important;
      font-weight: 500 !important;
    }
    [data-testid="stMetricValue"] > div,
    [data-testid="stMetricValue"] p,
    div[data-testid="metric-container"] [data-testid="stMetricValue"] {
      color: #0e0f0c !important;
      font-family: 'Geist Mono', monospace !important;
      font-size: 1.75rem !important;
      line-height: 1.0 !important;
      font-weight: 600 !important;
      font-variant-numeric: tabular-nums !important;
      margin-top: 6px !important;
      margin-bottom: 4px !important;
    }
    [data-testid="stMetricDelta"] {
      font-family: 'Geist Mono', monospace !important;
      font-size: 0.75rem !important;
      font-variant-numeric: tabular-nums !important;
      font-weight: 500 !important;
    }

    /* ── Form Containers ── */
    [data-testid="stForm"] {
      background: #ffffff !important;
      border: 1px solid rgba(14,15,12,0.10) !important;
      border-radius: 8px !important;
      padding: 24px !important;
      box-shadow: rgba(14,15,12,0.03) 0 1px 3px !important;
    }

    /* ── Form Labels & Widget Headings ── */
    label,
    [data-testid="stWidgetLabel"],
    [data-testid="stWidgetLabel"] *,
    label[data-testid="stWidgetLabel"] p,
    label[data-testid="stWidgetLabel"] span,
    label[data-testid="stWidgetLabel"] div {
      color: #0e0f0c !important;
      font-family: 'Inter', sans-serif !important;
      font-size: 0.875rem !important;
      font-weight: 500 !important;
      letter-spacing: -0.005em !important;
    }

    /* ── Radio & Checkbox Buttons ── */
    [data-testid="stRadio"] label,
    [data-testid="stRadio"] label *,
    [data-testid="stRadio"] div[role="radiogroup"] label *,
    [data-testid="stCheckbox"] label,
    [data-testid="stCheckbox"] label *,
    [data-testid="stCheckbox"] span,
    [data-testid="stCheckbox"] p {
      color: #0e0f0c !important;
      font-family: 'Inter', sans-serif !important;
      font-size: 0.875rem !important;
      font-weight: 400 !important;
    }
    [data-testid="stRadio"] input:checked + div {
      border-color: #9fe870 !important;
      background-color: #9fe870 !important;
    }

    /* ── Form Inputs & Textareas ── */
    input[type="text"], input[type="password"], input[type="email"],
    input[type="number"], textarea, [data-baseweb="input"] input {
      background-color: #ffffff !important;
      border: 1px solid rgba(14,15,12,0.15) !important;
      border-radius: 6px !important;
      color: #0e0f0c !important;
      font-family: 'Inter', sans-serif !important;
      font-size: 0.875rem !important;
      padding: 9px 12px !important;
    }
    input:focus, textarea:focus, [data-baseweb="input"]:focus-within {
      border-color: #9fe870 !important;
      box-shadow: 0 0 0 3px rgba(159,232,112,0.25) !important;
      outline: none !important;
    }
    ::placeholder,
    input::placeholder,
    textarea::placeholder {
      color: #8b8e93 !important;
      opacity: 0.85 !important;
      font-family: 'Inter', sans-serif !important;
    }

    /* ── Number Input Controls ── */
    [data-testid="stNumberInput"] input {
      font-family: 'Geist Mono', monospace !important;
      font-variant-numeric: tabular-nums !important;
      color: #0e0f0c !important;
    }
    [data-testid="stNumberInput"] button {
      background-color: #f4f6f1 !important;
      border: 1px solid rgba(14,15,12,0.12) !important;
      color: #0e0f0c !important;
    }
    [data-testid="stNumberInput"] button:hover {
      background-color: #e5e9e0 !important;
      border-color: #9fe870 !important;
    }
    [data-testid="stNumberInput"] button svg {
      fill: #0e0f0c !important;
    }

    /* ── Selectbox ── */
    [data-baseweb="select"] > div,
    [data-baseweb="select"] {
      background-color: #ffffff !important;
      border: 1px solid rgba(14,15,12,0.15) !important;
      border-radius: 6px !important;
    }
    [data-baseweb="select"] span,
    [data-baseweb="select"] div,
    [data-baseweb="select"] input {
      color: #0e0f0c !important;
      font-family: 'Inter', sans-serif !important;
    }
    [data-baseweb="popover"], [data-baseweb="menu"] {
      background-color: #ffffff !important;
      border-radius: 8px !important;
      border: 1px solid rgba(14,15,12,0.12) !important;
      box-shadow: 0 4px 14px rgba(0,0,0,0.08) !important;
    }
    [data-baseweb="option"], [data-baseweb="option"] * {
      background-color: #ffffff !important;
      color: #0e0f0c !important;
      font-size: 0.85rem !important;
    }
    [data-baseweb="option"]:hover, [data-baseweb="option"]:hover * {
      background-color: rgba(159,232,112,0.2) !important;
      color: #163300 !important;
    }

    /* ── Primary Action Buttons (Limepress Electric Lime + Dark Forest Text) ── */
    .stButton > button[kind="primary"],
    .stButton > button[data-testid="stBaseButton-primary"],
    .stFormSubmitButton > button {
      background-color: #9fe870 !important;
      border: 1px solid #9fe870 !important;
      border-radius: 6px !important;
      font-family: 'Inter', sans-serif !important;
      font-weight: 600 !important;
      font-size: 0.8125rem !important;
      padding: 9px 18px !important;
      box-shadow: 0 1px 3px rgba(14,15,12,0.1) !important;
      transition: all 180ms cubic-bezier(0.32, 0.72, 0, 1) !important;
    }
    .stButton > button[kind="primary"] *,
    .stButton > button[data-testid="stBaseButton-primary"] *,
    .stFormSubmitButton > button * {
      color: #163300 !important;
      font-family: 'Inter', sans-serif !important;
      font-weight: 600 !important;
    }
    .stButton > button[kind="primary"]:hover,
    .stButton > button[data-testid="stBaseButton-primary"]:hover,
    .stFormSubmitButton > button:hover {
      background-color: #8de05a !important;
      box-shadow: 0 0 16px -2px rgba(159,232,112,0.5) !important;
    }

    /* ── Secondary & Regular Buttons ── */
    .stButton > button[kind="secondary"],
    .stButton > button[data-testid="stBaseButton-secondary"],
    .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not(.stFormSubmitButton button) {
      background-color: #ffffff !important;
      border: 1px solid rgba(14,15,12,0.12) !important;
      border-radius: 6px !important;
      font-family: 'Inter', sans-serif !important;
      font-weight: 500 !important;
      font-size: 0.8125rem !important;
      padding: 9px 18px !important;
      transition: all 180ms ease !important;
    }
    .stButton > button[kind="secondary"] *,
    .stButton > button[data-testid="stBaseButton-secondary"] *,
    .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not(.stFormSubmitButton button) * {
      color: #0e0f0c !important;
      font-family: 'Inter', sans-serif !important;
      font-weight: 500 !important;
    }
    .stButton > button[kind="secondary"]:hover,
    .stButton > button[data-testid="stBaseButton-secondary"]:hover,
    .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not(.stFormSubmitButton button):hover {
      background-color: #f4f6f1 !important;
      border-color: #9fe870 !important;
    }
    .stButton > button[kind="secondary"]:hover *,
    .stButton > button[data-testid="stBaseButton-secondary"]:hover *,
    .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not(.stFormSubmitButton button):hover * {
      color: #163300 !important;
    }

    /* ── Outline & Download Buttons ── */
    [data-testid="stDownloadButton"] > button {
      background: transparent !important;
      border: 1px solid rgba(14,15,12,0.15) !important;
      border-radius: 6px !important;
      padding: 9px 18px !important;
      font-family: 'Inter', sans-serif !important;
      font-weight: 500 !important;
      font-size: 0.8125rem !important;
      transition: all 180ms ease !important;
    }
    [data-testid="stDownloadButton"] > button * {
      color: #0e0f0c !important;
    }
    [data-testid="stDownloadButton"] > button:hover {
      border-color: rgba(14,15,12,0.3) !important;
      background: rgba(14,15,12,0.04) !important;
    }

    /* ── Dataframes ── */
    [data-testid="stDataFrame"] {
      border: 1px solid rgba(14,15,12,0.10) !important;
      box-shadow: rgba(14,15,12,0.03) 0 1px 3px !important;
      border-radius: 8px !important;
      overflow: hidden !important;
      background: #ffffff !important;
    }
    [data-testid="stDataFrame"] th {
      background: #eaede6 !important;
      color: #454745 !important;
      font-family: 'Geist Mono', monospace !important;
      font-size: 0.72rem !important;
      font-weight: 600 !important;
      text-transform: uppercase !important;
      letter-spacing: 0.06em !important;
    }
    [data-testid="stDataFrame"] td {
      color: #0e0f0c !important;
      font-family: 'Geist Mono', monospace !important;
      font-size: 0.8125rem !important;
      font-variant-numeric: tabular-nums !important;
    }

    /* ── Expanders ── */
    details, [data-testid="stExpander"] {
      background: #ffffff !important;
      border: 1px solid rgba(14,15,12,0.10) !important;
      box-shadow: rgba(14,15,12,0.03) 0 1px 3px !important;
      border-radius: 8px !important;
      padding: 8px 16px !important;
    }
    details summary, [data-testid="stExpander"] summary, details summary * {
      color: #0e0f0c !important;
      font-family: 'Inter', sans-serif !important;
      font-weight: 600 !important;
      font-size: 0.95rem !important;
    }

    /* ── Alerts ── */
    [data-testid="stAlert"], div[role="alert"] {
      border-radius: 8px !important;
      border: 1px solid rgba(14,15,12,0.10) !important;
      border-left: 3px solid #9fe870 !important;
      background: #ffffff !important;
    }
    [data-testid="stAlert"] *, div[role="alert"] * {
      color: #0e0f0c !important;
      font-family: 'Inter', sans-serif !important;
    }

    /* ── Limepress Underline Tabs ── */
    [data-baseweb="tab-list"] {
      background: transparent !important;
      border-bottom: 1px solid rgba(14,15,12,0.10) !important;
      border-radius: 0 !important;
      padding: 0 !important;
      gap: 16px !important;
      margin-bottom: 16px !important;
    }
    [data-baseweb="tab"] {
      background: transparent !important;
      border: none !important;
      border-bottom: 2px solid transparent !important;
      border-radius: 0 !important;
      padding: 8px 4px !important;
    }
    [data-baseweb="tab"], [data-baseweb="tab"] * {
      color: #454745 !important;
      font-family: 'Inter', sans-serif !important;
      font-weight: 500 !important;
      font-size: 0.875rem !important;
    }
    [data-baseweb="tab"]:hover, [data-baseweb="tab"]:hover * {
      color: #0e0f0c !important;
    }
    [aria-selected="true"][data-baseweb="tab"] {
      background: transparent !important;
      border-bottom: 2px solid #9fe870 !important;
      box-shadow: none !important;
    }
    [aria-selected="true"][data-baseweb="tab"],
    [aria-selected="true"][data-baseweb="tab"] * {
      color: #0e0f0c !important;
      font-weight: 600 !important;
    }

    /* ── Sidebar (Limepress Fintech Rail) ── */
    section[data-testid="stSidebar"],
    [data-testid="stSidebar"] {
      background-color: #eaede6 !important;
      border-right: 1px solid rgba(14,15,12,0.10) !important;
    }

    .nav-header {
      color: #454745;
      font-family: 'Geist Mono', monospace;
      font-size: 0.68rem;
      font-weight: 600;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      margin-top: 8px;
      margin-bottom: 10px;
      padding-left: 6px;
    }

    section[data-testid="stSidebar"] .stButton {
      margin-bottom: 4px !important;
      width: 100% !important;
    }

    section[data-testid="stSidebar"] .stButton > button {
      width: 100% !important;
      display: flex !important;
      justify-content: flex-start !important;
      align-items: center !important;
      text-align: left !important;
      padding: 8px 14px !important;
      border-radius: 6px !important;
    }

    /* Inactive Sidebar Nav Items */
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"],
    section[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"],
    section[data-testid="stSidebar"] .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not(#sidebar_logout_btn) {
      background-color: #ffffff !important;
      border: 1px solid rgba(14,15,12,0.08) !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"] *,
    section[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"] *,
    section[data-testid="stSidebar"] .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not(#sidebar_logout_btn) * {
      color: #0e0f0c !important;
      font-family: 'Inter', sans-serif !important;
      font-weight: 500 !important;
      font-size: 0.85rem !important;
      justify-content: flex-start !important;
      text-align: left !important;
    }

    section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover,
    section[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"]:hover,
    section[data-testid="stSidebar"] .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not(#sidebar_logout_btn):hover {
      background-color: #f4f6f1 !important;
      border-color: #9fe870 !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover *,
    section[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"]:hover *,
    section[data-testid="stSidebar"] .stButton > button:not([kind="primary"]):not([data-testid="stBaseButton-primary"]):not(#sidebar_logout_btn):hover * {
      color: #163300 !important;
    }

    /* Active Sidebar Nav Item */
    section[data-testid="stSidebar"] .stButton > button[kind="primary"],
    section[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] {
      background-color: #9fe870 !important;
      border: 1px solid #9fe870 !important;
    }
    section[data-testid="stSidebar"] .stButton > button[kind="primary"] *,
    section[data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] * {
      color: #163300 !important;
      font-family: 'Inter', sans-serif !important;
      font-weight: 600 !important;
      font-size: 0.85rem !important;
      justify-content: flex-start !important;
      text-align: left !important;
    }

    /* Sign Out button */
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:last-child .stButton > button {
      background-color: transparent !important;
      border: 1px dashed rgba(14,15,12,0.18) !important;
      justify-content: center !important;
      text-align: center !important;
      border-radius: 6px !important;
      margin-top: 10px !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:last-child .stButton > button * {
      color: #454745 !important;
      text-align: center !important;
      justify-content: center !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:last-child .stButton > button:hover {
      background-color: rgba(239,68,68,0.08) !important;
      border-color: #ef4444 !important;
    }
    section[data-testid="stSidebar"] div[data-testid="stVerticalBlock"] > div:last-child .stButton > button:hover * {
      color: #ef4444 !important;
    }

    /* ===== NEO TOGGLE: Theme trigger button hidden ===== */
    [data-testid="stColumn"]:last-child [data-testid="stVerticalBlock"] {
      display: flex !important;
      flex-direction: column !important;
      align-items: flex-end !important;
      justify-content: center !important;
      padding: 0 !important;
      margin: 0 !important;
    }
    [data-testid="stColumn"]:last-child .stButton {
      display: none !important;
    }
    [data-testid="stColumn"]:last-child [data-testid="stElementContainer"] {
      padding: 0 !important;
      margin: 0 !important;
    }

    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #f8fafc; }
    ::-webkit-scrollbar-thumb { background: #cbd5e1; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #059669; }
    </style>
    ''')

# ----------------- SESSION AUTHENTICATION CHECK -----------------
user = get_current_user()

if not user:
    render_login(LOGO_B64)
    st.stop()

# ----------------- AUTHENTICATED WORKSPACE -----------------
allowed_modules = ROLES.get(user['role'], ['Dashboard'])

if 'current_module' not in st.session_state or st.session_state.current_module not in allowed_modules:
    st.session_state.current_module = allowed_modules[0] if allowed_modules else 'Dashboard'

# Sidebar Navigation
with st.sidebar:
    logo_border = "#5fe3b1" if is_dark else "#9fe870"
    logo_glow = "rgba(95,227,177,0.35)" if is_dark else "rgba(159,232,112,0.35)"
    logo_sidebar_img = f"<img src='data:image/jpeg;base64,{LOGO_B64}' style='width:46px; height:46px; border-radius:12px; border:1.5px solid {logo_border}; box-shadow: 0 0 16px {logo_glow}; flex-shrink:0; object-fit:cover;' />" if LOGO_B64 else ""

    sub_label_color = "#8b8e93" if is_dark else "#555754"
    card_bg = "#1a1c1e" if is_dark else "#ffffff"
    card_border = "rgba(245,246,247,0.08)" if is_dark else "rgba(14,15,12,0.12)"
    badge_bg = "#5fe3b1" if is_dark else "#9fe870"
    badge_color = "#0c0d0f" if is_dark else "#163300"
    title_color = "#f5f6f7" if is_dark else "#0e0f0c"

    st.html(f"""
    <div style='display:flex; align-items:center; gap:12px; padding: 4px 0 12px 0;'>
      {logo_sidebar_img}
      <div>
        <div style='font-family:"Inter",sans-serif; font-size:1.35rem; font-weight:700;
                    color:{title_color}; letter-spacing:-0.02em; line-height:0.9;'>SMARTBIZ</div>
        <div style='font-family:"Geist Mono",monospace; font-size:0.62rem; color:{sub_label_color};
                    letter-spacing:0.1em; text-transform:uppercase; margin-top:5px; font-weight:600;'>ERP SYSTEM</div>
      </div>
    </div>

    <div style='background:{card_bg}; border:1px solid {card_border}; border-radius:8px; padding:12px 14px; box-shadow:rgba(0,0,0,0.2) 0 1px 2px; margin-bottom:12px;'>
      <div style='font-family:"Geist Mono",monospace; color:{sub_label_color}; font-size:0.62rem; text-transform:uppercase; letter-spacing:0.08em; font-weight:600;'>OPERATOR</div>
      <div style='color:{title_color}; font-size:0.92rem; font-weight:600; margin-top:2px; font-family:"Inter",sans-serif;'>{user['name']}</div>
      <div style='display:inline-block; background:{badge_bg}; color:{badge_color}; font-family:"Geist Mono",monospace;
                  font-size:0.65rem; font-weight:700; letter-spacing:0.04em; padding:3px 8px;
                  border-radius:4px; text-transform:uppercase; margin-top:6px;'>{user['role']}</div>
    </div>
    """)

    st.html("<div class='nav-header'>NAVIGATION</div>")

    for mod in allowed_modules:
        is_active = (st.session_state.current_module == mod)
        if st.button(mod, key=f"nav_btn_{mod}", use_container_width=True, type="primary" if is_active else "secondary"):
            if st.session_state.current_module != mod:
                st.session_state.current_module = mod
                st.rerun()

    st.html("<div style='margin-top:16px;'></div>")
    if st.button("Log Out", key="sidebar_logout_btn", use_container_width=True):
        logout_user()

selected_module = st.session_state.current_module

# ----------------- TOP BAR THEME SWITCHER (CYBERNETIC NEO TOGGLE) -----------------
top_c1, top_c2 = st.columns([5.5, 1.2])
with top_c2:
    # 1. Hidden theme trigger button — display:none makes it invisible but JS .click() still fires it.
    if st.button("THEME_TOGGLE", key="theme_trigger_btn"):
        st.session_state.theme_mode = 'light' if is_dark else 'dark'
        st.rerun()

    # 2. Neo Toggle visual via components.html — has allow-same-origin so JS works cross-frame.
    checked_attr = "checked" if is_dark else ""
    on_color = "#5fe3b1" if is_dark else "#9fe870"
    glow_color = "rgba(95,227,177,0.5)" if is_dark else "rgba(159,232,112,0.5)"
    glow_border = "rgba(95,227,177,0.3)" if is_dark else "rgba(159,232,112,0.3)"
    glow_subtle = "rgba(95,227,177,0.2)" if is_dark else "rgba(159,232,112,0.2)"

    components.html(f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8">
    <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    html, body {{
      background: transparent !important;
      display: flex;
      justify-content: flex-end;
      align-items: flex-start;
      height: 80px;
      overflow: hidden;
      padding: 4px 4px 0 0;
    }}
    .neo-toggle-container {{
      --toggle-width: 80px;
      --toggle-height: 38px;
      --toggle-bg: #181c20;
      --toggle-off-color: #475057;
      --toggle-on-color: {on_color};
      --toggle-transition: 0.4s cubic-bezier(0.25, 1, 0.5, 1);
      position: relative;
      display: inline-flex;
      flex-direction: column;
      font-family: "Segoe UI", Tahoma, sans-serif;
      user-select: none;
    }}
    .neo-toggle-input {{
      position: absolute;
      opacity: 0;
      width: 0;
      height: 0;
    }}
    .neo-toggle {{
      position: relative;
      width: var(--toggle-width);
      height: var(--toggle-height);
      display: block;
      cursor: pointer;
      transform: translateZ(0);
      perspective: 500px;
    }}
    .neo-track {{
      position: absolute;
      inset: 0;
      border-radius: calc(var(--toggle-height) / 2);
      overflow: hidden;
      transform-style: preserve-3d;
      transform: translateZ(-1px);
      transition: transform var(--toggle-transition);
      box-shadow:
        0 2px 10px rgba(0,0,0,0.5),
        inset 0 0 0 1px rgba(255,255,255,0.1);
    }}
    .neo-background-layer {{
      position: absolute;
      inset: 0;
      background: var(--toggle-bg);
      background-image: linear-gradient(
        -45deg,
        rgba(20,20,20,0.8) 0%,
        rgba(30,30,30,0.3) 50%,
        rgba(20,20,20,0.8) 100%
      );
      opacity: 1;
      transition: all var(--toggle-transition);
    }}
    .neo-grid-layer {{
      position: absolute;
      inset: 0;
      background-image:
        linear-gradient(to right, rgba(71,80,87,0.05) 1px, transparent 1px),
        linear-gradient(to bottom, rgba(71,80,87,0.05) 1px, transparent 1px);
      background-size: 5px 5px;
      opacity: 0;
      transition: opacity var(--toggle-transition);
    }}
    .neo-track-highlight {{
      position: absolute;
      inset: 1px;
      border-radius: calc(var(--toggle-height) / 2);
      background: linear-gradient(90deg, transparent, {glow_subtle});
      opacity: 0;
      transition: all var(--toggle-transition);
    }}
    .neo-spectrum-analyzer {{
      position: absolute;
      bottom: 6px;
      right: 10px;
      height: 10px;
      display: flex;
      align-items: flex-end;
      gap: 2px;
      opacity: 0;
      transition: opacity var(--toggle-transition);
    }}
    .neo-spectrum-bar {{
      width: 2px;
      height: 3px;
      background-color: var(--toggle-on-color);
      opacity: 0.8;
    }}
    .neo-thumb {{
      position: absolute;
      top: 4px;
      left: 4px;
      width: 30px;
      height: 30px;
      border-radius: 50%;
      transform-style: preserve-3d;
      transition: transform var(--toggle-transition);
      z-index: 1;
    }}
    .neo-thumb-ring {{
      position: absolute;
      inset: 0;
      border-radius: 50%;
      border: 1px solid rgba(255,255,255,0.1);
      background: var(--toggle-off-color);
      box-shadow: 0 2px 10px rgba(0,0,0,0.2);
      transition: all var(--toggle-transition);
    }}
    .neo-thumb-core {{
      position: absolute;
      inset: 5px;
      border-radius: 50%;
      background: linear-gradient(135deg, rgba(255,255,255,0.1), transparent);
      transition: all var(--toggle-transition);
      overflow: hidden;
      display: flex;
      align-items: center;
      justify-content: center;
    }}
    .neo-thumb-icon {{
      position: relative;
      width: 10px;
      height: 10px;
      transition: all var(--toggle-transition);
    }}
    .neo-thumb-wave {{
      position: absolute;
      top: 50%;
      left: 50%;
      width: 10px;
      height: 2px;
      background: var(--toggle-off-color);
      transform: translate(-50%, -50%);
      transition: all var(--toggle-transition);
    }}
    .neo-thumb-pulse {{
      position: absolute;
      inset: 0;
      border-radius: 50%;
      border: 1px solid var(--toggle-off-color);
      transform: scale(0);
      opacity: 0;
      transition: all var(--toggle-transition);
    }}
    .neo-gesture-area {{
      position: absolute;
      inset: -10px;
      z-index: 0;
    }}
    .neo-interaction-feedback {{
      position: absolute;
      inset: 0;
      pointer-events: none;
      z-index: 0;
    }}
    .neo-ripple {{
      position: absolute;
      top: 50%;
      left: 30%;
      width: 0;
      height: 0;
      border-radius: 50%;
      background: radial-gradient(circle, var(--toggle-on-color) 0%, transparent 70%);
      transform: translate(-50%, -50%);
      opacity: 0;
      transition: all 0.4s ease-out;
    }}
    .neo-progress-arc {{
      position: absolute;
      top: 50%;
      left: 50%;
      width: 80px;
      height: 80px;
      border-radius: 50%;
      border: 2px solid transparent;
      border-top-color: var(--toggle-on-color);
      transform: translate(-50%, -50%) scale(0) rotate(0deg);
      opacity: 0;
      transition: opacity 0.3s ease, transform 0.5s ease;
    }}
    .neo-status {{
      position: absolute;
      bottom: -20px;
      left: 0;
      width: 100%;
      display: flex;
      justify-content: center;
    }}
    .neo-status-indicator {{
      display: flex;
      align-items: center;
      gap: 4px;
    }}
    .neo-status-dot {{
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background-color: var(--toggle-off-color);
      transition: all var(--toggle-transition);
    }}
    .neo-status-text {{
      font-size: 9px;
      font-weight: 600;
      color: var(--toggle-off-color);
      letter-spacing: 1px;
      transition: all var(--toggle-transition);
    }}
    .neo-toggle-input:checked + .neo-toggle .neo-thumb {{
      transform: translateX(calc(var(--toggle-width) - 38px));
    }}
    .neo-toggle-input:checked + .neo-toggle .neo-thumb-ring {{
      background-color: var(--toggle-on-color);
      border-color: {glow_border};
      box-shadow: 0 0 15px {glow_color};
    }}
    .neo-toggle-input:checked + .neo-toggle .neo-thumb-wave {{
      height: 8px;
      width: 8px;
      border-radius: 50%;
      background: transparent;
      border: 1px solid #fff;
    }}
    .neo-toggle-input:checked + .neo-toggle .neo-thumb-pulse {{
      transform: scale(1.2);
      opacity: 0.3;
      animation: neo-pulse 1.5s infinite;
    }}
    .neo-toggle-input:checked + .neo-toggle .neo-track-highlight {{
      background: linear-gradient(90deg, transparent, {glow_subtle});
      opacity: 1;
    }}
    .neo-toggle-input:checked + .neo-toggle .neo-grid-layer {{ opacity: 1; }}
    .neo-toggle-input:checked + .neo-toggle .neo-spectrum-analyzer {{ opacity: 1; }}
    .neo-toggle-input:checked + .neo-toggle .neo-spectrum-bar:nth-child(1) {{ animation: neo-spectrum 0.9s infinite; }}
    .neo-toggle-input:checked + .neo-toggle .neo-spectrum-bar:nth-child(2) {{ animation: neo-spectrum 0.8s 0.1s infinite; }}
    .neo-toggle-input:checked + .neo-toggle .neo-spectrum-bar:nth-child(3) {{ animation: neo-spectrum 1.1s 0.2s infinite; }}
    .neo-toggle-input:checked + .neo-toggle .neo-spectrum-bar:nth-child(4) {{ animation: neo-spectrum 0.7s 0.1s infinite; }}
    .neo-toggle-input:checked + .neo-toggle .neo-spectrum-bar:nth-child(5) {{ animation: neo-spectrum 0.9s 0.15s infinite; }}
    .neo-toggle-input:checked + .neo-toggle .neo-status-dot {{
      background-color: var(--toggle-on-color);
      box-shadow: 0 0 8px var(--toggle-on-color);
    }}
    .neo-toggle-input:checked + .neo-toggle .neo-status-text {{ color: var(--toggle-on-color); }}
    .neo-toggle-input:checked + .neo-toggle .neo-status-text::before {{ content: "DARK"; }}
    .neo-toggle-input:not(:checked) + .neo-toggle .neo-status-text::before {{ content: "BRIGHT"; }}
    .neo-toggle:hover .neo-thumb-ring {{ transform: scale(1.05); }}
    .neo-toggle.neo-activated .neo-ripple {{
      width: 100px;
      height: 100px;
      opacity: 0.5;
      transition: all 0.6s ease-out;
    }}
    .neo-toggle.neo-progress .neo-progress-arc {{
      opacity: 0.8;
      transform: translate(-50%, -50%) scale(1) rotate(270deg);
      transition: opacity 0.3s ease, transform 1s ease;
    }}
    @keyframes neo-pulse {{
      0%   {{ transform: scale(1);   opacity: 0.5; }}
      50%  {{ transform: scale(1.5); opacity: 0.2; }}
      100% {{ transform: scale(1);   opacity: 0.5; }}
    }}
    @keyframes neo-spectrum {{
      0%   {{ height: 3px; }}
      50%  {{ height: 8px; }}
      100% {{ height: 3px; }}
    }}
    </style>
    </head>
    <body>
    <div class="neo-toggle-container">
      <input class="neo-toggle-input" id="neo-toggle" type="checkbox" {checked_attr} />
      <label class="neo-toggle" for="neo-toggle" id="neoLabel">
        <div class="neo-track">
          <div class="neo-background-layer"></div>
          <div class="neo-grid-layer"></div>
          <div class="neo-spectrum-analyzer">
            <div class="neo-spectrum-bar"></div>
            <div class="neo-spectrum-bar"></div>
            <div class="neo-spectrum-bar"></div>
            <div class="neo-spectrum-bar"></div>
            <div class="neo-spectrum-bar"></div>
          </div>
          <div class="neo-track-highlight"></div>
        </div>
        <div class="neo-thumb">
          <div class="neo-thumb-ring"></div>
          <div class="neo-thumb-core">
            <div class="neo-thumb-icon">
              <div class="neo-thumb-wave"></div>
              <div class="neo-thumb-pulse"></div>
            </div>
          </div>
        </div>
        <div class="neo-gesture-area"></div>
        <div class="neo-interaction-feedback">
          <div class="neo-ripple"></div>
          <div class="neo-progress-arc"></div>
        </div>
        <div class="neo-status">
          <div class="neo-status-indicator">
            <div class="neo-status-dot"></div>
            <div class="neo-status-text"></div>
          </div>
        </div>
      </label>
    </div>
    <script>
    var label = document.getElementById('neoLabel');
    var inp   = document.getElementById('neo-toggle');
    label.addEventListener('click', function(e) {{
      e.preventDefault();
      label.classList.add('neo-activated', 'neo-progress');
      setTimeout(function() {{ label.classList.remove('neo-activated', 'neo-progress'); }}, 700);
      inp.checked = !inp.checked;
      try {{
        var btn = Array.from(window.parent.document.querySelectorAll('button')).find(function(b) {{
          return b.textContent.trim() === 'THEME_TOGGLE';
        }});
        if (btn) btn.click();
      }} catch(e) {{ console.warn('NeoToggle:', e); }}
    }});
    </script>
    </body></html>
    """, height=80, scrolling=False)



# ----------------- MODULE ROUTER -----------------
MODULE_ROUTERS = {
    'Dashboard': render_dashboard,
    'Products': render_products,
    'Inventory': render_inventory,
    'Customers': render_customers,
    'Suppliers': render_suppliers,
    'Sales & Invoices': render_sales,
    'Purchases': render_purchases,
    'Expenses': render_expenses,
    'Finance': render_finance,
    'Employees': render_employees,
    'Users & Roles': render_users,
    'Reports & Analytics': render_reports,
}

render_func = MODULE_ROUTERS.get(selected_module)
if render_func:
    render_func(user)
else:
    st.warning(f"Module '{selected_module}' is not implemented or not accessible.")
