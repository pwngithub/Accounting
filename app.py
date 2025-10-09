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
st.caption("Live P&L view synced from Google Sheets")

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
    df = pd.read_csv(csv_url)
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

# Detect likely columns for filters
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
# DISPLAY TABLE
# -------------------------------
st.subheader("📋 Profit & Loss Table")
st.dataframe(filtered_df, use_container_width=True)

# -------------------------------
# SUMMARY TOTALS
# -------------------------------
st.subheader("📊 Summary Totals")

# Auto-detect likely columns for amounts
amount_cols = [col for col in df.columns if any(x in col.lower() for x in ["income", "revenue", "expense", "profit", "amount"])]

if amount_cols:
    st.write("Detected financial columns:", ", ".join(amount_cols))
else:
    st.warning("No financial amount columns detected. Check your sheet headers.")
    amount_cols = []

# Try to detect income and expense automatically
income_cols = [c for c in amount_cols if "income" in c.lower() or "revenue" in c.lower()]
expense_cols = [c for c in amount_cols if "expense" in c.lower() or "cost" in c.lower()]
profit_cols = [c for c in amount_cols if "profit" in c.lower()]

total_income = filtered_df[income_cols].sum().sum() if income_cols else 0
total_expense = filtered_df[expense_cols].sum().sum() if expense_cols else 0
net_profit = total_income - total_expense if total_income or total_expense else filtered_df[profit_cols].sum().sum() if profit_cols else 0

col1, col2, col3 = st.columns(3)
col1.metric("Total Income", f"${total_income:,.2f}")
col2.metric("Total Expenses", f"${total_expense:,.2f}")
col3.metric("Net Profit", f"${net_profit:,.2f}", delta=f"{(net_profit / total_income * 100):.2f}%" if total_income else None)

# -------------------------------
# CHARTS
# -------------------------------
st.subheader("📈 Income vs Expense Over Time")

time_cols = [c for c in df.columns if "month" in c.lower() or "date" in c.lower()]
if time_cols:
    time_col = st.selectbox("Select Time Column:", time_cols)
    if income_cols or expense_cols:
        melted = filtered_df.melt(id_vars=[time_col], value_vars=income_cols + expense_cols, var_name="Type", value_name="Amount")
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

# -------------------------------
# FOOTER
# -------------------------------
st.markdown("---")
st.caption("© 2025 Pioneer Broadband | Live Profit & Loss Dashboard")
