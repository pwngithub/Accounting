import streamlit as st
import pandas as pd
import altair as alt
from datetime import datetime

# --- Page Configuration ---
st.set_page_config(
    page_title="Project Dashboard",
    page_icon="🚀",
    layout="wide"
)

# --- Logo and App Title ---
logo_url_main = "https://images.squarespace-cdn.com/content/v1/651eb4433b13e72c1034f375/369c5df0-5363-4827-b041-1add0367f447/PBB+long+logo.png?format=1500w" 
st.image(logo_url_main)

st.title("🚀 Project Performance Dashboard")
st.markdown("An interactive dashboard to monitor project progress from a live Google Sheet.")
st.info("ℹ️ This dashboard automatically refreshes every 5 minutes. You can also use the manual refresh button in the sidebar.")

# --- Data Loading Function ---
@st.cache_data(ttl=300)
def load_data(sheet_url):
    try:
        csv_url = sheet_url.replace("/edit?usp=sharing", "/export?format=csv")
        df = pd.read_csv(csv_url)
        df.columns = df.columns.str.strip()
        return df
    except Exception as e:
        st.error(f"Failed to load data. Please ensure the Google Sheet is public. Error: {e}")
        return None

# --- Google Sheet URL ---
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1iiBe4CLYPlr_kpIOuvzxLliwA0ferGtBRhtnMLfhOQg/edit?usp=sharing"

# --- Data Processing Function ---
def process_data(df):
    df_processed = df.copy()
    required_cols = ['Type', 'Design', 'As Built']
    if not all(col in df_processed.columns for col in required_cols):
        missing = [col for col in required_cols if col not in df_processed.columns]
        st.warning(f"Missing required columns for KPI calculation: {', '.join(missing)}")
        return None

    df_processed.dropna(subset=['Type'], inplace=True)
    df_processed['Type'] = df_processed['Type'].astype(str).str.replace(':', '', regex=False).str.strip().str.title()
    
    for col in ['Design', 'As Built']:
        df_processed[col] = df_processed[col].astype(str).str.replace(',', '', regex=False)
        df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce').fillna(0)
    
    kpi_summary = df_processed.groupby('Type').agg({
        'Design': 'sum',
        'As Built': 'sum'
    }).reset_index()

    kpi_summary['Completion %'] = 0
    mask = kpi_summary['Design'] > 0
    kpi_summary.loc[mask, 'Completion %'] = (kpi_summary.loc[mask, 'As Built'] / kpi_summary.loc[mask, 'Design']) * 100
    kpi_summary['Completion %'] = kpi_summary['Completion %'].clip(0, 100)
    kpi_summary['Left to be Built'] = kpi_summary['Design'] - kpi_summary['As Built']
    
    return kpi_summary

# --- Main App Logic ---
dataframe = load_data(GOOGLE_SHEET_URL)

if dataframe is not None:
    kpi_data = process_data(dataframe)
    
    if kpi_data is not None:
        st.sidebar.header("Controls & Filters")
        if st.sidebar.button("🔄 Refresh Data"):
            load_data.clear()
            st.rerun()
            
        st.sidebar.header("Filter Options")
        all_types = sorted(kpi_data['Type'].unique())
        selected_types = st.sidebar.multiselect(
            "Select Project Type(s):",
            options=all_types,
            default=all_types
        )
        
        filtered_kpi_data = kpi_data[kpi_data['Type'].isin(selected_types)]

        st.header("📊 Overall Project Health")
        total_design = filtered_kpi_data['Design'].sum()
        total_as_built = filtered_kpi_data['As Built'].sum()
        total_left = filtered_kpi_data['Left to be Built'].sum()
        overall_completion = (total_as_built / total_design * 100) if total_design > 0 else 0
        
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Design", f"{total_design:,.0f}")
        col2.metric("Total As Built", f"{total_as_built:,.0f}")
        col3.metric("Left to be Built", f"{total_left:,.0f}")
        col4.metric("Overall Completion", f"{overall_completion:.2f}%")

        st.header("🏗️ Completion by Project Type")
        if not filtered_kpi_data.empty:
            chart = alt.Chart(filtered_kpi_data).mark_bar().encode(
                x=alt.X('Completion %:Q', title='Completion Percentage', scale=alt.Scale(domain=[0, 100])),
                y=alt.Y('Type:N', sort='-x', title='Project Type'),
                tooltip=['Type', 'Completion %', 'As Built', 'Design']
            ).properties(title='Completion Percentage by Type')
            
            text = chart.mark_text(
                align='left',
                baseline='middle',
                dx=3
            ).encode(text=alt.Text('Completion %:Q', format='.2f'))

            st.altair_chart(chart + text, use_container_width=True)

            for index, row in filtered_kpi_data.iterrows():
                with st.container(border=True):
                    st.subheader(f"{row['Type']}")
                    st.progress(int(row['Completion %']))
                    kpi_col1, kpi_col2, kpi_col3 = st.columns(3)
                    kpi_col1.metric("Completion", f"{row['Completion %']:.2f}%")
                    kpi_col2.metric("As Built", f"{row['As Built']:,.2f}")
                    kpi_col3.metric("Left to be Built", f"{row['Left to be Built']:,.2f}")
        else:
            st.info("No data to display for the selected project types.")

    with st.expander("🔍 View Raw Data Table"):
        columns_to_show = [col for col in dataframe.columns if not col.startswith('Unnamed')]
        display_df = dataframe[columns_to_show]
        st.dataframe(display_df)
else:
    st.warning("Could not display data. Please check the sheet's sharing settings and the URL.")
