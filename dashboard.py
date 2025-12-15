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

# --- Load NLP Model (Standard Way) ---
# We rely on requirements.txt to install this beforehand
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
        background-color: rgba(0, 0, 0, 0.3); /* Dark tint */
        backdrop-filter: blur(15px);
        -webkit-backdrop-filter: blur(15px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.08); /* Subtle border */
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

    /* 3. THE SIDEBAR: Deepest glass layer */
    section[data-testid="stSidebar"] {
        background-color: rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(20px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    
    /* 4. TYPOGRAPHY: Crisp Silver/White */
    h1, h2, h3 {
        font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
        font-weight: 200 !important;
        color: #ffffff !important;
        letter-spacing: 0.5px;
    }
    p, label, .stMarkdown {
        color: #cfcfcf; /* Soft white */
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
    </style>
    """, unsafe_allow_html=True)

# --- Helper Functions ---
def get_rules():
    try:
        # Load from the local JSON file
        with open('data/tracked_rules.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return []

def get_history(rule_id):
    # Ensure DB exists (for cloud deployments)
    if not os.path.exists('data/regulations.db'):
        return pd.DataFrame()
        
    conn = sqlite3.connect('data/regulations.db')
    try:
        df = pd.read_sql_query(
            "SELECT id, check_date, length(rule_text) as text_length, change_summary FROM rule_versions WHERE rule_id = ? ORDER BY check_date DESC",
            conn,
            params=(rule_id,)
        )
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
        fromdesc="Baseline",
        todesc="Comparison",
        context=True,
        numlines=3
    )
    # DARK MODE CSS for Redlines
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

# --- Sidebar ---
st.sidebar.markdown("### ⚖️ Regulatory Harmony")
rules = get_rules()

if not rules:
    st.error("No rules loaded. Check data/tracked_rules.json")
    st.stop()

# Build dictionary for dropdown
rule_options = {r['name']: r for r in rules}
selected_rule_name = st.sidebar.selectbox("Select Rulebook", list(rule_options.keys()))
selected_rule = rule_options[selected_rule_name]

st.sidebar.markdown(f"""
<div style='background: rgba(255,255,255,0.05); padding: 15px; border-radius: 15px; font-size: 12px; border: 1px solid rgba(255,255,255,0.1); margin-bottom: 20px;'>
    <strong style='color: #fff'>Tracking ID:</strong> <span style='color:#aaa'>{selected_rule['id']}</span><br>
    <a href="{selected_rule['url']}" style="color: #4da6ff; text-decoration: none;">View Official Source →</a>
</div>
""", unsafe_allow_html=True)

if st.sidebar.button("Run Live Audit"):
    with st.spinner("Connecting to FINRA..."):
        latest = download_rule(selected_rule['url'])
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

# --- Main Page ---
st.title(selected_rule_name)
st.markdown("Regulatory Compliance Monitor")

history_df = get_history(selected_rule['id'])

if history_df.empty:
    st.info("No data available. Click 'Run Live Audit' in the sidebar to initialize this rule.")
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
    
    col_a, col_b = st.columns(2)
    
    version_options = history_df.apply(lambda x: f"v.{x['id']} — {pd.to_datetime(x['check_date']).strftime('%b %d %H:%M')}", axis=1).tolist()
    version_map = {f"v.{row['id']} — {pd.to_datetime(row['check_date']).strftime('%b %d %H:%M')}": row['id'] for _, row in history_df.iterrows()}
    
    with col_a:
        ver_a_label = st.selectbox("Baseline Version", version_options, index=len(version_options)-1 if len(version_options)>1 else 0)
    with col_b:
        ver_b_label = st.selectbox("Comparison Version", version_options, index=0)
        
    id_a = version_map[ver_a_label]
    id_b = version_map[ver_b_label]
    
    text_a = get_specific_version_text(id_a)
    text_b = get_specific_version_text(id_b)
    
    if text_a == text_b:
        st.markdown("""
        <div style='text-align: center; padding: 40px; color: #666; background: rgba(0,0,0,0.2); border-radius: 20px; border: 1px dashed #444;'>
            ✨ These versions are identical.
        </div>
        """, unsafe_allow_html=True)
    else:
        html_diff = generate_dark_glass_diff(text_a, text_b)
        components.html(html_diff, height=600, scrolling=True)

with tab3:
    st.markdown("##### Current Legal Text")
    latest_text = get_specific_version_text(history_df.iloc[0]['id'])
    st.text_area("Content", latest_text, height=600, label_visibility="collapsed")
