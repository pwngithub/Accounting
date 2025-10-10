import streamlit as st
import pandas as pd
import requests
import re

# -------------------------------
# APP CONFIGURATION
# -------------------------------
st.set_page_config(page_title="Profit & Loss Dashboard", page_icon="💰", layout="wide")

# -------------------------------
# SIDEBAR: THEME TOGGLE
# -------------------------------
if "dark_mode" not in st.session_state:
    st.session_state["dark_mode"] = False  # default: light mode

# Dynamic label for sidebar toggle
toggle_label = "🌙 Switch to Dark Mode" if not st.session_state["dark_mode"] else "☀️ Switch to Light Mode"

if st.sidebar.button(toggle_label):
    st.session_state["dark_mode"] = not st.session_state["dark_mode"]
    st.rerun()

# -------------------------------
# COLORS & LOGO SETTINGS
# -------------------------------
if st.session_state["dark_mode"]:
    bg_color = "#000000"
    text_color = "#FFFFFF"
    card_bg = "#1c1c1c"
    border_color = "#1e90ff"
    logo_url = (
        "https://images.squarespace-cdn.com/content/v1/651eb4433b13e72c1034f375/"
        "369c5df0-5363-4827-b041-1add0367f447/PBB+long+logo+white.png?format=1500w"
    )
    float_button_bg = "#1e90ff"
    float_button_text = "#ffffff"
else:
    bg_color = "#FFFFFF"
    text_color = "#000000"
    card_bg = "#ffffff"
    border_color = "#0056b3"
    logo_url = (
        "https://images.squarespace-cdn.com/content/v1/651eb4433b13e72c1034f375/"
        "369c5df0-5363-4827-b041-1add0367f447/PBB+long+logo.png?format=1500w"
    )
    float_button_bg = "#0056b3"
    float_button_text = "#ffffff"

