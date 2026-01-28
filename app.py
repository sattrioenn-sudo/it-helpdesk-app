import streamlit as st
import pymysql
import pandas as pd
import certifi
from datetime import datetime, timedelta
import io

# --- 1. KONFIGURASI & THEME ---
st.set_page_config(
    page_title="IT Kemasan", 
    page_icon="🎫", 
    layout="wide"
)

# --- 2. FUNGSI WAKTU WIB ---
def get_wib_now():
    return datetime.now() + timedelta(hours=7)

# --- 3. DATABASE CONNECTION ---
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

# --- 4. CSS CUSTOM (PREMIUM UI) ---
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
    section[data-testid="stSidebar"] {
        background-color: #0e1117 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
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
    </style>
    """, unsafe_allow_html=True)

# --- 5. LOGIKA AUDIT LOG ---
if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = []

def add_log(action, details):
    waktu = get_wib_now().strftime('%H:%M:%S')
    st.session_state.audit_logs.insert(0, {
        "Waktu": waktu,
        "User": st.session_state.user_name.upper() if 'user_name' in st.session_state else "GUEST",
        "Aksi": action, "Detail": details
    })

# --- 6. SIDEBAR MANAGEMENT ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: white;'>🎫 IT-Kemasan</h1>", unsafe_allow_html=True)
    wib = get_wib_now()
    st.markdown(f'<div class="clock-box"><div class="digital-clock">{wib.strftime("%H:%M:%S")}</div></div>', unsafe_allow_html=True)

    if 'logged_in' not in st.session_state: st.session_state.logged_in = False

    if st.session_state.logged_in:
        st.success(f"User: {st.session_state.user_name.upper()}")
        menu = st.selectbox("📂 MENU", ["Dashboard Monitor", "Analytics & Performance", "Export & Reporting", "Security Log", "Buat Tiket Baru"])
        if st.button("🔒 LOGOUT", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
    else:
        menu = "Buat Tiket Baru"
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("🔓 SIGN IN", use_container_width=True, type="primary"):
            if u in st.secrets["auth"] and p == st.secrets["auth"][u]:
                st.session_state.logged_in = True
                st.session_state.user_name = u
                add_log("LOGIN", "Masuk Dashboard")
                st.rerun()

# --- 7. DASHBOARD MONITOR (Sama seperti sebelumnya) ---
if menu == "Dashboard Monitor" and st.session_state.logged_in:
    st.markdown("## 📊 Monitoring Center")
    db = get_connection()
    df = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", db)
    db.close()
    
    if 'waktu_selesai' in df.columns:
        df['waktu_selesai'] = df.apply(lambda r: get_wib_now().strftime('%Y-%m-%d %H:%M:%S') if (r['status'] == 'Solved' and (r['waktu_selesai'] is None or str(r['waktu_selesai']) == 'None')) else r['waktu_selesai'], axis=1)

    df_display = df.rename(columns={'nama_user': 'Nama Teknisi'})
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # ... (Bagian Action Center Update/Delete tetap sama) ...

# --- 8. MENU BARU: ANALYTICS & PERFORMANCE ---
elif menu == "Analytics & Performance" and st.session_state.logged_in:
    st.title("📈 IT Performance Analytics")
    db = get_connection()
    df = pd.read_sql("SELECT * FROM tickets", db)
    db.close()

    if not df.empty:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("👨‍💻 Tiket per Teknisi")
            # Menghitung jumlah tiket per teknisi
            teknisi_stats = df['nama_user'].value_counts()
            st.bar_chart(teknisi_stats)

        with col2:
            st.subheader("🏢 Sebaran per Cabang")
            cabang_stats = df['cabang'].value_counts()
            st.area_chart(cabang_stats)

        st.subheader("🚦 Status Pekerjaan Saat Ini")
        status_stats = df['status'].value_counts()
        st.bar_chart(status_stats, horizontal=True)
    else:
        st.info("Data belum tersedia untuk dianalisa.")

# --- MENU LAINNYA (Export, Log, Buat Tiket tetap sama kodenya) ---
elif menu == "Export & Reporting" and st.session_state.logged_in:
    st.markdown("## 📂 Export Data")
    # ... (Kode export lo sebelumnya) ...

elif menu == "Buat Tiket Baru":
    # ... (Kode form input lo sebelumnya) ...
    st.title("📝 Form Laporan IT")
