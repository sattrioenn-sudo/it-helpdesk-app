import streamlit as st
import pymysql
import pandas as pd
import certifi
from datetime import datetime
import time  # Tambahan untuk manipulasi waktu tampilan

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="IT Helpdesk Pro", 
    page_icon="🎫", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FUNGSI HELPER KONEKSI ---
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

# --- CUSTOM CSS (ADAPTIVE & MODERN) ---
st.markdown("""
    <style>
    .time-display {
        font-family: 'Courier New', Courier, monospace;
        color: #10b981;
        font-weight: bold;
        font-size: 1.2rem;
        text-align: center;
        padding: 10px;
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 10px;
        background: rgba(16, 185, 129, 0.05);
        margin-bottom: 20px;
    }
    .main-header { font-size: 32px; font-weight: 800; text-align: center; color: var(--text-color); }
    </style>
    """, unsafe_allow_html=True)

# --- SIDEBAR & CLOCK ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>🎫 IT-PRO</h1>", unsafe_allow_html=True)
    
    # MENAMPILKAN WAKTU SEKARANG (REAL-TIME DISPLAY)
    # Data ini hanya di memori Streamlit, tidak masuk ke TiDB
    now = datetime.now()
    st.markdown(f"""
        <div class="time-display">
            🕒 {now.strftime('%H:%M:%S')}<br>
            <span style="font-size: 0.8rem;">{now.strftime('%A, %d %b %Y')}</span>
        </div>
    """, unsafe_allow_html=True)

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False
    
    if not st.session_state.logged_in:
        st.write("---")
        u_input = st.text_input("Username")
        p_input = st.text_input("Password", type="password")
        if st.button("Login", use_container_width=True, type="primary"):
            users = st.secrets["auth"]
            if u_input in users and p_input == users[u_input]:
                st.session_state.logged_in = True
                st.session_state.user_name = u_input
                st.rerun()
            else:
                st.error("Gagal Login")
    else:
        st.success(f"User: **{st.session_state.user_name.upper()}**")
        if st.button("Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

# --- LOGIKA NAVIGASI ---
if st.session_state.logged_in:
    menu = st.sidebar.selectbox("📂 MENU", ["Daftar Tiket", "Statistik", "Buat Tiket", "Management User"])
else:
    menu = "Buat Tiket"

# --- MENU 1: BUAT TIKET ---
if menu == "Buat Tiket":
    st.markdown("<div class='main-header'>📝 Submit Support Ticket</div>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("ticket_form", clear_on_submit=True):
            user = st.text_input("👤 Nama / Dept")
            cabang = st.selectbox("🏢 Cabang", st.secrets["master"]["daftar_cabang"])
            issue = st.text_area("🛠 Detail Kendala")
            priority = st.select_slider("🔥 Prioritas", options=["Low", "Medium", "High"])
            
            if st.form_submit_button("🚀 KIRIM LAPORAN", use_container_width=True):
                if user and issue:
                    db = get_connection()
                    cursor = db.cursor()
                    # Waktu database tetap menggunakan default DB atau waktu server saat insert
                    cursor.execute("INSERT INTO tickets (nama_user, cabang, masalah, prioritas, status) VALUES (%s, %s, %s, %s, 'Open')", (user, cabang, issue, priority))
                    db.close()
                    st.success(f"Tiket terkirim pada {datetime.now().strftime('%H:%M:%S')}")
                    st.balloons()

# --- MENU 2: DAFTAR TIKET ---
elif menu == "Daftar Tiket" and st.session_state.logged_in:
    st.markdown("<div class='main-header'>📊 Monitoring Dashboard</div>", unsafe_allow_html=True)
    
    db = get_connection()
    df = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", db)
    db.close()

    # Dashboard Metrics
    m1, m2, m3 = st.columns(3)
    m1.metric("Total Tiket", len(df))
    m2.metric("Status Terakhir", "Live Updates")
    m3.metric("Waktu Cek", now.strftime('%H:%M'))

    st.dataframe(df, use_container_width=True, hide_index=True)

    # Action Panel (Update & Hapus tetap ada di sini)
    # ... (kode update/hapus lo yang lama tinggal dilanjutin di sini)
