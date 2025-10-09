import streamlit as st
import pandas as pd

# -------------------------------
# APP CONFIGURATION
# -------------------------------
st.set_page_config(page_title="Profit & Loss Dashboard", page_icon="💰", layout="wide")
st.title("💰 Pioneer Broadband Profit & Loss Dashboard")
st.caption("Live P&L view synced from Google Sheets with KPI tracking for MRR, Subscribers, ARPU, and EBITDA Margin")

# -------------------------------
# GOOGLE SHEET CONFIG
# -------------------------------
GOOGLE_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/1iiBe4CLYPlr_kpIOuvzxLliwA0ferGtBRhtnMLfhOQg/edit?usp=sharing"
)

# -------------------------------
# LOAD DATA FUNCTION
# -------------------------------
@st.cache_data(ttl=300)
def load_data(sheet_url):
    """Loads the Google Sheet and returns it as a DataFrame (headers in row 2)."""
    csv_url = sheet_url.replace("/edit?usp=sharing", "/export?format=csv")
    df = pd.read_csv(csv_url, header=1)
    df.columns = df.columns.str.strip()
    return df

try:
    df = load_data(GOOGLE_SHEET_URL)
    st.success("✅ Data loaded successfully from Google Sheet!")
except Exception as e:
    st.error(f"❌ Failed to load sheet. Ensure it's shared as 'Anyone with link → Viewer'. Error: {e}")
    st.stop()

# -------------------------------
# EXTRACT KPI VALUES
# -------------------------------
def get_numeric_value(row_idx, col_idx):
    """Safely extracts and cleans a numeric value from the DataFrame."""
    try:
        raw_value = str(df.iat[row_idx, col_idx])
        return pd.to_numeric(raw_value.replace(",", "").replace("$", ""), errors="coerce")
    except Exception:
        return 0

# Row 59 (index 58) = Subscribers
# Row 60 (index 59) = MRR
subscriber_count = get_numeric_value(58, 1)
mrr_value = get_numeric_value(59, 1)

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
    st.warning("⚠️ MRR (Row 60 Col B) is missing or not numeric.")
if subscriber_count == 0:
    st.warning("⚠️ Subscriber count (Row 59 Col B) is missing or zero.")

# -------------------------------
# DATA TABLE
# -------------------------------
st.subheader("📋 Profit & Loss Sheet (Preview)")
st.dataframe(df, use_container_width=True)

# -------------------------------
# DOWNLOAD
# -------------------------------
st.subheader("⬇️ Download Data")
csv = df.to_csv(index=False).encode("utf-8")
st.download_button("Download Sheet CSV", csv, "profit_loss_data.csv", "text/csv")

st.markdown("---")
st.caption("© 2025 Pioneer Broadband | Live Profit & Loss Dashboard")
