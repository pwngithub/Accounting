import streamlit as st
import pandas as pd
import requests
import re

# -------------------------------
# APP CONFIGURATION
# -------------------------------
st.set_page_config(page_title="Profit & Loss Dashboard", page_icon="💰", layout="wide")

# -------------------------------
# SIDEBAR: THEME TOGGLE
# -------------------------------
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = False  # default: light mode

# Theme toggle button
if st.sidebar.button("🌓 Toggle Background Theme"):
    st.session_state["dark_mode"] = not st.session_state["dark_mode"]

# Apply color settings based on mode
if st.session_state["dark_mode"]:
    bg_color = "#000000"
    text_color = "#FFFFFF"
    card_bg = "#1c1c1c"
    border_color = "#1e90ff"
    logo_url = (
        "https://images.squarespace-cdn.com/content/v1/651eb4433b13e72c1034f375/"
        "369c5df0-5363-4827-b041-1add0367f447/PBB+long+logo+white.png?format=1500w"
    )
else:
    bg_color = "#FFFFFF"
    text_color = "#000000"
    card_bg = "#ffffff"
    border_color = "#0056b3"
    logo_url = (
        "https://images.squarespace-cdn.com/content/v1/651eb4433b13e72c1034f375/"
        "369c5df0-5363-4827-b041-1add0367f447/PBB+long+logo.png?format=1500w"
    )

