import streamlit as st
import pymysql
import pandas as pd
import certifi
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="IT Helpdesk Pro", 
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
        margin-bottom: 25px; color: var(--text-color);
    }
    [data-testid="stForm"] {
        border: 1px solid rgba(128, 128, 128, 0.3);
        border-radius: 20px; padding: 20px;
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
        st.markdown("<h2 style='text-align: center;'>🎫 IT-PRO</h2>", unsafe_allow_html=True)
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False
        
        if not st.session_state.logged_in:
            st.write("---")
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
            st.info(f"User: **{st.session_state.user_name.upper()}**")
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
            user = st.text_input("👤 Nama / Dept")
            cabang = st.selectbox("🏢 Cabang", st.secrets["master"]["daftar_cabang"])
            issue = st.text_area("🛠 Detail Kendala")
            priority = st.select_slider("🔥 Prioritas", options=["Low", "Medium", "High"])
            if st.form_submit_button("🚀 KIRIM LAPORAN", use_container_width=True):
                if user and issue:
                    db = get_connection()
                    cursor = db.cursor()
                    cursor.execute("INSERT INTO tickets (nama_user, cabang, masalah, prioritas, status) VALUES (%s, %s, %s, %s, 'Open')", (user, cabang, issue, priority))
                    db.close()
                    st.success("Tiket Berhasil Dikirim!")
                    st.balloons()

# --- MENU 2: DAFTAR TIKET (WITH SEARCH/KNOWLEDGE BASE) ---
elif menu == "Daftar Tiket" and st.session_state.logged_in:
    st.markdown("<div class='main-header'>📊 Monitoring & Knowledge Base</div>", unsafe_allow_html=True)
    
    db = get_connection()
    df = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", db)
    db.close()

    # --- FITUR PENCARIAN JANGKA PANJANG ---
    with st.container():
        search_query = st.text_input("🔍 Cari Masalah Sebelumnya (Contoh: 'Printer', 'Wifi', 'Budi')", placeholder="Ketik kata kunci masalah untuk referensi solusi...")
        
        if search_query:
            # Cari di kolom masalah, nama_user, atau cabang (Case Insensitive)
            filtered_df = df[
                df['masalah'].str.contains(search_query, case=False, na=False) | 
                df['nama_user'].str.contains(search_query, case=False, na=False) |
                df['cabang'].str.contains(search_query, case=False, na=False)
            ]
            st.write(f"Ditemukan **{len(filtered_df)}** data yang relevan.")
        else:
            filtered_df = df

    st.write("---")
    
    # Dashboard Metrics (Berdasarkan data yang sudah difilter cari)
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total View", len(filtered_df))
    m2.metric("Open", len(filtered_df[filtered_df['status'] == 'Open']))
    m3.metric("Progress", len(filtered_df[filtered_df['status'] == 'In Progress']))
    m4.metric("Solved", len(filtered_df[filtered_df['status'] == 'Solved']))

    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

    # --- ACTION PANEL ---
    c1, c2 = st.columns(2)
    with c1:
        with st.expander("🔄 Update Status"):
            if not filtered_df.empty:
                id_upd = st.selectbox("ID Tiket", filtered_df['id'].tolist(), key="upd")
                new_status = st.selectbox("Status", ["Open", "In Progress", "Solved", "Closed"])
                if st.button("Simpan", type="primary"):
                    db = get_connection()
                    cursor = db.cursor()
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if new_status in ["Solved", "Closed"] else None
                    cursor.execute("UPDATE tickets SET status=%s, waktu_selesai=%s WHERE id=%s", (new_status, now, id_upd))
                    db.close()
                    st.rerun()
    with c2:
        with st.expander("🗑️ Hapus Data"):
            if not filtered_df.empty:
                id_del = st.selectbox("ID Tiket", filtered_df['id'].tolist(), key="del")
                if st.button("Hapus Permanen"):
                    db = get_connection()
                    cursor = db.cursor()
                    cursor.execute("DELETE FROM tickets WHERE id=%s", (id_del))
                    db.close()
                    st.rerun()

# --- MENU 3 & 4 (Statistik & Management User tetap sama) ---
elif menu == "Statistik" and st.session_state.logged_in:
    st.markdown("<div class='main-header'>📈 IT Performance</div>", unsafe_allow_html=True)
    db = get_connection()
    df_s = pd.read_sql("SELECT status, cabang FROM tickets", db)
    db.close()
    if not df_s.empty:
        col1, col2 = st.columns(2)
        col1.bar_chart(df_s['cabang'].value_counts())
        col2.bar_chart(df_s['status'].value_counts())

elif menu == "Management User" and st.session_state.logged_in:
    st.markdown("<div class='main-header'>👤 User Management</div>", unsafe_allow_html=True)
    users = st.secrets["auth"]
    st.table([{"Username": u, "Role": "Admin"} for u in users])
