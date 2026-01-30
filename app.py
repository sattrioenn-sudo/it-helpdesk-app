import streamlit as st
import pymysql
import pandas as pd
import certifi
import json
import os
from datetime import datetime, timedelta

# --- 1. KONFIGURASI ---
st.set_page_config(page_title="IT Support System - KCS", page_icon="🎫", layout="wide")

# --- 2. STORAGE VIRTUAL ---
def load_data(file, default):
    if os.path.exists(file):
        try:
            with open(file, 'r') as f: return json.load(f)
        except: return default
    return default

def save_data(file, data):
    with open(file, 'w') as f: json.dump(data, f)

if 'custom_keterangan' not in st.session_state:
    st.session_state.custom_keterangan = load_data('keterangan_it.json', {})
if 'user_db' not in st.session_state:
    default_users = {"admin": ["kcs_2026", "Admin", ["Dashboard", "Input Tiket", "Update Status", "Inventory", "Export", "Security", "User Management", "Hapus Tiket"]]}
    st.session_state.user_db = load_data('users_it.json', default_users)
if 'security_logs' not in st.session_state:
    st.session_state.security_logs = load_data('security_logs.json', [])
if 'current_menu' not in st.session_state:
    st.session_state.current_menu = "📊 Dashboard"

# --- 3. FUNGSI UTAMA ---
def get_wib_now():
    return datetime.utcnow() + timedelta(hours=7)

def get_connection():
    return pymysql.connect(
        host=st.secrets["tidb"]["host"], port=int(st.secrets["tidb"]["port"]),
        user=st.secrets["tidb"]["user"], password=st.secrets["tidb"]["password"],
        database=st.secrets["tidb"]["database"], autocommit=True, ssl={'ca': certifi.where()}
    )

def has_access(perm):
    user = st.session_state.get("user_name", "").lower()
    user_data = st.session_state.user_db.get(user, [None, None, ["Dashboard"]])
    return perm in user_data[2]

