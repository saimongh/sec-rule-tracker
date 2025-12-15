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
    
    /* Input Field Visibility Fix */
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: rgba(0, 0, 0, 0.3) !important;
        color: white !important;
    }
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
        fromdesc="Baseline (Left)",
        todesc="Comparison (Right)",
        context=True,
        numlines=3
    )
    
    # CSS: Dark Mode + Hide Default Junk
    custom_css = """
    <style>
        body { font-family: 'Helvetica Neue', sans-serif; font-size: 13px; color: #ccc; background-color: transparent; }
        table.diff { width: 100%; border-collapse: separate; border-spacing: 0; border: 1px solid #333; border-radius: 8px; }
        .diff_header { background-color: #1a1a1a; color: #888; border: none; }
        td { padding: 8px; border-bottom: 1px solid #222; }
        
        /* High-Contrast Colors */
        .diff_add { background-color: #0f3d1b; color: #84e897; } 
        .diff_sub { background-color: #3d1414; color: #f28b8b; } 
        .diff_chg { background-color: #3d3514; color: #e8d984; }
        
        /* Hide Default Legends/Links */
        a[href^="#"] { display: none !important; }
        table[summary="Legends"] { display: none !important; }
    </style>
    """
    return html.replace('<head>', f'<head>{custom_css}')

# --- THE FIX: Precise String Matching ---
def inject_demo_data(rule_id):
    # We define the COMMON part exactly so it matches 100%
    common_part = """(a) Standards of Commercial Honor and Principles of Trade
A member, in the conduct of its business, shall observe high standards of commercial honor and just and equitable principles of trade.

(b) Prohibition Against Deceptive Practices
No member shall effect any transaction in, or induce the purchase or sale of, any security by means of any manipulative, deceptive or other fraudulent device or contrivance."""

    # The NEW part
    added_part = """

(c) New Requirement (Demo Update)
This section simulates a new regulatory requirement added by the SEC to demonstrate the redline capabilities. Because this text is NOT in the baseline, it will appear GREEN."""

    conn = sqlite3.connect('data/regulations.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rule_versions (id INTEGER PRIMARY KEY AUTOINCREMENT, rule_id TEXT, check_date TEXT, rule_text TEXT, change_summary TEXT)''')
    
    # 1. Clean Slate
    c.execute("DELETE FROM rule_versions WHERE rule_id = ?", (rule_id,))
    
    # 2. Insert Baseline (Just Common Part)
    c.execute("INSERT INTO rule_versions (rule_id, check_date, rule_text, change_summary) VALUES (?, datetime('now', '-1 day'), ?, ?)", 
              (rule_id, common_part, "Historical Baseline (Demo)"))

    # 3. Insert New Version (Common + Added)
    c.execute("INSERT INTO rule_versions (rule_id, check_date, rule_text, change_summary) VALUES (?, datetime('now'), ?, ?)", 
              (rule_id, common_part + added_part, "Live Audit (Demo)"))
    
    conn.commit()
    conn.close()
    return True

# --- APP LOGIC ---
st.sidebar.markdown("### ⚖️ Regulatory Harmony")
rules = get_rules()
if not rules: st.stop()

selected_rule_name = st.sidebar.selectbox("Select Rulebook", list({r['name']: r for r in rules}.keys()))
selected_rule = {r['name']: r for r in rules}[selected_rule_name]

if st.sidebar.button("Run Live Audit", type="primary"):
    with st.spinner("Scanning FINRA..."):
        latest = download_rule(selected_rule['url'])
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
        col_a, col_b = st.columns(2)
        version_options = history_df.apply(lambda x: f"v.{x['id']} — {pd.to_datetime(x['check_date']).strftime('%b %d %H:%M')}", axis=1).tolist()
        version_map = {f"v.{row['id']} — {pd.to_datetime(row['check_date']).strftime('%b %d %H:%M')}": row['id'] for _, row in history_df.iterrows()}
        
        # Smart Default: Left = Oldest (Last item), Right = Newest (First item)
        with col_a: ver_a_label = st.selectbox("Baseline Version", version_options, index=len(version_options)-1)
        with col_b: ver_b_label = st.selectbox("Comparison Version", version_options, index=0)
            
        id_a = version_map[ver_a_label]
        id_b = version_map[ver_b_label]
        text_a = get_specific_version_text(id_a)
        text_b = get_specific_version_text(id_b)
        
        # --- NEW LOCATION: The Legend lives HERE, outside the scroll box ---
        st.markdown("""
        <div style="margin-bottom: 10px; padding: 8px; background: rgba(0,0,0,0.3); border-radius: 6px; display: flex; gap: 15px; font-family: sans-serif; font-size: 11px; color: #aaa; border: 1px solid #444; width: fit-content;">
            <span style="display:flex; align-items:center;"><span style="width:10px; height:10px; background:#0f3d1b; margin-right:5px; border:1px solid #84e897;"></span> Added</span>
            <span style="display:flex; align-items:center;"><span style="width:10px; height:10px; background:#3d1414; margin-right:5px; border:1px solid #f28b8b;"></span> Deleted</span>
            <span style="display:flex; align-items:center;"><span style="width:10px; height:10px; background:#3d3514; margin-right:5px; border:1px solid #e8d984;"></span> Changed</span>
        </div>
        """, unsafe_allow_html=True)

        if text_a == text_b:
            st.info("Versions are identical.")
        else:
            # Smart Resizing
            line_count = max(len(text_a.splitlines()), len(text_b.splitlines()))
            dynamic_height = min(max(300, line_count * 25 + 50), 800)
            components.html(generate_dark_glass_diff(text_a, text_b), height=dynamic_height, scrolling=True)

with tab3:
    st.markdown("##### Current Legal Text")
    try: selected_text_view = get_specific_version_text(version_map[ver_b_label])
    except: selected_text_view = get_specific_version_text(history_df.iloc[0]['id'])
    
    st.code(selected_text_view, language="text")
