import streamlit as st
import pandas as pd
import altair as alt

# -------------------------------
# APP CONFIGURATION
# -------------------------------
st.set_page_config(page_title="Profit & Loss Dashboard", page_icon="💰", layout="wide")
st.title("💰 Pioneer Broadband Profit & Loss Dashboard")
st.caption("Live P&L view synced from Google Sheets with KPI tracking for MRR, ARPU, and EBITDA Margin")

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
    st.error(
        f"❌ Failed to load sheet. Ensure it's shared as 'Anyone with link → Viewer'. Error: {e}"
    )
    st.stop()

# -------------------------------
# EXTRACT KPI VALUES
# -------------------------------
try:
    # Row 12 (index 11), Column 7 (index 6)
    raw_value = str(df.iat[11, 6])
    mrr_value = pd.to_numeric(raw_value.replace(",", "").replace("$", ""), errors="coerce")
    if pd.isna(mrr_value):
        mrr_value = 0
except Exception:
    mrr_value = 0

# Sidebar inputs
st.sidebar.header("🔧 KPI Inputs")
subscriber_count = st.sidebar.number_input("Total Active Subscribers", min_value=1, value=1000)
ebitda_margin_input = st.sidebar.number_input("EBITDA Margin (%)", min_value=0.0, max_value=100.0, value=0.0)

# KPI calculations
arpu_value = mrr_value / subscriber_count if subscriber_count > 0 else 0
ebitda_margin_value = ebitda_margin_input

# -------------------------------
# KPI DISPLAY
# -------------------------------
st.header("📊 Key Performance Indicators")
col1, col2, col3 = st.columns(3)
col1.metric("Monthly Recurring Revenue (MRR)", f"${mrr_value:,.2f}")
col2.metric("Average Revenue Per User (ARPU)", f"${arpu_value:,.2f}")
col3.metric("EBITDA Margin", f"{ebitda_margin_value:.2f}%")

# -------------------------------
# DATA TABLE
# -------------------------------
st.subheader("📋 Profit & Loss Sheet (Preview)")
st.dataframe(df, use_container_width=True)

# -------------------------------
# OPTIONAL CHART
# -------------------------------
time_cols = [c for c in df.columns if "month" in c.lower() or "date" in c.lower()]
amount_cols = [c for c in df.columns if any(x in c.lower() for x in ["income", "revenue", "expense", "profit", "amount"])]

if time_cols and amount_cols:
    st.subheader("📈 Revenue & Expense Trend")
    time_col = time_cols[0]
    melted = df.melt(id_vars=[time_col], value_vars=amount_cols, var_name="Type", value_name="Amount")
    melted["Amount"] = pd.to_numeric(
        melted["Amount"].astype(str).str.replace("[^0-9.-]", "", regex=True),
        errors="coerce"
    )
    chart = (
        alt.Chart(melted)
        .mark_line(point=True)
        .encode(
            x=alt.X(time_col, title="Period"),
            y=alt.Y("Amount:Q", title="Amount ($)"),
            color="Type:N",
            tooltip=[time_col, "Type", "Amount"],
        )
        .properties(height=400)
    )
    st.altair_chart(chart, use_container_width=True)

# -------------------------------
# DOWNLOAD
# -------------------------------
st.subheader("⬇️ Download Data")
csv = df.to_csv(index=False).encode("utf-8")
st.download_button("Download Sheet CSV", csv, "profit_loss_data.csv", "text/csv")

st.markdown("---")
st.caption("© 2025 Pioneer Broadband | Live Profit & Loss Dashboard with KPIs")
