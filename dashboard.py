# dashboard.py

import streamlit as st
import sqlite3
import pandas as pd
import json
import difflib
import spacy
import os
import streamlit.components.v1 as components
from src.downloader import download_rule
from src.database_manager import get_latest_version, log_new_version

# --- Load NLP Model ---
try:
    nlp = spacy.load("en_core_web_sm")
except OSError:
    pass 

# --- Configuration ---
st.set_page_config(page_title="Regulatory Harmony", layout="wide", page_icon="🌑")

# --- Styles ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); background-attachment: fixed; }
    h1, h2, h3, p, label, .stMarkdown { color: #cfcfcf !important; }
    .stButton>button { width: 100%; border-radius: 50px; background: rgba(255, 255, 255, 0.05); color: #ffffff; border: 1px solid rgba(255, 255, 255, 0.2); }
    .stTabs [data-baseweb="tab"] { color: #888; }
    .stTabs [aria-selected="true"] { background-color: rgba(255,255,255, 0.1) !important; color: #fff !important; }
    </style>
    """, unsafe_allow_html=True)

# --- Helper Functions ---
def get_rules():
    try:
        with open('data/tracked_rules.json', 'r') as f: return json.load(f)
    except FileNotFoundError: return []

def get_history(rule_id):
    if not os.path.exists('data/regulations.db'): return pd.DataFrame()
    conn = sqlite3.connect('data/regulations.db')
    try:
        df = pd.read_sql_query("SELECT id, check_date, length(rule_text) as text_length, change_summary FROM rule_versions WHERE rule_id = ? ORDER BY check_date DESC", conn, params=(rule_id,))
    except Exception: df = pd.DataFrame()
    finally: conn.close()
    return df

def get_specific_version_text(version_id):
    conn = sqlite3.connect('data/regulations.db')
    cursor = conn.cursor()
    cursor.execute("SELECT rule_text FROM rule_versions WHERE id = ?", (version_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else ""

def generate_dark_glass_diff(old_text, new_text):
    d = difflib.HtmlDiff()
    html = d.make_file(
        old_text.splitlines(),
        new_text.splitlines(),
        fromdesc="Baseline",
        todesc="Selected Version",
        context=True,
        numlines=3
    )
    # DARK MODE CSS + HIDE UGLY LINKS
    custom_css = """
    <style>
        body { font-family: 'Helvetica Neue', sans-serif; font-size: 13px; color: #ccc; background-color: transparent; }
        table.diff { width: 100%; border-collapse: separate; border-spacing: 0; border: 1px solid #333; border-radius: 8px; }
        .diff_header { background-color: #1a1a1a; color: #888; border: none; }
        td { padding: 8px; border-bottom: 1px solid #222; }
        .diff_add { background-color: #0f3d1b; color: #84e897; } 
        .diff_sub { background-color: #3d1414; color: #f28b8b; } 
        .diff_chg { background-color: #3d3514; color: #e8d984; }
        
        /* HIDE THE UGLY 't' LINKS AND LEGEND */
        a[href^="#"] { display: none !important; } /* Hides the 't' links */
        table[summary="Legends"] { display: none !important; } /* Hides the bottom legend */
    </style>
    """
    return html.replace('<head>', f'<head>{custom_css}')

# --- THE GUARANTEED FIX: Hardcoded Demo Data ---
def inject_demo_data(rule_id):
    """
    Injects SAFE, KNOWN data into the database.
    """
    # 1. The "Past" Version (Missing the last paragraph)
    fake_old_text = """(a) Standards of Commercial Honor and Principles of Trade
A member, in the conduct of its business, shall observe high standards of commercial honor and just and equitable principles of trade.

(b) Prohibition Against Deceptive Practices
No member shall effect any transaction in, or induce the purchase or sale of, any security by means of any manipulative, deceptive or other fraudulent device or contrivance."""
    
    # 2. The "Live" Version (Full Text)
    fake_new_text = """(a) Standards of Commercial Honor and Principles of Trade
A member, in the conduct of its business, shall observe high standards of commercial honor and just and equitable principles of trade.

(b) Prohibition Against Deceptive Practices
No member shall effect any transaction in, or induce the purchase or sale of, any security by means of any manipulative, deceptive or other fraudulent device or contrivance.

(c) New Requirement (Demo Update)
This section simulates a new regulatory requirement added by the SEC to demonstrate the redline capabilities."""
    
    conn = sqlite3.connect('data/regulations.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rule_versions (id INTEGER PRIMARY KEY AUTOINCREMENT, rule_id TEXT, check_date TEXT, rule_text TEXT, change_summary TEXT)''')
    
    # Clear bad data
    c.execute("DELETE FROM rule_versions WHERE rule_id = ?", (rule_id,))
    
    # Insert Baseline (Yesterday)
    c.execute("INSERT INTO rule_versions (rule_id, check_date, rule_text, change_summary) VALUES (?, datetime('now', '-1 day'), ?, ?)", 
              (rule_id, fake_old_text, "Historical Baseline (Demo)"))

    # Insert New Version (Today)
    c.execute("INSERT INTO rule_versions (rule_id, check_date, rule_text, change_summary) VALUES (?, datetime('now'), ?, ?)", 
              (rule_id, fake_new_text, "Live Audit (Demo)"))
    
    conn.commit()
    conn.close()
    return True

# --- APP LOGIC ---
st.sidebar.markdown("### ⚖️ Regulatory Harmony")
rules = get_rules()
if not rules: st.stop()

selected_rule_name = st.sidebar.selectbox("Select Rulebook", list({r['name']: r for r in rules}.keys()))
selected_rule = {r['name']: r for r in rules}[selected_rule_name]

# --- MAIN BUTTONS ---
if st.sidebar.button("Run Live Audit", type="primary"):
    with st.spinner("Scanning FINRA..."):
        latest = download_rule(selected_rule['url'])
        
        # GATEKEEPER: Don't save empty data or error messages
        if not latest or len(latest) < 50 or "Error" in latest:
            st.error(f"Audit Failed: {latest}")
        else:
            baseline = get_latest_version(selected_rule['id'])
            if not baseline:
                log_new_version(selected_rule['id'], latest, "Initial Baseline")
                st.sidebar.success("Baseline Established")
            elif latest != baseline:
                log_new_version(selected_rule['id'], latest, "Audit: Change Detected")
                st.sidebar.warning("Change Logged")
            else:
                st.sidebar.success("Compliant")
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("##### 🛠️ Demo Tools")
if st.sidebar.button("⚠️ Load Test Data (Reset)"):
    inject_demo_data(selected_rule['id'])
    st.sidebar.success("System Reset: Demo Data Loaded.")
    st.rerun()

# --- MAIN DISPLAY ---
st.title(selected_rule_name)
history_df = get_history(selected_rule['id'])

if history_df.empty:
    st.info("System Ready. Please click '⚠️ Load Test Data' in the sidebar to initialize.")
    st.stop()

# Tabs
tab1, tab2, tab3 = st.tabs(["Overview", "Redline Analysis", "Raw Text"])

with tab1:
    st.metric("Versions Archived", len(history_df))
    st.metric("Latest Update", pd.to_datetime(history_df['check_date'].iloc[0]).strftime('%b %d %H:%M'))
    st.line_chart(history_df.set_index('check_date')['text_length'])

with tab2:
    st.markdown("##### Visual Comparison Engine")
    
    if len(history_df) < 2:
        st.warning("⚠️ Insufficient data for comparison.")
    else:
        # --- RESTORED FEATURE: Dropdown Selectors ---
        col_a, col_b = st.columns(2)
        
        # Create friendly labels for the dropdowns
        version_options = history_df.apply(lambda x: f"v.{x['id']} — {pd.to_datetime(x['check_date']).strftime('%b %d %H:%M')}", axis=1).tolist()
        # Map labels back to IDs
        version_map = {f"v.{row['id']} — {pd.to_datetime(row['check_date']).strftime('%b %d %H:%M')}": row['id'] for _, row in history_df.iterrows()}
        
        with col_a:
            # Default to 2nd newest (Baseline)
            ver_a_label = st.selectbox("Baseline Version", version_options, index=1 if len(version_options) > 1 else 0)
        with col_b:
            # Default to newest (Comparison)
            ver_b_label = st.selectbox("Comparison Version", version_options, index=0)
            
        id_a = version_map[ver_a_label]
        id_b = version_map[ver_b_label]
        
        text_a = get_specific_version_text(id_a)
        text_b = get_specific_version_text(id_b)
        
        if text_a == text_b:
            st.info("Versions are identical.")
        else:
            components.html(generate_dark_glass_diff(text_a, text_b), height=600, scrolling=True)

with tab3:
    st.markdown("##### Current Legal Text")
    
    # Show the text of the VERSION SELECTED IN TAB 2 (or latest if not set)
    # This keeps the tabs synced.
    try:
        selected_text_view = get_specific_version_text(version_map[ver_b_label])
    except:
        selected_text_view = get_specific_version_text(history_df.iloc[0]['id'])

    # Debug info to prove data exists
    st.caption(f"Showing content for selected version. Length: {len(selected_text_view)} chars")
    
    if len(selected_text_view) == 0:
        st.error("The database contains an empty entry for this version. Please Reset Data.")
    else:
        st.code(selected_text_view, language="text")
