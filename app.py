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

# --- CUSTOM UI DESIGN (CSS) ---
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    div[data-testid="stMetricValue"] { font-size: 28px; color: #007bff; }
    div[data-testid="metric-container"] {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #eee;
    }
    .stButton>button {
        border-radius: 8px;
        transition: all 0.3s;
        font-weight: 600;
    }
    div.stButton > button:first-child[data-testid="baseButton-secondary"] {
        color: white;
        background-color: #dc3545;
        border: none;
    }
    </style>
    """, unsafe_allow_html=True)

# --- FUNGSI LOGIN ---
def login():
    with st.sidebar:
        st.title("🔐 IT Portal")
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False
        
        if not st.session_state.logged_in:
            user_input = st.text_input("Username", placeholder="Username")
            pw_input = st.text_input("Password", type="password", placeholder="******")
            if st.button("Login", use_container_width=True):
                users_dict = st.secrets["auth"]
                if user_input in users_dict and pw_input == users_dict[user_input]:
                    st.session_state.logged_in = True
                    st.session_state.user_name = user_input
                    st.rerun()
                else:
                    st.sidebar.error("Gagal Login")
        else:
            st.success(f"Online: **{st.session_state.user_name.upper()}**")
            if st.button("Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.rerun()

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

# --- JALANKAN LOGIN ---
login()
st.sidebar.divider()

if st.session_state.logged_in:
    menu = st.sidebar.selectbox("🧭 Navigasi", ["Daftar Tiket", "Buat Tiket", "Statistik", "Management User"])
else:
    menu = "Buat Tiket"

# --- MENU 1: BUAT TIKET ---
if menu == "Buat Tiket":
    st.title("📝 Submit IT Ticket")
    with st.form("ticket_form", clear_on_submit=True):
        c1, c2 = st.columns(2)
        user = c1.text_input("👤 Nama / Dept")
        cabang = c2.selectbox("🏢 Cabang", st.secrets["master"]["daftar_cabang"])
        issue = st.text_area("🛠 Detail Masalah")
        priority = st.select_slider("🔥 Prioritas", options=["Low", "Medium", "High"])
        if st.form_submit_button("🚀 Kirim Laporan", use_container_width=True):
            if user and issue:
                try:
                    db = get_connection()
                    cursor = db.cursor()
                    cursor.execute("INSERT INTO tickets (nama_user, cabang, masalah, prioritas, status) VALUES (%s, %s, %s, %s, 'Open')", (user, cabang, issue, priority))
                    db.close()
                    st.success("✅ Tiket Berhasil Dikirim!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Error Database: {e}")
            else:
                st.warning("Mohon isi nama dan detail masalah.")

# --- MENU 2: DAFTAR TIKET (Update & Hapus) ---
elif menu == "Daftar Tiket" and st.session_state.logged_in:
    st.title("📊 Monitoring Center")
    db = get_connection()
    df = pd.read_sql("SELECT id, nama_user, cabang, masalah, prioritas, status, waktu FROM tickets ORDER BY id DESC", db)
    db.close()

    m1, m2, m3 = st.columns(3)
    m1.metric("Total Tiket", len(df))
    m2.metric("Open", len(df[df['status'] == 'Open']))
    m3.metric("Solved", len(df[df['status'] == 'Solved']))

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()
    col_act1, col_act2 = st.columns(2)

    with col_act1:
        with st.expander("⚙️ Update Status"):
            if not df.empty:
                u1, u2 = st.columns(2)
                id_upd = u1.selectbox("Pilih ID Update", df['id'].tolist(), key="upd_id")
                stat_upd = u2.selectbox("Status Baru", ["Open", "In Progress", "Solved", "Closed"])
                if st.button("Update Status", use_container_width=True, type="primary"):
                    db = get_connection()
                    cursor = db.cursor()
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if stat_upd in ["Solved", "Closed"] else None
                    cursor.execute("UPDATE tickets SET status=%s, waktu_selesai=%s WHERE id=%s", (stat_upd, now, id_upd))
                    db.close()
                    st.rerun()

    with col_act2:
        with st.expander("🗑️ Hapus Tiket"):
            if not df.empty:
                id_del = st.selectbox("Pilih ID Hapus", df['id'].tolist(), key="del_id")
                st.warning(f"Hapus tiket ID #{id_del}?")
                if st.button("Hapus Permanen", use_container_width=True):
                    db = get_connection()
                    cursor = db.cursor()
                    cursor.execute("DELETE FROM tickets WHERE id=%s", (id_del))
                    db.close()
                    st.toast(f"Tiket #{id_del} telah dihapus!")
                    st.rerun()

# --- MENU 3: STATISTIK ---
elif menu == "Statistik" and st.session_state.logged_in:
    st.title("📈 IT Performance")
    db = get_connection()
    df_s = pd.read_sql("SELECT status, cabang FROM tickets", db)
    db.close()
    if not df_s.empty:
        c1, c2 = st.columns(2)
        with c1:
            st.write("**Tiket per Cabang**")
            st.bar_chart(df_s['cabang'].value_counts())
        with c2:
            st.write("**Status Tiket**")
            st.bar_chart(df_s['status'].value_counts())

# --- MENU 4: MANAGEMENT USER ---
elif menu == "Management User" and st.session_state.logged_in:
    st.title("👤 User Directory")
    users = st.secrets["auth"]
    st.table([{"Username": u, "Role": "Admin/IT Staff"} for u in users])
