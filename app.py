import streamlit as st
import pandas as pd
import altair as alt

# --- Page Setup ---
st.set_page_config(page_title="Google Sheet Viewer", page_icon="📄", layout="wide")
st.title("📄 Google Sheet Data Viewer")

# --- Google Sheet URL ---
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1iiBe4CLYPlr_kpIOuvzxLliwA0ferGtBRhtnMLfhOQg/edit?usp=sharing"

# --- Data Loading Function ---
@st.cache_data(ttl=300)
def load_data(sheet_url):
    csv_url = sheet_url.replace("/edit?usp=sharing", "/export?format=csv")
    df = pd.read_csv(csv_url)
    df.columns = df.columns.str.strip()
    return df

# --- Load Data ---
try:
    df = load_data(GOOGLE_SHEET_URL)
    st.success("✅ Data loaded successfully from Google Sheet!")
except Exception as e:
    st.error(f"❌ Failed to load sheet. Check sharing settings. Error: {e}")
    st.stop()

# --- Display Table ---
st.subheader("📋 Data Preview")
st.dataframe(df, use_container_width=True)

# --- Filter Section ---
st.subheader("🔍 Filter Data")
col = st.selectbox("Select a column to filter", df.columns)
val = st.text_input("Enter a value to search")
if st.button("Apply Filter"):
    filtered = df[df[col].astype(str).str.contains(val, case=False, na=False)]
    st.dataframe(filtered, use_container_width=True)
else:
    filtered = df

# --- Optional Chart ---
st.subheader("📈 Quick Visualization")
numeric_cols = df.select_dtypes(include="number").columns.tolist()
if numeric_cols:
    x_col = st.selectbox("X Axis", df.columns)
    y_col = st.selectbox("Y Axis (numeric)", numeric_cols)
    chart = alt.Chart(filtered).mark_bar().encode(
        x=x_col,
        y=y_col,
        tooltip=list(filtered.columns)
    ).properties(height=400)
    st.altair_chart(chart, use_container_width=True)
else:
    st.info("No numeric columns found for charting.")

# --- Download Option ---
csv = filtered.to_csv(index=False).encode("utf-8")
st.download_button("⬇️ Download Filtered CSV", csv, "filtered_data.csv", "text/csv")
