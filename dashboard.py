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
