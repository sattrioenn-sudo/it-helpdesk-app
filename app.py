import streamlit as st
import pymysql
import pandas as pd
import certifi
from datetime import datetime, timedelta
import io
# Import modul sparepart yang sudah kita buat
from spareparts import show_sparepart_menu

# --- 1. KONFIGURASI & THEME ---
st.set_page_config(page_title="IT Kemasan", page_icon="🎫", layout="wide")

# --- 2. LOGIKA PERSISTENT SESSION ---
@st.cache_resource
def get_auth_state():
    return {"logged_in": False, "user_name": ""}

auth = get_auth_state()
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = auth["logged_in"]
if 'user_name' not in st.session_state:
    st.session_state.user_name = auth["user_name"]

# --- 3. FUNGSI WAKTU WIB ---
def get_wib_now():
    return datetime.utcnow() + timedelta(hours=7)

# --- 4. DATABASE CONNECTION ---
def get_connection():
    return pymysql.connect(
        host=st.secrets["tidb"]["host"],
        port=int(st.secrets["tidb"]["port"]),
        user=st.secrets["tidb"]["user"],
        password=st.secrets["tidb"]["password"],
        database=st.secrets["tidb"]["database"],
        autocommit=True,
        ssl={'ca': certifi.where()}
    )

# --- 5. CSS CUSTOM ---
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top right, #0e1117, #1c2533); }
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 20px; border-radius: 15px;
        color: white !important;
    }
    .clock-box {
        background: linear-gradient(135deg, #1d4ed8 0%, #10b981 100%);
        padding: 15px; border-radius: 12px; text-align: center;
        margin-bottom: 25px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }
    .digital-clock {
        font-family: 'JetBrains Mono', monospace;
        color: white; font-size: 28px; font-weight: 800;
    }
    .action-header {
        background: rgba(255, 255, 255, 0.05);
        padding: 10px 20px; border-radius: 10px;
        border-left: 5px solid #1d4ed8; margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 6. LOGIKA AUDIT LOG ---
if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = []

def add_log(action, details):
    waktu = get_wib_now().strftime('%H:%M:%S')
    st.session_state.audit_logs.insert(0, {
        "Waktu": waktu,
        "User": st.session_state.user_name.upper() if st.session_state.user_name else "GUEST",
        "Aksi": action, "Detail": details
    })

# --- 7. SIDEBAR MANAGEMENT ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: white;'>🎫 IT-Kemasan</h1>", unsafe_allow_html=True)
    wib = get_wib_now()
    st.markdown(f'<div class="clock-box"><div class="digital-clock">{wib.strftime("%H:%M:%S")}</div><div style="color: white; font-size: 12px; opacity: 0.9;">{wib.strftime("%A, %d %B %Y")}</div></div>', unsafe_allow_html=True)

    if not st.session_state.logged_in:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("🔓 SIGN IN", use_container_width=True, type="primary"):
            # FIX: Cek apakah key 'auth' ada untuk menghindari KeyError
            if "auth" in st.secrets and u in st.secrets["auth"]:
                if p == str(st.secrets["auth"][u]):
                    st.session_state.logged_in = True
                    st.session_state.user_name = u
                    add_log("LOGIN", "Masuk Dashboard")
                    st.rerun()
                else:
                    st.error("Password Salah!")
            else:
                st.error("User tidak terdaftar di Secrets!")
    else:
        st.markdown(f"<p style='text-align: center;'>Operator: <b>{st.session_state.user_name.upper()}</b></p>", unsafe_allow_html=True)
        # Tambahkan menu Sparepart di sini
        menu = st.selectbox("📂 MAIN MENU", ["Dashboard Monitor", "⚙️ Sparepart Inventory", "Export & Reporting", "Security Log"])
        if st.button("🔒 LOGOUT", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

# --- 8. MENU LOGIC ---
if not st.session_state.logged_in:
    menu = "Quick Input Mode"

# --- ROUTING MENU ---
if menu == "Dashboard Monitor" and st.session_state.logged_in:
    st.markdown("## 📊 Monitoring Center")
    db = get_connection()
    df = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", db)
    db.close()
    
    # ... (Sisa kode dashboard monitor lo tetap sama) ...
    st.dataframe(df, use_container_width=True, hide_index=True)

elif menu == "⚙️ Sparepart Inventory" and st.session_state.logged_in:
    # PANGGIL MODUL SPAREPART YANG KITA REVISI TADI
    show_sparepart_menu(get_connection, get_wib_now, add_log)

elif menu == "Export & Reporting" and st.session_state.logged_in:
    st.markdown("## 📂 Export Report")
    # ... (Sisa kode export lo) ...

elif menu == "Security Log" and st.session_state.logged_in:
    st.markdown("## 🛡️ Security Audit Log")
    if st.session_state.audit_logs:
        st.dataframe(pd.DataFrame(st.session_state.audit_logs), use_container_width=True, hide_index=True)

elif menu == "Quick Input Mode":
    st.markdown("<h1 style='text-align: center;'>📝 Form Laporan IT</h1>", unsafe_allow_html=True)
    # ... (Sisa kode quick input lo) ...
