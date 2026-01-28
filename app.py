import streamlit as st
import pymysql
import pandas as pd
import certifi
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="IT Kemasan", 
    page_icon="🎫", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (ADAPTIVE THEME) ---
st.markdown("""
    <style>
    .main { padding: 2rem; }
    div[data-testid="metric-container"] {
        background-color: rgba(128, 128, 128, 0.1); 
        border: 1px solid rgba(128, 128, 128, 0.2);
        padding: 15px; border-radius: 15px;
    }
    .main-header {
        font-size: 32px; font-weight: 800; text-align: center;
        margin-bottom: 10px; color: var(--text-color);
    }
    .user-badge {
        text-align: center; color: #64748b; margin-bottom: 30px; font-style: italic;
    }
    </style>
    """, unsafe_allow_html=True)

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

# --- LOGIN SYSTEM ---
def login():
    with st.sidebar:
        st.markdown("<h2 style='text-align: center;'>🎫 IT-Kemasan Group</h2>", unsafe_allow_html=True)
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False
        
        if not st.session_state.logged_in:
            user_input = st.text_input("Username")
            pw_input = st.text_input("Password", type="password")
            if st.button("Login", use_container_width=True, type="primary"):
                users_dict = st.secrets["auth"]
                if user_input in users_dict and pw_input == users_dict[user_input]:
                    st.session_state.logged_in = True
                    st.session_state.user_name = user_input
                    st.rerun()
                else:
                    st.error("Gagal Login")
        else:
            st.success(f"Aktif: **{st.session_state.user_name.upper()}**")
            if st.button("Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.rerun()

login()

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
            user = st.text_input("👤 Nama Pelapor / Dept")
            cabang = st.selectbox("🏢 Cabang", st.secrets["master"]["daftar_cabang"])
            issue = st.text_area("🛠 Detail Kendala")
            priority = st.select_slider("🔥 Prioritas", options=["Low", "Medium", "High"])
            if st.form_submit_button("🚀 KIRIM LAPORAN", use_container_width=True):
                if user and issue:
                    db = get_connection()
                    cursor = db.cursor()
                    cursor.execute("INSERT INTO tickets (nama_user, cabang, masalah, prioritas, status) VALUES (%s, %s, %s, %s, 'Open')", (user, cabang, issue, priority))
                    db.close()
                    st.success(f"Tiket berhasil dibuat!")
                    st.balloons()

# --- MENU 2: DAFTAR TIKET (DENGAN LOG AKTIVITAS USER) ---
elif menu == "Daftar Tiket" and st.session_state.logged_in:
    st.markdown("<div class='main-header'>📊 Monitoring Dashboard</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='user-badge'>Operator Bertugas: {st.session_state.user_name.upper()}</div>", unsafe_allow_html=True)
    
    db = get_connection()
    df = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", db)
    db.close()

    # Search bar
    search_query = st.text_input("🔍 Cari Riwayat Masalah", placeholder="Ketik kata kunci...")
    if search_query:
        df = df[df['masalah'].str.contains(search_query, case=False, na=False) | df['nama_user'].str.contains(search_query, case=False, na=False)]

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()
    c1, c2 = st.columns(2)
    
    with c1:
        with st.expander("🔄 Update Status Tiket"):
            if not df.empty:
                id_upd = st.selectbox("Pilih ID Tiket", df['id'].tolist(), key="upd")
                new_status = st.selectbox("Status Baru", ["Open", "In Progress", "Solved", "Closed"])
                if st.button("Update Sekarang", type="primary", use_container_width=True):
                    db = get_connection()
                    cursor = db.cursor()
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if new_status in ["Solved", "Closed"] else None
                    cursor.execute("UPDATE tickets SET status=%s, waktu_selesai=%s WHERE id=%s", (new_status, now, id_upd))
                    db.close()
                    # Menampilkan siapa yang melakukan update
                    st.toast(f"✅ Tiket #{id_upd} diupdate oleh {st.session_state.user_name.upper()}")
                    st.rerun()

    with c2:
        with st.expander("🗑️ Hapus Tiket"):
            if not df.empty:
                id_del = st.selectbox("Pilih ID Tiket", df['id'].tolist(), key="del")
                st.warning(f"Konfirmasi penghapusan ID #{id_del}")
                if st.button("Hapus Permanen", use_container_width=True):
                    db = get_connection()
                    cursor = db.cursor()
                    cursor.execute("DELETE FROM tickets WHERE id=%s", (id_del))
                    db.close()
                    # Menampilkan siapa yang melakukan penghapusan
                    st.toast(f"⚠️ Tiket #{id_del} dihapus oleh {st.session_state.user_name.upper()}")
                    st.rerun()

# --- MENU LAINNYA ---
elif menu == "Statistik" and st.session_state.logged_in:
    st.markdown("<div class='main-header'>📈 Analitik</div>", unsafe_allow_html=True)
    st.info(f"Analisis data oleh: {st.session_state.user_name.upper()}")
    # ... (kode bar chart tetap sama)

elif menu == "Management User" and st.session_state.logged_in:
    st.markdown("<div class='main-header'>👤 Staff IT Terdaftar</div>", unsafe_allow_html=True)
    st.table([{"User": u, "Akses": "Administrator"} for u in st.secrets["auth"]])
