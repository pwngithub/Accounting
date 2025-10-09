import streamlit as st
import pandas as pd
import altair as alt

# -------------------------------
# APP CONFIGURATION
# -------------------------------
st.set_page_config(
    page_title="Profit & Loss Dashboard",
    page_icon="💰",
    layout="wide"
)

st.title("💰 Pioneer Broadband Profit & Loss Dashboard")
st.caption("Live P&L view synced from Google Sheets with KPI tracking for MRR, ARPU, and EBITDA Margin")

# -------------------------------
# GOOGLE SHEET CONFIG
# -------------------------------
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1iiBe4CLYPlr_kpIOuvzxLliwA0ferGtBRhtnMLfhOQg/edit?usp=sharing"

# -------------------------------
# LOAD DATA FUNCTION
# -------------------------------
@st.cache_data(ttl=300)
def load_data(sheet_url):
    csv_url = sheet_url.replace("/edit?usp=sharing", "/export?format=csv")
    df = pd.read_csv(csv_url, header=1)
    df.columns = df.columns.str.strip()
    return df

try:
    df = load_data(GOOGLE_SHEET_URL)
    st.success("✅ Data loaded successfully from Google Sheet!")
except Exception as e:
    st.error(f"❌ Failed to load sheet. Please ensure it's shared as 'Anyone with link → Viewer'. Error: {e}")
    st.stop()

# -------------------------------
# EXTRACT KPI VALUES FROM CELLS
# -------------------------------
# Ensure we have enough rows/columns before attempting to read
try:
    mrr_value = pd.to_numeric(str(df.iat[13, 5]).replace(",", "").replace("$", ""), errors="coerce")
except Exception:
    mrr_value = 0

# Sidebar input for subscriber count
st.sidebar.header("🔧 KPI Inputs")
subscriber_count = st.sidebar.number_input("Total Active Subscribers", min_value=1, value=1000)

# If EBITDA Margin exists in sheet, find it
ebitda_margin_col = [col for col in df.columns if "ebitda" in col.lower()]
if ebitda_margin_col:
    try:
        ebitda_margin_value = pd.to_numeric(str(df[ebitda_margin_col[0]].iloc[13]).replace("%", ""), errors="coerce")
    except Exception:
        ebitda_margin_value = 0
else:
    ebitda_margin_value = 0

# Calculate ARPU
arpu_value = mrr_value / subscriber_count if subscriber_count > 0 else 0

# -------------------------------
# DISPLAY KPI METRICS
# -------------------------------
st.header("📊 Key Performance Indicators")
col1, col2, col3 = st.columns(3)
col1.metric("Monthly Recurring Revenue (MRR)", f"${mrr_value:,.2f}")
col2.metric("Average Revenue Per User (ARPU)", f"${arpu_value:,.2f}")
col3.metric("EBITDA Margin", f"{ebitda_margin_value:.2f}%")

# -------------------------------
# SHOW TABLE BELOW
# -------------------------------
st.subheader("📋 Profit & Loss Sheet (Preview)")
st.dataframe(df, use_container_width=True)

# -------------------------------
# OPTIONAL: Chart (if 'Month' or 'Date' exists)
# -------------------------------
time_cols = [c for c in df.columns if "month" in c.lower() or "date" in c.lower()]
amount_cols = [c for c in df.columns if any(x in c.lower() for x in ["income", "revenue", "expense", "profit", "amount"])]

if time_cols and amount_cols:
    st.subheader("📈 Revenue & Expense Trend")
    time_col = time_cols[0]
    melted = df.melt(id_vars=[time_col], value_vars=amount_cols, var_name="Type", value_name="Amount")
    melted["Amount"] = pd.to_numeric(melted["Amount"].astype(str).str.replace("[^0-9.-]", "", regex=True), errors="coerce")
    chart = (
        alt.Chart(melted)
        .mark_line(point=True)
        .encode(
            x=alt.X(time_col, title="Period"),
            y=alt.Y("Amount:Q", title="Amount ($)"),
            color="Type:N",
            tooltip=[time_col, "Type", "Amount"]
        )
        .properties(height=400)
    )
    st.altair_chart(chart, use_container_width=True)

# -------------------------------
# DOWNLOAD OPTION
# -------------------------------
st.subheader("⬇️ Download Data")
csv = df.to_csv(index=False).encode("utf-8")
st.download_button("Download Sheet CSV", csv, "profit_loss_data.csv", "text/csv")

st.markdown("---")
st.caption("© 2025 Pioneer Broadband | Live Profit & Loss Dashboard with KPIs")
