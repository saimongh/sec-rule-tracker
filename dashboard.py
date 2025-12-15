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
    # If requirements.txt is correct, this shouldn't happen, but we handle it.
    pass 

# --- Configuration ---
st.set_page_config(page_title="Regulatory Harmony", layout="wide", page_icon="🌑")

# --- Styles ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%); background-attachment: fixed; }
    h1, h2, h3, p, label, .stMarkdown { color: #cfcfcf !important; }
    .stButton>button { width: 100%; border-radius: 50px; background: rgba(255, 255, 255, 0.05); color: #ffffff; border: 1px solid rgba(255, 255, 255, 0.2); }
    /* Fix for Tabs visibility */
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
    html = d.make_file(old_text.splitlines(), new_text.splitlines(), fromdesc="Baseline", todesc="Live Audit", context=True, numlines=3)
    return html.replace('<head>', '<head><style>body{font-family:sans-serif;color:#ccc;background:transparent;} .diff_add{background:#0f3d1b;color:#84e897;} .diff_sub{background:#3d1414;color:#f28b8b;} .diff_chg{background:#3d3514;color:#e8d984;}</style>')

# --- THE GUARANTEED FIX: Hardcoded Demo Data ---
def inject_demo_data(rule_id):
    """
    Injects SAFE, KNOWN data into the database.
    Does NOT rely on the internet.
    """
    # 1. The "Past" Version (Missing the last paragraph)
    fake_old_text = """
    (a) Standards of Commercial Honor and Principles of Trade
    A member, in the conduct of its business, shall observe high standards of commercial honor and just and equitable principles of trade.
    
    (b) Prohibition Against Deceptive Practices
    No member shall effect any transaction in, or induce the purchase or sale of, any security by means of any manipulative, deceptive or other fraudulent device or contrivance.
    """
    
    # 2. The "Live" Version (Has the extra paragraph)
    # We won't save this yet, we just want to establish the baseline.
    
    conn = sqlite3.connect('data/regulations.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rule_versions (id INTEGER PRIMARY KEY AUTOINCREMENT, rule_id TEXT, check_date TEXT, rule_text TEXT, change_summary TEXT)''')
    
    # Clear bad data first for this rule
    c.execute("DELETE FROM rule_versions WHERE rule_id = ?", (rule_id,))
    
    # Insert the "Baseline"
    c.execute("INSERT INTO rule_versions (rule_id, check_date, rule_text, change_summary) VALUES (?, datetime('now', '-30 days'), ?, ?)", 
              (rule_id, fake_old_text.strip(), "Historical Baseline (Demo)"))
    
    conn.commit()
    conn.close()
    return True

# --- APP LOGIC ---
st.sidebar.markdown("### ⚖️ Regulatory Harmony")
rules = get_rules()
if not rules: st.stop()

# Rule Selection
selected_rule_name = st.sidebar.selectbox("Select Rulebook", list({r['name']: r for r in rules}.keys()))
selected_rule = {r['name']: r for r in rules}[selected_rule_name]

# --- MAIN BUTTONS ---
if st.sidebar.button("Run Live Audit", type="primary"):
    with st.spinner("Scanning FINRA..."):
        latest = download_rule(selected_rule['url'])
        
        # BLOCK EMPTY DATA
        if len(latest) < 50:
            st.error(f"Audit Failed: {latest}")
        else:
            baseline = get_latest_version(selected_rule['id'])
            # If no baseline exists, save this as baseline
            if not baseline:
                log_new_version(selected_rule['id'], latest, "Initial Baseline")
                st.sidebar.success("Baseline Established")
            # If baseline exists, check for changes
            elif latest != baseline:
                log_new_version(selected_rule['id'], latest, "Audit: Change Detected")
                st.sidebar.warning("Change Logged")
            else:
                st.sidebar.success("Compliant")
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("##### 🛠️ Demo Tools")
if st.sidebar.button("⚠️ Load Test Data (Reset)"):
    # This button now FIXES everything by forcing good data
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
    if len(history_df) < 2:
        st.info("Waiting for a second version to compare... (Click 'Run Live Audit' to generate comparison)")
    else:
        # Compare the two most recent versions
        text_a = get_specific_version_text(history_df.iloc[1]['id']) # Older
        text_b = get_specific_version_text(history_df.iloc[0]['id']) # Newer
        components.html(generate_dark_glass_diff(text_a, text_b), height=600, scrolling=True)

with tab3:
    st.markdown("##### Current Legal Text")
    latest_text = get_specific_version_text(history_df.iloc[0]['id'])
    
    # Use st.code to guarantee visibility (White on Black)
    st.code(latest_text, language="text")
