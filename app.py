import streamlit as st
import pandas as pd
import requests

# -------------------------------
# APP CONFIGURATION
# -------------------------------
st.set_page_config(page_title="Profit & Loss Dashboard", page_icon="💰", layout="wide")
st.title("💰 Pioneer Broadband Profit & Loss Dashboard")
st.caption("Securely synced from Google Sheets via Google Sheets API with KPI tracking for MRR, Subscribers, ARPU, and EBITDA Margin")

# -------------------------------
# GOOGLE SHEETS SETTINGS
# -------------------------------
SHEET_ID = "1iiBe4CLYPlr_kpIOuvzxLliwA0ferGtBRhtnMLfhOQg"
RANGE_NAME = "'Profit & Loss'!A1:Z100"

# Load API key securely from Streamlit secrets
try:
    API_KEY = st.secrets["gcp"]["api_key"]
except Exception:
    st.error("❌ Google API key not found. Please add it in Streamlit secrets under [gcp].")
    st.stop()

# -------------------------------
# LOAD DATA FROM GOOGLE SHEETS API
# -------------------------------
@st.cache_data(ttl=300)
def load_sheet_data(sheet_id, range_name, api_key):
    """Fetch Google Sheet data securely via the Sheets API with smart header detection and duplicate handling."""
    def fetch(url):
        r = requests.get(url)
        if r.status_code != 200:
            raise Exception(f"HTTP {r.status_code}: {r.text}")
        return r.json().get("values", [])

    url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/{range_name}?key={api_key}"
    try:
        data = fetch(url)
    except Exception:
        st.warning("⚠️ Named tab not found. Attempting to load the first sheet instead...")
        fallback_url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/A1:Z100?key={api_key}"
        data = fetch(fallback_url)

    if not data:
        raise Exception("No data returned. Check your range or sheet permissions.")

    # --- Smart header detection ---
    header = data[0]
    if len(header) == 1 and len(data) > 1 and len(data[1]) > 1:
        header = data[1]
        body = data[2:]
    else:
        body = data[1:]

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
    df = load_sheet_data(SHEET_ID, RANGE_NAME, API_KEY)
    st.success("✅ Data loaded successfully from Google Sheets API!")
except Exception as e:
    st.error(f"❌ Failed to load sheet: {e}")
    st.stop()

# -------------------------------
# EXTRACT KPI VALUES
# -------------------------------
def get_numeric_value(df, row_idx, col_idx):
    """Safely extracts and cleans a numeric value from a DataFrame cell."""
    try:
        raw_value = str(df.iat[row_idx, col_idx])
        return pd.to_numeric(raw_value.replace(",", "").replace("$", ""), errors="coerce")
    except Exception:
        return 0

# Row 59 (index 58) = Subscribers
# Row 60 (index 59) = MRR
subscriber_count = get_numeric_value(df, 58, 1)
mrr_value = get_numeric_value(df, 59, 1)

# -------------------------------
# KPI CALCULATIONS
# -------------------------------
arpu_value = (mrr_value / subscriber_count) if subscriber_count > 0 else 0

st.sidebar.header("🔧 KPI Inputs")
ebitda_margin_input = st.sidebar.number_input("EBITDA Margin (%)", min_value=0.0, max_value=100.0, value=0.0)
ebitda_margin_value = ebitda_margin_input

# -------------------------------
# KPI DISPLAY
# -------------------------------
st.header("📊 Key Performance Indicators")
col1, col2, col3, col4 = st.columns(4)
col1.metric("Monthly Recurring Revenue (MRR)", f"${mrr_value:,.2f}")
col2.metric("Subscriber Count", f"{subscriber_count:,.0f}")
col3.metric("Average Revenue Per User (ARPU)", f"${arpu_value:,.2f}")
col4.metric("EBITDA Margin", f"{ebitda_margin_value:.2f}%")

if mrr_value == 0:
    st.warning("⚠️ MRR (Row 60 Col B) may be missing or not numeric.")
if subscriber_count == 0:
    st.warning("⚠️ Subscriber count (Row 59 Col B) may be missing or zero.")

# -------------------------------
# DATA TABLE
# -------------------------------
st.subheader("📋 Profit & Loss Sheet (Preview)")
st.dataframe(df, use_container_width=True)

# -------------------------------
# DOWNLOAD BUTTON
# -------------------------------
st.subheader("⬇️ Download Data")
csv = df.to_csv(index=False).encode("utf-8")
st.download_button("Download Sheet CSV", csv, "profit_loss_data.csv", "text/csv")

st.markdown("---")
st.caption("© 2025 Pioneer Broadband | Secure Profit & Loss Dashboard (Google Sheets API)")