# -------------------------------
# PAGE BACKGROUND + ANIMATION
# -------------------------------
st.markdown(
    f"""
    <style>
    * {{
        transition: background-color 0.3s ease, color 0.3s ease;
    }}
    body {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
    }}
    [data-testid="stAppViewContainer"], [data-testid="stHeader"], [data-testid="stSidebar"] {{
        background-color: {bg_color} !important;
        color: {text_color} !important;
    }}
    div[data-testid="stMarkdownContainer"] p, h1, h2, h3, h4, h5, h6 {{
        color: {text_color} !important;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)

# -------------------------------
# HEADER SECTION
# -------------------------------
st.markdown(
    f"""
    <div style="display:flex;align-items:center;justify-content:flex-start;">
        <img src="{logo_url}" width="258" height="49" style="margin-right:15px;">
    </div>
    <hr style="height:4px;border:none;background-color:{border_color};margin-top:0;margin-bottom:20px;">
    """,
    unsafe_allow_html=True,
)

# -------------------------------
# GOOGLE SHEETS CONFIG
# -------------------------------
SHEET_ID = "1iiBe4CLYPlr_kpIOuvzxLliwA0ferGtBRhtnMLfhOQg"

try:
    API_KEY = st.secrets["gcp"]["api_key"]
except Exception:
    st.error("❌ Google API key not found in Streamlit secrets under [gcp].")
    st.stop()

# -------------------------------
# FETCH SHEET NAMES
# -------------------------------
@st.cache_data(ttl=300)
def get_sheet_tabs(sheet_id, api_key):
    meta_url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}?key={api_key}"
    r = requests.get(meta_url)
    if r.status_code != 200:
        raise Exception(f"Metadata error: {r.text}")
    sheets = r.json().get("sheets", [])
    return [s["properties"]["title"] for s in sheets]

try:
    sheet_names = get_sheet_tabs(SHEET_ID, API_KEY)
    month_tabs = [n for n in sheet_names if n.startswith("25.")]
    if not month_tabs:
        month_tabs = sheet_names
    selected_tab = st.sidebar.selectbox("📅 Select Month", month_tabs, index=len(month_tabs) - 1)
except Exception as e:
    st.error(f"❌ Could not fetch sheet tabs: {e}")
    st.stop()

# -------------------------------
# LOAD SHEET DATA
# -------------------------------
@st.cache_data(ttl=300)
def load_sheet(sheet_id, tab, api_key):
    url = f"https://sheets.googleapis.com/v4/spreadsheets/{sheet_id}/values/'{tab}'!A1:Z200?key={api_key}"
    r = requests.get(url)
    if r.status_code != 200:
        raise Exception(f"Failed to load '{tab}': {r.text}")
    vals = r.json().get("values", [])
    if not vals:
        raise Exception("No data returned.")
    header_row = next((i for i, row in enumerate(vals) if sum(1 for c in row if c.strip()) >= 3), None)
    if header_row is None:
        raise Exception("Header not found.")
    df = pd.DataFrame(vals[header_row + 1:], columns=vals[header_row])
    df.columns = [c.strip() if c else f"Column_{i}" for i, c in enumerate(df.columns)]
    if df.columns.duplicated().any():
        df.columns = [f"{c}_{i}" if df.columns.tolist().count(c) > 1 else c for i, c in enumerate(df.columns)]
    return df

try:
    df = load_sheet(SHEET_ID, selected_tab, API_KEY)
except Exception as e:
    st.error(f"❌ Load error for {selected_tab}: {e}")
    st.stop()

# -------------------------------
# FIND KPI ROWS
# -------------------------------
def find_row(df, keys):
    col = df.iloc[:, 0].astype(str).str.lower()
    for k in keys:
        m = col[col.str.contains(k.lower())]
        if not m.empty:
            return m.index[0]
    return None

def find_col(df, key):
    for i, c in enumerate(df.columns):
        if re.search(key, c, re.IGNORECASE):
            return i
    return None

def num(df, r, c):
    try:
        v = str(df.iat[r, c])
        return pd.to_numeric(v.replace(",", "").replace("$", ""), errors="coerce")
    except Exception:
        return 0

col_idx = find_col(df, "month") or 1
ebitda_r = find_row(df, ["ebitda"])
subs_r = find_row(df, ["users months", "user months"])
mrr_r = find_row(df, ["broadhub rev", "broadhub"])

ebitda = num(df, ebitda_r, col_idx) if ebitda_r is not None else 0
subs = num(df, subs_r, col_idx) if subs_r is not None else 0
mrr = num(df, mrr_r, col_idx) if mrr_r is not None else 0
arpu = (mrr / subs) if subs > 0 else 0

# -------------------------------
# KPI SECTION
# -------------------------------
st.markdown(f"<h2 style='color:{border_color};'>💼 Financial Performance – {selected_tab}</h2>", unsafe_allow_html=True)
c1, c2, c3, c4 = st.columns(4)

def kpi_box(label, value):
    try:
        n = float(str(value).replace("$", "").replace(",", ""))
    except:
        n = 0
    val_color = border_color if n >= 0 else "red"
    return f"""
    <div style="
        background-color:{card_bg};
        border:2px solid {border_color};
        border-radius:10px;
        padding:14px;
        box-shadow:0px 2px 10px rgba(0,86,179,0.15);
        text-align:center;">
        <div style="font-weight:600;color:{text_color};">{label}</div>
        <div style="font-size:1.5em;font-weight:700;color:{val_color};">{value}</div>
    </div>
    """

c1.markdown(kpi_box("Monthly Recurring Revenue (MRR)", f"${mrr:,.2f}"), unsafe_allow_html=True)
c2.markdown(kpi_box("Subscriber Count", f"{subs:,.0f}"), unsafe_allow_html=True)
c3.markdown(kpi_box("Average Revenue Per User (ARPU)", f"${arpu:,.2f}"), unsafe_allow_html=True)
c4.markdown(kpi_box("EBITDA", f"${ebitda:,.2f}"), unsafe_allow_html=True)

# -------------------------------
# SIDEBAR OPTIONS
# -------------------------------
st.sidebar.markdown("---")
show_df = st.sidebar.checkbox("📋 Show Profit & Loss Sheet Preview", False)
if show_df:
    st.subheader(f"📋 Profit & Loss Sheet Preview – {selected_tab}")
    st.dataframe(df, use_container_width=True)

# -------------------------------
# DOWNLOAD BUTTON
# -------------------------------
st.subheader("⬇️ Download Data")
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(f"Download {selected_tab} CSV", csv, f"{selected_tab}_profit_loss.csv", "text/csv")

# -------------------------------
# FLOATING THEME TOGGLE BUTTON
# -------------------------------
float_label = "☀️ Light Mode" if st.session_state["dark_mode"] else "🌙 Dark Mode"
float_action = "light" if st.session_state["dark_mode"] else "dark"

st.markdown(
    f"""
    <div style="
        position: fixed;
        top: 15px;
        right: 20px;
        z-index: 9999;
        background-color: {float_button_bg};
        color: {float_button_text};
        border-radius: 20px;
        padding: 6px 12px;
        font-weight: 600;
        font-size: 14px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        cursor: pointer;
        transition: 0.3s ease;
    "
    onclick="window.parent.postMessage({{'theme_toggle': true}}, '*')">
        {float_label}
    </div>
    """,
    unsafe_allow_html=True,
)

# Inject JS listener to rerun theme toggle
st.components.v1.html(
    """
    <script>
    window.addEventListener('message', (event) => {
        if (event.data.theme_toggle) {
            const streamlitSend = window.parent.Streamlit;
            if (streamlitSend && streamlitSend.setComponentValue) {
                streamlitSend.setComponentValue(true);
            } else {
                window.parent.location.reload();
            }
        }
    });
    </script>
    """,
    height=0,
)

# -------------------------------
# FOOTER
# -------------------------------
st.markdown("---")
st.caption("© 2025 Pioneer Broadband")
