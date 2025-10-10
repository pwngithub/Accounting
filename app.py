import streamlit as st
import pandas as pd
import requests
import re

# -------------------------------
# APP CONFIGURATION
# -------------------------------
st.set_page_config(page_title="Profit & Loss Dashboard", page_icon="💰", layout="wide")
st.title("💰 Pioneer Broadband Profit & Loss Dashboard")
st.caption("Auto-detecting Profit & Loss Dashboard synced securely from Google Sheets via the Google Sheets API.")

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
    st.success(f"✅ Loaded data for **{selected_tab}**")
except Exception as e:
    st.error(f"❌ Failed to load data for {selected_tab}: {e}")
    st.stop()

# -------------------------------
# AUTO-DETECT KPI ROWS & COLUMNS
# -------------------------------
def find_row(df, keywords):
    """Find row index containing any keyword in the first column."""
    col_a = df.iloc[:, 0].astype(str).str.lower()
    for kw in keywords:
        match = col_a[col_a.str.contains(kw.lower())]
        if not match.empty:
            return match.index[0]
    return None

def find_column(df, keyword):
    """Find column index containing keyword in the header."""
    for i, col in enumerate(df.columns):
        if re.search(keyword, col, re.IGNORECASE):
            return i
    return None

def get_numeric(df, row, col):
    """Safely extract and clean numeric value."""
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
# KPI DISPLAY
# -------------------------------
st.header(f"📊 Key Performance Indicators – {selected_tab}")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Monthly Recurring Revenue (MRR)", f"${mrr_value:,.2f}")
col2.metric("Subscriber Count", f"{subscriber_count:,.0f}")
col3.metric("Average Revenue Per User (ARPU)", f"${arpu_value:,.2f}")
col4.metric("EBITDA", f"${ebitda_value:,.2f}")

if mrr_value == 0:
    st.warning("⚠️ Could not detect MRR — check for 'BroadHub Rev' in column A.")
if subscriber_count == 0:
    st.warning("⚠️ Could not detect Subscriber count — check for 'Users Months' in column A.")
if ebitda_value == 0:
    st.warning("⚠️ Could not detect EBITDA — check for 'EBITDA' in column A.")

# -------------------------------
# DATA TABLE
# -------------------------------
st.subheader(f"📋 Profit & Loss Sheet Preview – {selected_tab}")
# Duplicate column protection before rendering
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
st.caption("© 2025 Pioneer Broadband | Intelligent Profit & Loss Dashboard (Google Sheets API)")