# Global app-wide background styling
st.markdown(
    f"""
    <style>
    body {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
    }}
    [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stSidebar"] {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
    }}
    div[data-testid="stMarkdownContainer"] p, h1, h2, h3, h4, h5, h6 {{
        color: {text_color} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------
# HEADER SECTION
# -------------------------------
st.markdown(
    f"""
    <div style="display:flex;align-items:center;justify-content:flex-start;">
        <img src="{logo_url}" width="258" height="49" style="margin-right:15px;">
    </div>
    <hr style="height:4px;border:none;background-color:{border_color};margin-top:0;margin-bottom:20px;">
    """,
    unsafe_allow_html=True,
)

# -------------------------------
# GOOGLE SHEETS SETTINGS
# -------------------------------
SHEET_ID = "1iiBe4CLYPlr_kpIOuvzxLliwA0ferGtBRhtnMLfhOQg"

# Load API key securely from Streamlit secrets
try:
    API_KEY = st.secrets["gcp"]["api_key"]
except Exception:
    st.error("❌ Google API key not found. Please add it in Streamlit secrets under [gcp].")
    st.stop()

# -------------------------------
# FETCH AVAILABLE SHEET NAMES
# -------------------------------
@st.cache_data(ttl=300)
def get_sheet_tabs(sheet_id, api_key):
    meta_url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}?key={api_key}"
    resp = requests.get(meta_url)
    if resp.status_code != 200:
        raise Exception(f"Failed to get sheet metadata: {resp.text}")
    sheets = resp.json().get("sheets", [])
    return [s["properties"]["title"] for s in sheets]

try:
    sheet_names = get_sheet_tabs(SHEET_ID, API_KEY)
    month_tabs = [n for n in sheet_names if n.startswith("25.")]
    if not month_tabs:
        month_tabs = sheet_names
    selected_tab = st.sidebar.selectbox("📅 Select Month", month_tabs, index=len(month_tabs) - 1)
except Exception as e:
    st.error(f"❌ Could not fetch sheet tabs: {e}")
    st.stop()

# -------------------------------
# LOAD DATA
# -------------------------------
@st.cache_data(ttl=300)
def load_sheet_data(sheet_id, tab_name, api_key):
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/'{tab_name}'!A1:Z200?key={api_key}"
    resp = requests.get(url)
    if resp.status_code != 200:
        raise Exception(f"Failed to load tab '{tab_name}': {resp.text}")

    data = resp.json().get("values", [])
    if not data:
        raise Exception("No data returned from sheet.")

    # --- find header row ---
    header_row_idx = None
    for i, row in enumerate(data):
        if sum(1 for c in row if c.strip()) >= 3:
            header_row_idx = i
            break
    if header_row_idx is None:
        raise Exception("Could not find a valid header row.")

    header = data[header_row_idx]
    body = data[header_row_idx + 1:]

    header = [h.strip() if h else f"Column_{i+1}" for i, h in enumerate(header)]
    df = pd.DataFrame(body, columns=header)

    # --- ensure unique column names ---
    if df.columns.duplicated().any():
        seen = {}
        new_cols = []
        for col in df.columns:
            seen[col] = seen.get(col, 0) + 1
            new_cols.append(col if seen[col] == 1 else f"{col}_{seen[col]}")
        df.columns = new_cols

    return df

try:
    df = load_sheet_data(SHEET_ID, selected_tab, API_KEY)
except Exception as e:
    st.error(f"❌ Failed to load data for {selected_tab}: {e}")
    st.stop()

# -------------------------------
# AUTO-DETECT KPI ROWS & COLUMNS
# -------------------------------
def find_row(df, keywords):
    col_a = df.iloc[:, 0].astype(str).str.lower()
    for kw in keywords:
        match = col_a[col_a.str.contains(kw.lower())]
        if not match.empty:
            return match.index[0]
    return None

def find_column(df, keyword):
    for i, col in enumerate(df.columns):
        if re.search(keyword, col, re.IGNORECASE):
            return i
    return None

def get_numeric(df, row, col):
    try:
        value = str(df.iat[row, col])
        return pd.to_numeric(value.replace(",", "").replace("$", ""), errors="coerce")
    except Exception:
        return 0

# --- detect column indices ---
monthly_col = find_column(df, "month") or 1
ytd_col = find_column(df, "ytd") or monthly_col

# --- detect key rows ---
ebitda_row = find_row(df, ["ebitda"])
subscriber_row = find_row(df, ["users months", "user months"])
mrr_row = find_row(df, ["broadhub rev", "broadhub revenue", "broadhub"])

# --- extract values ---
ebitda_value = get_numeric(df, ebitda_row, monthly_col) if ebitda_row is not None else 0
subscriber_count = get_numeric(df, subscriber_row, monthly_col) if subscriber_row is not None else 0
mrr_value = get_numeric(df, mrr_row, monthly_col) if mrr_row is not None else 0
arpu_value = (mrr_value / subscriber_count) if subscriber_count > 0 else 0

# -------------------------------
# KPI SECTION WITH COLORIZED VALUES
# -------------------------------
st.markdown(f"<h2 style='color:{border_color};'>💼 Financial Performance – {selected_tab}</h2>", unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)

def kpi_box(label, value):
    # Convert value to numeric if possible
    numeric_val = None
    try:
        numeric_val = float(value.replace('$','').replace(',',''))
    except Exception:
        pass
    value_color = border_color if numeric_val is None or numeric_val >= 0 else "red"
    label_color = text_color

    return f"""
    <div style="
        background-color:{card_bg};
        border:2px solid {border_color};
        border-radius:10px;
        padding:14px;
        box-shadow:0px 2px 10px rgba(0, 86, 179, 0.15);
        text-align:center;">
        <div style="font-weight:600;color:{label_color};">{label}</div>
        <div style="font-size:1.5em;font-weight:700;color:{value_color};">
            {value}
        </div>
    </div>
    """

mrr_display = f"${mrr_value:,.2f}"
subs_display = f"{subscriber_count:,.0f}"
arpu_display = f"${arpu_value:,.2f}"
ebitda_display = f"${ebitda_value:,.2f}"

col1.markdown(kpi_box("Monthly Recurring Revenue (MRR)", mrr_display), unsafe_allow_html=True)
col2.markdown(kpi_box("Subscriber Count", subs_display), unsafe_allow_html=True)
col3.markdown(kpi_box("Average Revenue Per User (ARPU)", arpu_display), unsafe_allow_html=True)
col4.markdown(kpi_box("EBITDA", ebitda_display), unsafe_allow_html=True)

# -------------------------------
# SIDEBAR OPTION: VIEW DATAFRAME
# -------------------------------
st.sidebar.markdown("---")
show_df = st.sidebar.checkbox("📋 Show Profit & Loss Sheet Preview", value=False)

if show_df:
    st.subheader(f"📋 Profit & Loss Sheet Preview – {selected_tab}")
    if df.columns.duplicated().any():
        df.columns = [
            f"{col}_{i+1}" if df.columns.tolist().count(col) > 1 else col
            for i, col in enumerate(df.columns)
        ]
    st.dataframe(df, use_container_width=True)

# -------------------------------
# DOWNLOAD BUTTON
# -------------------------------
st.subheader("⬇️ Download Data")
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(f"Download {selected_tab} CSV", csv, f"{selected_tab}_profit_loss.csv", "text/csv")

st.markdown("---")
st.caption("© 2025 Pioneer Broadband")
