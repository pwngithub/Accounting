import streamlit as st
import pandas as pd
import requests

# -------------------------------
# APP CONFIGURATION
# -------------------------------
st.set_page_config(page_title="Profit & Loss Dashboard", page_icon="💰", layout="wide")
st.title("💰 Pioneer Broadband Profit & Loss Dashboard")
st.caption("Securely synced from Google Sheets via Google Sheets API with monthly tab selection and KPI tracking.")

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
    """Retrieve all sheet/tab names from the Google Sheet."""
    meta_url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}?key={api_key}"
    resp = requests.get(meta_url)
    if resp.status_code != 200:
        raise Exception(f"Failed to get sheet metadata: {resp.text}")
    sheets = resp.json().get("sheets", [])
    return [s["properties"]["title"] for s in sheets]

try:
    sheet_names = get_sheet_tabs(SHEET_ID, API_KEY)
    month_tabs = [name for name in sheet_names if name.startswith("25.")]
    if not month_tabs:
        month_tabs = sheet_names
    selected_tab = st.sidebar.selectbox("📅 Select Month", month_tabs, index=len(month_tabs)-1)
except Exception as e:
    st.error(f"❌ Could not fetch sheet tabs: {e}")
    st.stop()

# -------------------------------
# SMART LOADER
# -------------------------------
@st.cache_data(ttl=300)
def load_sheet_data(sheet_id, tab_name, api_key):
    """Fetch data for the selected month/tab and auto-detect header row."""
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/'{tab_name}'!A1:Z200?key={api_key}"
    resp = requests.get(url)
    if resp.status_code != 200:
        raise Exception(f"Failed to load tab '{tab_name}': {resp.text}")

    data = resp.json().get("values", [])
    if not data:
        raise Exception("No data returned from sheet.")

    # --- Detect header row dynamically ---
    header_row_idx = None
    for i, row in enumerate(data):
        filled_cells = sum(1 for c in row if c.strip() != "")
        if filled_cells >= 3:  # heuristic: likely header row
            header_row_idx = i
            break

    if header_row_idx is None:
        raise Exception("Could not detect header row in sheet.")

    header = data[header_row_idx]
    body = data[header_row_idx + 1:]

    # --- Clean header names and remove duplicates ---
    header = [h.strip() if h else f"Column_{i+1}" for i, h in enumerate(header)]
    seen = {}
    unique_header = []
    for h in header:
        if h in seen:
            seen[h] += 1
            unique_header.append(f"{h}_{seen[h]}")
        else:
            seen[h] = 1
            unique_header.append(h)

    df = pd.DataFrame(body, columns=unique_header)
    return df

try:
    df = load_sheet_data(SHEET_ID, selected_tab, API_KEY)
    st.success(f"✅ Loaded data for **{selected_tab}**")
except Exception as e:
    st.error(f"❌ Failed to load data for {selected_tab}: {e}")
    st.stop()

# -------------------------------
# KPI EXTRACTION
# -------------------------------
def get_numeric_value(df, row_idx, col_idx):
    """Safely extracts and cleans a numeric value from a DataFrame cell."""
    try:
        raw_value = str(df.iat[row_idx, col_idx])
        return pd.to_numeric(raw_value.replace(",", "").replace("$", ""), errors="coerce")
    except Exception:
        return 0

# KPI data references
subscriber_count = get_numeric_value(df, 58, 1)  # Row 59, Col B
mrr_value = get_numeric_value(df, 59, 1)         # Row 60, Col B

# EBITDA calculation = sum of (row 53, col 1) + (row 49, col 1) + (row 31, col 1)
ebitda_value = (
    get_numeric_value(df, 52, 1) +
    get_numeric_value(df, 48, 1) +
    get_numeric_value(df, 30, 1)
)

# -------------------------------
# KPI CALCULATIONS
# -------------------------------
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
    st.warning("⚠️ MRR (Row 60 Col B) may be missing or not numeric.")
if subscriber_count == 0:
    st.warning("⚠️ Subscriber count (Row 59 Col B) may be missing or zero.")

# -------------------------------
# DATA TABLE
# -------------------------------
st.subheader(f"📋 Profit & Loss Sheet Preview – {selected_tab}")
st.dataframe(df, use_container_width=True)

# -------------------------------
# DOWNLOAD BUTTON
# -------------------------------
st.subheader("⬇️ Download Data")
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(f"Download {selected_tab} CSV", csv, f"{selected_tab}_profit_loss.csv", "text/csv")

st.markdown("---")
st.caption("© 2025 Pioneer Broadband | Multi-Month Profit & Loss Dashboard (Google Sheets API)")
