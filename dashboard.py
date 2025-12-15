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

# --- CUSTOM DIFF ENGINE (The Fix) ---
def render_diff_html(old_text, new_text):
    """
    Manually builds a clean HTML table for side-by-side comparison.
    """
    a = old_text.splitlines()
    b = new_text.splitlines()
    
    # Use SequenceMatcher to find the differences
    matcher = difflib.SequenceMatcher(None, a, b)
    
    html = []
    html.append("""
    <style>
        /* CSS FIX: Targets the text cell directly to force White Color */
        .diff-row { display: flex; border-bottom: 1px solid #333; font-family: 'Helvetica Neue', sans-serif; font-size: 13px; }
        
        .diff-cell { 
            flex: 1; 
            padding: 5px 10px; 
            word-wrap: break-word; 
            white-space: pre-wrap; 
            color: #ffffff; /* <--- THIS IS THE FIX (Was defaulting to black) */
        }
        
        .diff-num { 
            width: 30px; 
            color: #666; 
            text-align: right; 
            padding-right: 10px; 
            border-right: 1px solid #333; 
            user-select: none; 
        }
        
        /* THE COLORS */
        .added { background-color: rgba(15, 61, 27, 0.6); color: #84e897; }   /* Green Background + Light Green Text */
        .deleted { background-color: rgba(61, 20, 20, 0.6); color: #f28b8b; } /* Red Background + Light Red Text */
        .empty { background-color: transparent; }
    </style>
    <div style="background: rgba(0,0,0,0.2); border-radius: 8px; border: 1px solid #444; overflow: hidden;">
    """)
    
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        # EQUAL: Print side by side (White)
        if tag == 'equal':
            for i, line in enumerate(a[i1:i2]):
                html.append(f"""
                <div class="diff-row">
                    <div class="diff-num">{i1+i+1}</div><div class="diff-cell">{line}</div>
                    <div class="diff-num">{j1+i+1}</div><div class="diff-cell">{line}</div>
                </div>""")
        
        # REPLACE: Print Old (Red) on Left, New (Green) on Right
        elif tag == 'replace':
            old_chunk = a[i1:i2]
            new_chunk = b[j1:j2]
            max_len = max(len(old_chunk), len(new_chunk))
            old_chunk += [''] * (max_len - len(old_chunk))
            new_chunk += [''] * (max_len - len(new_chunk))
            
            for i in range(max_len):
                o_text = old_chunk[i]
                n_text = new_chunk[i]
                o_cls = "deleted" if o_text else "empty"
                n_cls = "added" if n_text else "empty"
                html.append(f"""
                <div class="diff-row">
                    <div class="diff-num">{i1+i+1 if o_text else ''}</div><div class="diff-cell {o_cls}">{o_text}</div>
                    <div class="diff-num">{j1+i+1 if n_text else ''}</div><div class="diff-cell {n_cls}">{n_text}</div>
                </div>""")

        # DELETE: Print Old (Red) on Left, Empty on Right
        elif tag == 'delete':
            for i, line in enumerate(a[i1:i2]):
                html.append(f"""
                <div class="diff-row">
                    <div class="diff-num">{i1+i+1}</div><div class="diff-cell deleted">{line}</div>
                    <div class="diff-num"></div><div class="diff-cell empty"></div>
                </div>""")

        # INSERT: Print Empty on Left, New (Green) on Right
        elif tag == 'insert':
            for i, line in enumerate(b[j1:j2]):
                html.append(f"""
                <div class="diff-row">
                    <div class="diff-num"></div><div class="diff-cell empty"></div>
                    <div class="diff-num">{j1+i+1}</div><div class="diff-cell added">{line}</div>
                </div>""")
                
    html.append("</div>")
    return "".join(html)
# --- INJECT DATA ---
def inject_demo_data(rule_id):
    # Distinct lines help the diff engine work better
    common = """(a) Standards of Commercial Honor and Principles of Trade
A member, in the conduct of its business, shall observe high standards of commercial honor and just and equitable principles of trade.

(b) Prohibition Against Deceptive Practices
No member shall effect any transaction in, or induce the purchase or sale of, any security by means of any manipulative, deceptive or other fraudulent device or contrivance."""

    added = """
(c) New Requirement (Demo Update)
This section simulates a new regulatory requirement added by the SEC to demonstrate the redline capabilities. Because this text is NOT in the baseline, it will appear GREEN."""

    conn = sqlite3.connect('data/regulations.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS rule_versions (id INTEGER PRIMARY KEY AUTOINCREMENT, rule_id TEXT, check_date TEXT, rule_text TEXT, change_summary TEXT)''')
    
    c.execute("DELETE FROM rule_versions WHERE rule_id = ?", (rule_id,))
    
    # Baseline (v1)
    c.execute("INSERT INTO rule_versions (rule_id, check_date, rule_text, change_summary) VALUES (?, datetime('now', '-1 day'), ?, ?)", 
              (rule_id, common, "Historical Baseline (Demo)"))

    # Live Audit (v2) - Note explicit newlines
    c.execute("INSERT INTO rule_versions (rule_id, check_date, rule_text, change_summary) VALUES (?, datetime('now'), ?, ?)", 
              (rule_id, common + "\n" + added, "Live Audit (Demo)"))
    
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
        
        # Default: Left=Oldest (Bottom list item), Right=Newest (Top list item)
        with col_a: ver_a_label = st.selectbox("Baseline Version", version_options, index=len(version_options)-1)
        with col_b: ver_b_label = st.selectbox("Comparison Version", version_options, index=0)
            
        id_a = version_map[ver_a_label]
        id_b = version_map[ver_b_label]
        text_a = get_specific_version_text(id_a)
        text_b = get_specific_version_text(id_b)
        
        # THE LEGEND
        st.markdown("""
        <div style="margin-bottom: 10px; padding: 8px; background: rgba(0,0,0,0.3); border-radius: 6px; display: flex; gap: 15px; font-family: sans-serif; font-size: 11px; color: #aaa; border: 1px solid #444; width: fit-content;">
            <span style="display:flex; align-items:center;"><span style="width:10px; height:10px; background:#0f3d1b; margin-right:5px; border:1px solid #84e897;"></span> Added</span>
            <span style="display:flex; align-items:center;"><span style="width:10px; height:10px; background:#3d1414; margin-right:5px; border:1px solid #f28b8b;"></span> Deleted</span>
        </div>
        """, unsafe_allow_html=True)

        if text_a == text_b:
            st.info("Versions are identical.")
        else:
            # Generate Custom HTML
            diff_html = render_diff_html(text_a, text_b)
            
            # Dynamic Height Logic
            line_count = max(len(text_a.splitlines()), len(text_b.splitlines()))
            dynamic_height = min(max(300, line_count * 25 + 50), 800)
            
            components.html(diff_html, height=dynamic_height, scrolling=True)

with tab3:
    st.markdown("##### Current Legal Text")
    try: selected_text_view = get_specific_version_text(version_map[ver_b_label])
    except: selected_text_view = get_specific_version_text(history_df.iloc[0]['id'])
    
    st.code(selected_text_view, language="text")