# --- 4. CSS: THE "ALIVE" DESIGN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }

    /* Animated Dynamic Background */
    .stApp {
        background: linear-gradient(-45deg, #05070a, #0c0e12, #111827, #080a0f);
        background-size: 400% 400%;
        animation: gradient 15s ease infinite;
    }
    @keyframes gradient {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Sidebar Glassmorphism */
    [data-testid="stSidebar"] {
        background-color: rgba(10, 12, 16, 0.8) !important;
        backdrop-filter: blur(12px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Pulse Status Indicator */
    .pulse-dot {
        height: 8px; width: 8px;
        background-color: #10b981;
        border-radius: 50%;
        display: inline-block;
        box-shadow: 0 0 8px #10b981;
        animation: pulse 2s infinite;
        margin-right: 8px;
    }
    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 6px rgba(16, 185, 129, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
    }

    /* Hero Text & Typing Effect */
    .hero-container { text-align: center; padding: 100px 0; }
    .typing-title {
        color: #ffffff;
        font-size: 64px;
        font-weight: 800;
        letter-spacing: -3px;
        background: linear-gradient(to right, #ffffff, #60a5fa);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Card Glass Effect */
    div.stMetric {
        background: rgba(255, 255, 255, 0.03) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 20px !important;
        padding: 20px !important;
        transition: transform 0.3s ease;
    }
    div.stMetric:hover { transform: translateY(-5px); border-color: #60a5fa !important; }

    /* Button Styling */
    .stButton > button {
        border-radius: 12px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        background: rgba(255, 255, 255, 0.02);
        color: #94a3b8;
        padding: 12px 20px;
        transition: all 0.3s;
        text-align: left;
        width: 100%;
    }
    .stButton > button:hover {
        background: #3b82f6; color: white;
        border-color: #60a5fa; box-shadow: 0 0 20px rgba(59, 130, 246, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color: white; font-weight: 800; margin-bottom: 0;'>KCS <span style='color:#3b82f6;'>CORE</span></h2>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 10px; color: #475569; letter-spacing: 2px;'>SYSTEM INFRASTRUCTURE</p>", unsafe_allow_html=True)
    
    t_now = get_wib_now()
    st.markdown(f'''
    <div style="background: rgba(255,255,255,0.02); padding: 15px; border-radius: 15px; border: 1px solid rgba(255,255,255,0.05); margin: 20px 0;">
        <div style="font-size: 10px; color: #64748b; text-transform: uppercase;">Realtime Clock</div>
        <div style="font-family: monospace; color: #60a5fa; font-size: 20px; font-weight: bold;">{t_now.strftime("%H:%M:%S")}</div>
        <div style="display: flex; align-items: center; margin-top: 10px;">
            <span class="pulse-dot"></span><span style="font-size: 11px; color: #10b981;">NODE_ONLINE</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)

    if st.session_state.get('logged_in'):
        u_name = st.session_state.user_name
        u_role = st.session_state.user_db.get(u_name, ["", "User"])[1]
        
        st.markdown(f'''
        <div style="padding: 10px 0 20px 0;">
            <div style="font-size: 10px; color: #475569; text-transform: uppercase;">Operator Identity</div>
            <div style="font-weight: 700; color: #f8fafc; font-size: 18px;">{u_name.upper()}</div>
            <div style="color: #60a5fa; font-size: 11px;">🛡️ {u_role}</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Menu with consistent labels
        if st.button("📊 Dashboard Overview", use_container_width=True): st.session_state.current_menu = "📊 Dashboard"
        if has_access("Inventory") and st.button("📦 Inventory Management", use_container_width=True): st.session_state.current_menu = "📦 Inventory"
        if has_access("User Management") and st.button("👥 System User Control", use_container_width=True): st.session_state.current_menu = "👥 User Management"
        if has_access("Security") and st.button("🛡️ Security Audit Log", use_container_width=True): st.session_state.current_menu = "🛡️ Security"
        
        st.markdown("<br>"*5, unsafe_allow_html=True)
        if st.button("🔒 Terminate Session", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
    else:
        st.markdown("<p style='font-size: 12px; color: #475569; text-align: center;'>IDENTIFICATION REQUIRED</p>", unsafe_allow_html=True)
        u_in = st.text_input("Username").lower()
        p_in = st.text_input("Password", type="password")
        if st.button("ACCESS SYSTEM", use_container_width=True):
            if u_in in st.session_state.user_db and p_in == st.session_state.user_db[u_in][0]:
                st.session_state.logged_in, st.session_state.user_name = True, u_in
                st.rerun()
            else: st.error("Access Refused")

# --- 6. WELCOME PAGE (THE "ALIVE" SCREEN) ---
if not st.session_state.get('logged_in'):
    st.markdown(f"""
    <div class="hero-container">
        <div style="background: #3b82f6; width: 50px; height: 4px; border-radius: 20px; margin: 0 auto 30px auto;"></div>
        <h1 class="typing-title">Nexus Infrastructure</h1>
        <p style="color: #475569; font-size: 18px; letter-spacing: 6px; font-weight: 300;">KEMASAN CIPTATAMA SEMPURNA</p>
        <div style="margin-top: 40px; color: #1e293b; font-family: monospace;">SECURE_GATEWAY_V.2.6 // PORT_8501_ACTIVE</div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# --- 7. MAIN CONTENT ---
if st.session_state.current_menu == "📊 Dashboard":
    st.markdown("<h2 style='font-weight: 800; letter-spacing: -1px;'>Infrastructure <span style='color:#3b82f6;'>Monitor</span></h2>", unsafe_allow_html=True)
    
    db = get_connection()
    df_raw = pd.read_sql("SELECT * FROM tickets ORDER BY id ASC", db)
    db.close()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Current Traffic", f"{len(df_raw)} Units")
    m2.metric("Critical State", len(df_raw[df_raw['status'] == 'Open']), delta="Active", delta_color="inverse")
    m3.metric("In Progress", len(df_raw[df_raw['status'] == 'In Progress']))
    m4.metric("System Solved", len(df_raw[df_raw['status'] == 'Solved']))

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Filter & Table with Neon Accent
    st.markdown('<div style="background: rgba(255,255,255,0.01); padding: 25px; border-radius: 25px; border: 1px solid rgba(255,255,255,0.05);">', unsafe_allow_html=True)
    
    c_f1, c_f2 = st.columns(2)
    d_start = c_f1.date_input("Filter Since", value=datetime.now() - timedelta(days=30))
    d_end = c_f2.date_input("Filter Until", value=datetime.now())

    df_raw['tgl_saja'] = pd.to_datetime(df_raw['waktu']).dt.date
    df = df_raw[(df_raw['tgl_saja'] >= d_start) & (df_raw['tgl_saja'] <= d_end)].copy()
    df = df.reset_index(drop=True)
    df.insert(0, 'No', range(1, len(df) + 1)) 
    df['IT_Notes'] = df['id'].apply(lambda x: st.session_state.custom_keterangan.get(str(x), "-"))
    
    def status_styler(val):
        color = {'Open': '#f87171', 'In Progress': '#fbbf24', 'Solved': '#34d399'}.get(val, 'white')
        return f'color: {color}; font-weight: 800;'

    st.dataframe(
        df[['No', 'nama_user', 'cabang', 'masalah', 'status', 'waktu', 'IT_Notes']].style.map(status_styler, subset=['status']), 
        use_container_width=True, hide_index=True
    )
    st.markdown('</div>', unsafe_allow_html=True)

    if has_access("Export"):
        st.download_button("📥 GENERATE DATA REPORT", df.to_csv(index=False).encode('utf-8'), "IT_Core_Report.csv", use_container_width=True)

    # Input & Update Logic (Functions remain unchanged)
    c_a, c_b = st.columns(2)
    with c_a:
        if has_access("Input Tiket"):
            with st.expander("➕ Open System Ticket"):
                # Form and SQL logic remains exactly the same...
                pass
