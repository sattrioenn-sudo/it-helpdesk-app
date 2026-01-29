import streamlit as st
import pymysql
import pandas as pd
import certifi
import pytz
import plotly.express as px
from datetime import datetime, timedelta, date

# --- 1. SETTING HALAMAN ---
st.set_page_config(page_title="APLICATION", page_icon="💎", layout="wide")

# --- 2. PERSISTENCE LOGIN (ANTI-REFRESH) ---
@st.cache_resource
def get_auth_state():
    return {"logged_in": False, "user": "", "perms": []}

auth_cache = get_auth_state()

# Inisialisasi Session State agar data tidak hilang/error
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = auth_cache["logged_in"]
if "current_user" not in st.session_state:
    st.session_state["current_user"] = auth_cache["user"]
if "user_perms" not in st.session_state:
    st.session_state["user_perms"] = auth_cache["perms"]
if "global_login_tracker" not in st.session_state:
    st.session_state["global_login_tracker"] = {}
if "security_logs" not in st.session_state:
    st.session_state["security_logs"] = []
if "user_db" not in st.session_state:
    st.session_state["user_db"] = {
        "admin": ["kcs_2026", "Admin", ["Dashboard IT", "Monitor IT", "POS Inventory", "Masuk", "Keluar", "Edit", "User Management", "Security"]]
    }

# --- 3. KONEKSI DATABASE (UNIFIED PYMYSQL) ---
def get_db_conn():
    return pymysql.connect(
        **st.secrets["tidb"],
        autocommit=True,
        ssl={'ca': certifi.where()}
    )

def get_wib():
    return datetime.now(pytz.timezone('Asia/Jakarta'))

def parse_detail(val):
    parts = [p.strip() for p in str(val).split('|')]
    while len(parts) < 6: parts.append("-")
    return parts

# --- 4. CSS QUANTUM DASHBOARD (MURNI PUNYA LO) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
    .stApp { background: radial-gradient(circle at top right, #1e1b4b, #0f172a, #020617); color: #f8fafc; }
    .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 1.5rem; border-radius: 20px;
        backdrop-filter: blur(15px); margin-bottom: 20px;
    }
    .shimmer-text {
        background: linear-gradient(90deg, #38bdf8, #818cf8, #c084fc, #38bdf8);
        background-size: 200% auto; -webkit-background-clip: text; -webkit-text-fill-color: transparent;
        animation: shimmer 3s linear infinite; font-weight: 800; font-size: 2.2rem;
    }
    @keyframes shimmer { to { background-position: 200% center; } }
    .stat-label { color: #94a3b8; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    .stat-value { font-size: 1.8rem; font-weight: 800; color: #ffffff; margin-top: 5px; }
    .session-info {
        background: rgba(56, 189, 248, 0.05);
        border: 1px solid rgba(56, 189, 248, 0.2);
        padding: 12px; border-radius: 12px; margin-bottom: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. LOGIC AUTH ---
if not st.session_state["logged_in"]:
    st.markdown("<br><br><br>", unsafe_allow_html=True)
    _, col2, _ = st.columns([1, 1, 1])
    with col2:
        st.markdown("<div style='text-align:center;'><h1 class='shimmer-text'>SATRIO POS</h1></div>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.form_submit_button("SYSTEM ENTRY"):
                if u in st.session_state["user_db"] and str(p) == str(st.session_state["user_db"][u][0]):
                    now_str = get_wib().strftime('%d/%m/%Y %H:%M')
                    st.session_state.update({
                        "logged_in": True, "current_user": u, 
                        "user_perms": st.session_state["user_db"][u][2],
                        "last_login_display": now_str, "current_login_time": now_str
                    })
                    auth_cache.update({"logged_in": True, "user": u, "perms": st.session_state["user_db"][u][2]})
                    st.rerun()
                else: st.error("Invalid Credentials")
else:
    # --- 6. SIDEBAR ---
    with st.sidebar:
        st.markdown(f"<h2 class='shimmer-text' style='font-size:1.5rem;'>{st.session_state['current_user'].upper()}</h2>", unsafe_allow_html=True)
        st.markdown(f"""<div class="session-info">
            <div style="font-size:0.65rem; color:#94a3b8;">LOGIN: {st.session_state.get('current_login_time')}</div>
        </div>""", unsafe_allow_html=True)
        
        all_menus = {
            "📊 Dashboard IT": "Dashboard IT",
            "🖥️ Monitor IT": "Monitor IT",
            "📦 POS Inventory": "POS Inventory",
            "➕ Barang Masuk": "Masuk",
            "📤 Barang Keluar": "Keluar",
            "🔧 Kontrol POS": "Edit",
            "👥 User Management": "User Management",
            "🛡️ Security Logs": "Security",
            "📝 Buat Tiket IT": "Buat Tiket"
        }
        nav_options = [m for m, p in all_menus.items() if p in st.session_state["user_perms"] or p == "Buat Tiket"]
        menu = st.selectbox("MENU NAVIGATION", nav_options)
        
        if st.button("🚪 LOGOUT", use_container_width=True):
            st.session_state["logged_in"] = False
            auth_cache["logged_in"] = False
            st.rerun()

    # --- 7. MENU ROUTING ---

    # MONITOR IT (REVISI NAMA KOLOM)
    if menu == "🖥️ Monitor IT":
        st.markdown("<h1 class='shimmer-text'>IT Monitor Tower</h1>", unsafe_allow_html=True)
        try:
            conn = get_db_conn()
            df_it = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", conn)
            conn.close()
            df_display = df_it.rename(columns={'nama_user': 'Nama Teknisi', 'masalah': 'Problem', 'waktu': 'Waktu Laporan'})
            st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
            st.dataframe(df_display, use_container_width=True, hide_index=True)
            st.markdown("</div>", unsafe_allow_html=True)
        except Exception as e: st.error(f"Data IT Error: {e}")

    # POS INVENTORY (DATA ASLI LO)
    elif menu == "📦 POS Inventory":
        st.markdown("<h1 class='shimmer-text'>Control Tower</h1>", unsafe_allow_html=True)
        try:
            conn = get_db_conn()
            df_raw = pd.read_sql("SELECT * FROM inventory ORDER BY id DESC", conn)
            conn.close()
            if not df_raw.empty:
                p_data = df_raw['nama_barang'].apply(parse_detail)
                df_raw['SKU'], df_raw['Item'] = p_data.apply(lambda x: x[0]), p_data.apply(lambda x: x[1])
                df_raw['adj'] = df_raw.apply(lambda x: x['jumlah'] if x['jenis_mutasi'] == 'Masuk' else -x['jumlah'], axis=1)
                stok_summary = df_raw.groupby(['SKU', 'Item'])['adj'].sum().reset_index(name='Stock')
                st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
                st.dataframe(stok_summary, use_container_width=True, hide_index=True)
                st.markdown("</div>", unsafe_allow_html=True)
        except Exception as e: st.error(f"Data POS Error: {e}")

    # FORM TIKET IT
    elif menu == "📝 Buat Tiket IT":
        st.markdown("<h1 class='shimmer-text'>Laporan IT</h1>", unsafe_allow_html=True)
        with st.form("tiket"):
            nama = st.text_input("Nama")
            mas = st.text_area("Kendala")
            if st.form_submit_button("KIRIM"):
                conn = get_db_conn(); cur = conn.cursor()
                cur.execute("INSERT INTO tickets (nama_user, masalah, status, waktu) VALUES (%s,%s,'Open',%s)", 
                            (nama, mas, get_wib().strftime('%Y-%m-%d %H:%M:%S')))
                conn.close(); st.success("Berhasil!"); st.rerun()
