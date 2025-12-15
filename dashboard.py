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
    st.error("Model not found. Please ensure it is in requirements.txt")

# --- Configuration ---
st.set_page_config(page_title="Regulatory Harmony", layout="wide", page_icon="🌑")

# --- Dieter Rams x Dark Glass Design System ---
st.markdown("""
    <style>
    /* 1. THE CANVAS: Deep, dark midnight gradient */
    .stApp {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        background-attachment: fixed;
    }

    /* 2. THE GLASS: Dark, frosted cards */
    div[data-testid="stMetric"], div[data-testid="stExpander"] {
        background-color: rgba(0, 0, 0, 0.3);
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.08);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        padding: 15px !important;
    }

    /* Metric Values */
    div[data-testid="stMetricValue"] {
        color: #e0e0e0 !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #a0a0a0 !important;
    }

    /* 3. THE SIDEBAR */
    section[data-testid="stSidebar"] {
        background-color: rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* 4. TYPOGRAPHY */
    h1, h2, h3 {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 200 !important;
        color: #ffffff !important;
        letter-spacing: 0.5px;
    }
    p, label, .stMarkdown {
        color: #cfcfcf;
        font-weight: 300;
    }

    /* 5. INTERACTION: Ghost Buttons */
    .stButton>button {
        width: 100%;
        border-radius: 50px;
        background: rgba(255, 255, 255, 0.05);
        color: #ffffff;
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background: rgba(255, 255, 255, 0.15);
        border-color: #ffffff;
        box-shadow: 0 0 15px rgba(255,255,255,0.1);
    }

    /* 6. TABS */
    .stTabs [data-baseweb="tab"] {
        color: #888;
    }
    .stTabs [aria-selected="true"] {
        background-color: rgba(255,255,255, 0.1) !important;
        color: #fff !important;
        border-radius: 10px;
    }

    /* 7. INPUT FIELDS (The Fix) */
    .stTextArea textarea {
        background-color: rgba(0, 0, 0, 0.3) !important;
        color: #ffffff !important; /* Force White Text */
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .stSelectbox div[data-baseweb="select"] > div {
        background-color: rgba(0, 0, 0, 0.3) !important;
        color: white !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- Helper Functions ---
def get_rules():
    try:
        with open('data/tracked_rules.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def get_history(rule_id):
    if not os.path.exists('data/regulations.db'):
        return pd.DataFrame()
    conn = sqlite3.connect('data/regulations.db')
    try:
        df = pd.read_sql_query(
            "SELECT id, check_date, length(rule_text) as text_length, change_summary FROM rule_versions WHERE rule_id = ? ORDER BY check_date DESC",
            conn, params=(rule_id,))
    except Exception:
        df = pd.DataFrame()
    finally:
        conn.close()
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
        fromdesc="Baseline (Past)",
        todesc="Live Audit (Current)",
        context=True,
        numlines=3
    )
    custom_css = """
    <style>
        body { font-family: 'Helvetica Neue', sans-serif; font-size: 13px; color: #ccc; background-color: transparent; }
        table.diff { width: 100%; border-collapse: separate; border-spacing: 0; border: 1px solid #333; border-radius: 8px; }
        .diff_header { background-color: #1a1a1a; color: #888; border: none; }
        td { padding: 8px; border-bottom: 1px solid #222; }
        .diff_add { background-color: #0f3d1b; color: #84e897; } 
        .diff_sub { background-color: #3d1414; color: #f28b8b; } 
        .diff_chg { background-color: #3d3514; color: #e8d984; } 
    </style>
    """
    return html.replace('<head>', f'<head>{custom_css}')

# --- SIMULATION ENGINE ---
def inject_demo_data(rule_id, rule_url):
    """
    Creates a fake 'past' version of the rule by removing the last paragraph.
    """
    real_text = download_rule(rule_url)
    
    # Handle case where scraper returns an error string
    if not real_text or "Error" in real_text:
        st.sidebar.error("Could not download rule for simulation. Check scraper.")
        return False
    
    # Create a 'truncated' version
    lines = real_text.split('\n')
    cutoff = int(len(lines) * 0.8) 
    fake_old_text = "\n".join(lines[:cutoff])
    
    conn = sqlite3.connect('data/regulations.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rule_versions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  rule_id TEXT,
                  check_date TEXT,
                  rule_text TEXT,
                  change_summary TEXT)''')
    
    c.execute("INSERT INTO rule_versions (rule_id, check_date, rule_text, change_summary) VALUES (?, datetime('now', '-30 days'), ?, ?)",
              (rule_id, fake_old_text, "Historical Baseline (Demo)"))
    conn.commit()
    conn.close()
    return True

# --- Sidebar ---
st.sidebar.markdown("### ⚖️ Regulatory Harmony")
rules = get_rules()
if not rules:
    st.error("No rules loaded.")
    st.stop()

rule_options = {r['name']: r for r in rules}
selected_rule_name = st.sidebar.selectbox("Select Rulebook", list(rule_options.keys()))
selected_rule = rule_options[selected_rule_name]

st.sidebar.markdown(f"""
<div style='background: rgba(255,255,255,0.05); padding: 15px; border-radius: 15px; font-size: 12px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px;'>
    <strong style='color: #fff'>Tracking ID:</strong> <span style='color:#aaa'>{selected_rule['id']}</span><br>
    <a href="{selected_rule['url']}" style="color: #4da6ff; text-decoration: none;">View Official Source →</a>
</div>
""", unsafe_allow_html=True)

# MAIN BUTTONS
if st.sidebar.button("Run Live Audit", type="primary"):
    with st.spinner("Connecting to FINRA..."):
        latest = download_rule(selected_rule['url'])
        
        # Guard clause: Don't save if it's an error message unless it's the only data we have
        if "Error:" in latest:
             st.error(latest)
        else:
            baseline = get_latest_version(selected_rule['id'])
            
            if not baseline:
                log_new_version(selected_rule['id'], latest, "Initial Baseline")
                st.sidebar.success("Baseline Established")
            elif latest != baseline:
                log_new_version(selected_rule['id'], latest, "Audit: Change Detected")
                st.sidebar.warning("Change Logged")
            else:
                st.sidebar.success("Compliant - No Changes")
            st.rerun()

st.sidebar.markdown("---")
st.sidebar.markdown("##### 🛠️ Demo Tools")
if st.sidebar.button("⚠️ Load Test Data"):
    with st.spinner("Generating historical simulation..."):
        success = inject_demo_data(selected_rule['id'], selected_rule['url'])
        if success:
            st.sidebar.success("Test Data Loaded! Now click 'Run Live Audit'.")
            st.rerun()

# --- Main Page ---
st.title(selected_rule_name)
st.markdown("Regulatory Compliance Monitor")

history_df = get_history(selected_rule['id'])

if history_df.empty:
    st.info("System Ready. Please Initialize via Sidebar.")
    st.stop()

# Tabs
tab1, tab2, tab3 = st.tabs(["Overview", "Redline Analysis", "Raw Text"])

with tab1:
    col1, col2, col3 = st.columns(3)
    col1.metric("Versions Archived", len(history_df))
    col2.metric("Latest Update", pd.to_datetime(history_df['check_date'].iloc[0]).strftime('%b %d, %Y'))
    col3.metric("Char Count", history_df['text_length'].iloc[0])
    
    st.markdown("##### Compliance Timeline")
    st.line_chart(history_df.set_index('check_date')['text_length'])

with tab2:
    st.markdown("##### Visual Comparison Engine")
    
    if len(history_df) < 2:
        st.warning("⚠️ Insufficient data for comparison. Run a Live Audit again to generate a new version.")
    else:
        col_a, col_b = st.columns(2)
        version_options = history_df.apply(lambda x: f"v.{x['id']} — {pd.to_datetime(x['check_date']).strftime('%b %d %H:%M')}", axis=1).tolist()
        version_map = {f"v.{row['id']} — {pd.to_datetime(row['check_date']).strftime('%b %d %H:%M')}": row['id'] for _, row in history_df.iterrows()}
        
        with col_a:
            ver_a_label = st.selectbox("Baseline Version", version_options, index=1)
        with col_b:
            ver_b_label = st.selectbox("Comparison Version", version_options, index=0)
            
        id_a = version_map[ver_a_label]
        id_b = version_map[ver_b_label]
        
        text_a = get_specific_version_text(id_a)
        text_b = get_specific_version_text(id_b)
        
        if text_a == text_b:
            st.info("Versions are identical.")
        else:
            html_diff = generate_dark_glass_diff(text_a, text_b)
            components.html(html_diff, height=600, scrolling=True)

with tab3:
    st.markdown("##### Current Legal Text")
    latest_text = get_specific_version_text(history_df.iloc[0]['id'])
    st.text_area("Content", latest_text, height=600, label_visibility="collapsed")
