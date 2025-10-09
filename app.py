import streamlit as st
import pandas as pd

st.set_page_config(page_title="P&L Debug", page_icon="🧩", layout="wide")
st.title("🧩 Profit & Loss Sheet Debugger")

GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1iiBe4CLYPlr_kpIOuvzxLliwA0ferGtBRhtnMLfhOQg/edit?usp=sharing"

@st.cache_data(ttl=300)
def load_data(sheet_url):
    csv_url = sheet_url.replace("/edit?usp=sharing", "/export?format=csv")
    df = pd.read_csv(csv_url, header=1)
    df.columns = df.columns.str.strip()
    return df

try:
    df = load_data(GOOGLE_SHEET_URL)
    st.success("✅ Data loaded successfully")
except Exception as e:
    st.error(f"❌ Error loading data: {e}")
    st.stop()

# Show diagnostic info
st.write("📐 DataFrame Shape:", df.shape)
st.write("🧭 Column Indexes:")
for i, col in enumerate(df.columns):
    st.write(f"Column {i}: {col}")

# Show row 11 (index 10)
st.write("📊 Row 11 contents:")
if len(df) > 10:
    row_data = df.iloc[10]
    for idx, val in enumerate(row_data):
        st.write(f"Column {idx}: {val}")
else:
    st.warning("Row 11 (index 10) not found in sheet.")

st.dataframe(df.head(15))
