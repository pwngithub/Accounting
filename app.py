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
st.caption("Live P&L view with KPIs for MRR, ARPU, and EBITDA Margin")

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
    df = pd.read_csv(csv_url, header=1)  # Headers in 2nd row
    df.columns = df.columns.str.strip()
    return df

try:
    df = load_data(GOOGLE_SHEET_URL)
    st.success("✅ Data loaded successfully from Google Sheet!")
except Exception as e:
    st.error(f"❌ Failed to load sheet. Please ensure it's shared as 'Anyone with link → Viewer'. Error: {e}")
    st.stop()

# -------------------------------
# SIDEBAR FILTERS
# -------------------------------
st.sidebar.header("🔧 Filters & Options")
if st.sidebar.button("🔄 Refresh Data"):
    load_data.clear()
    st.rerun()

# Optional user input
subscriber_count = st.sidebar.number_input("Total Active Subscribers", min_value=1, value=1000)

# Detect likely columns
filter_columns = [col for col in df.columns if any(x in col.lower() for x in ["month", "category", "department"])]

filters = {}
for col in filter_columns:
    unique_vals = sorted(df[col].dropna().unique().tolist())
    selected = st.sidebar.multiselect(f"Filter by {col}:", options=unique_vals, default=unique_vals)
    filters[col] = selected

filtered_df = df.copy()
for col, selected_vals in filters.items():
    filtered_df = filtered_df[filtered_df[col].isin(selected_vals)]

# -------------------------------
# CLEAN NUMERIC COLUMNS
# -------------------------------
amount_cols = [col for col in df.columns if any(x in col.lower() for x in ["income", "revenue", "expense", "profit", "amount", "mrr", "ebitda"])]

for col in amount_cols:
    filtered_df[col] = pd.to_numeric(
        filtered_df[col].astype(str).str.replace("[^0-9.-]", "", regex=True),
        errors="coerce"
    ).fillna(0)

# -------------------------------
# KPI CALCULATIONS
# -------------------------------
total_revenue = filtered_df[[c for c in amount_cols if "revenue" in c.lower() or "income" in c.lower() or "mrr" in c.lower()]].sum().sum()
total_expenses = filtered_df[[c for c in amount_cols if "expense" in c.lower() or "cost" in c.lower()]].sum().sum()
ebitda = filtered_df[[c for c in amount_cols if "ebitda" in c.lower()]].sum().sum()
if ebitda == 0:
    ebitda = total_revenue - total_expenses  # fallback

net_profit = total_revenue - total_expenses
mrr = total_revenue
arpu = mrr / subscriber_count if subscriber_count > 0 else 0
ebitda_margin = (ebitda / total_revenue * 100) if total_revenue else 0

# -------------------------------
# KPI DISPLAY
# -------------------------------
st.header("📊 Key Performance Indicators")

col1, col2, col3 = st.columns(3)
col1.metric("Monthly Recurring Revenue (MRR)", f"${mrr:,.2f}")
col2.metric("Average Revenue Per User (ARPU)", f"${arpu:,.2f}")
col3.metric("EBITDA Margin", f"{ebitda_margin:.2f}%")

# -------------------------------
# SUMMARY TOTALS
# -------------------------------
st.subheader("📋 Summary Totals")

col4, col5, col6 = st.columns(3)
col4.metric("Total Revenue", f"${total_revenue:,.2f}")
col5.metric("Total Expenses", f"${total_expenses:,.2f}")
col6.metric("Net Profit", f"${net_profit:,.2f}", delta=f"{(net_profit / total_revenue * 100):.2f}%" if total_revenue else None)

# -------------------------------
# CHARTS
# -------------------------------
st.subheader("📈 Income vs Expense Over Time")

time_cols = [c for c in df.columns if "month" in c.lower() or "date" in c.lower()]
if time_cols:
    time_col = st.selectbox("Select Time Column:", time_cols)
    melted = filtered_df.melt(
        id_vars=[time_col],
        value_vars=[c for c in amount_cols if "income" in c.lower() or "revenue" in c.lower() or "expense" in c.lower()],
        var_name="Type",
        value_name="Amount"
    )
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
else:
    st.info("No date/month column found for time-based chart.")

# -------------------------------
# DOWNLOAD OPTION
# -------------------------------
st.subheader("⬇️ Download Data")
csv = filtered_df.to_csv(index=False).encode("utf-8")
st.download_button("Download Filtered CSV", csv, "filtered_profit_loss.csv", "text/csv")

st.markdown("---")
st.caption("© 2025 Pioneer Broadband | Live Profit & Loss Dashboard with KPIs")
