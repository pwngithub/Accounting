import streamlit as st
import pandas as pd
import requests
from io import StringIO

# ---------------------------
# CONFIGURATION
# ---------------------------
SHEET_ID = "1iiBe4CLYPlr_kpIOuvzxLliwA0ferGtBRhtnMLfhOQg"
SHEET_GID = "0"  # First tab (change if needed)

def load_google_sheet(sheet_id, gid="0"):
    """Fetch Google Sheet as a DataFrame via CSV export."""
    url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"
    resp = requests.get(url)
    if resp.status_code != 200:
        st.error(f"Failed to load sheet. HTTP {resp.status_code}")
        st.stop()
    csv_str = resp.content.decode("utf-8")
    df = pd.read_csv(StringIO(csv_str))
    return df


def main():
    st.set_page_config(page_title="Pioneer Google Sheet Dashboard", layout="wide")
    st.title("📊 Pioneer Broadband Google Sheet Dashboard")

    # Load data
    with st.spinner("Loading Google Sheet..."):
        df = load_google_sheet(SHEET_ID, SHEET_GID)

    st.success("Data loaded successfully!")

    # Show table
    st.subheader("Full Data Table")
    st.dataframe(df, use_container_width=True)

    # Filter section
    st.subheader("🔍 Filter Data")
    col = st.selectbox("Select a column to filter", df.columns)
    val = st.text_input("Enter a value or keyword to search")
    if st.button("Apply Filter"):
        filtered = df[df[col].astype(str).str.contains(val, case=False, na=False)]
        st.write(f"Filtered results ({len(filtered)} rows):")
        st.dataframe(filtered, use_container_width=True)
    else:
        filtered = df

    # Chart section
    st.subheader("📈 Quick Visualization")
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    if numeric_cols:
        x_axis = st.selectbox("Select X axis", df.columns)
        y_axis = st.selectbox("Select Y axis (numeric)", numeric_cols)
        st.bar_chart(filtered.groupby(x_axis)[y_axis].sum())
    else:
        st.info("No numeric columns available for charting.")

    # Download option
    st.subheader("⬇️ Download Data")
    csv = filtered.to_csv(index=False).encode("utf-8")
    st.download_button("Download Filtered CSV", csv, "filtered_data.csv", "text/csv")

if __name__ == "__main__":
    main()
