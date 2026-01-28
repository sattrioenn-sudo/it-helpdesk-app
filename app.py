import streamlit as st
import pymysql
import pandas as pd
import certifi
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(page_title="IT Helpdesk Pro", page_icon="🎫", layout="wide")

# --- SISTEM LOGGING TANPA DATABASE (In-Memory) ---
# Kita gunakan session_state agar log tidak hilang selama aplikasi tidak di-reboot
if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = []

def add_log(action, details):
    log_entry = {
        "Waktu": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "User": st.session_state.user_name.upper(),
        "Aksi": action,
        "Detail": details
    }
    st.session_state.audit_logs.insert(0, log_entry) # Tambah ke urutan paling atas

# --- CUSTOM CSS ---
st.markdown("""
    <style>
    .main-header { font-size: 32px; font-weight: 800; text-align: center; margin-bottom: 20px; }
    .log-container { background-color: rgba(128, 128, 128, 0.05); padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNGSI KONEKSI DB ---
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
        st.title("🎫 IT-PRO")
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False
        if not st.session_state.logged_in:
            u_input = st.text_input("Username")
            p_input = st.text_input("Password", type="password")
            if st.button("Login", use_container_width=True, type="primary"):
                users = st.secrets["auth"]
                if u_input in users and p_input == users[u_input]:
                    st.session_state.logged_in = True
                    st.session_state.user_name = u_input
                    add_log("LOGIN", "Berhasil masuk ke sistem")
                    st.rerun()
        else:
            st.success(f"Online: {st.session_state.user_name}")
            if st.button("Logout", use_container_width=True):
                add_log("LOGOUT", "Keluar dari sistem")
                st.session_state.logged_in = False
                st.rerun()

login()

# --- NAVIGASI ---
if st.session_state.logged_in:
    menu = st.sidebar.selectbox("📂 MENU", ["Daftar Tiket", "Security Audit Log", "Statistik", "Buat Tiket"])
else:
    menu = "Buat Tiket"

# --- MENU: DAFTAR TIKET (With Logging Trigger) ---
if menu == "Daftar Tiket" and st.session_state.logged_in:
    st.markdown("<div class='main-header'>📊 Monitoring Dashboard</div>", unsafe_allow_html=True)
    
    db = get_connection()
    df = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", db)
    db.close()

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        with st.expander("🔄 Update Status"):
            id_upd = st.selectbox("ID Tiket", df['id'].tolist() if not df.empty else [None], key="u")
            new_stat = st.selectbox("Status", ["Open", "In Progress", "Solved", "Closed"])
            if st.button("Simpan", type="primary"):
                db = get_connection()
                cursor = db.cursor()
                cursor.execute("UPDATE tickets SET status=%s WHERE id=%s", (new_stat, id_upd))
                db.close()
                # CATAT KE LOG
                add_log("UPDATE", f"Mengubah Status Tiket #{id_upd} menjadi {new_stat}")
                st.rerun()

    with c2:
        with st.expander("🗑️ Hapus Tiket"):
            id_del = st.selectbox("ID Tiket", df['id'].tolist() if not df.empty else [None], key="d")
            if st.button("Hapus Permanen"):
                db = get_connection()
                cursor = db.cursor()
                cursor.execute("DELETE FROM tickets WHERE id=%s", (id_del))
                db.close()
                # CATAT KE LOG
                add_log("DELETE", f"Menghapus Tiket #{id_del}")
                st.rerun()

# --- MENU BARU: SECURITY AUDIT LOG ---
elif menu == "Security Audit Log" and st.session_state.logged_in:
    st.markdown("<div class='main-header'>🛡️ Security Audit Trail</div>", unsafe_allow_html=True)
    st.info("Log ini mencatat semua aktivitas sensitif selama sesi aplikasi berjalan.")
    
    if st.session_state.audit_logs:
        log_df = pd.DataFrame(st.session_state.audit_logs)
        st.table(log_df)
        
        if st.button("Bersihkan Log Sesi"):
            st.session_state.audit_logs = []
            st.rerun()
    else:
        st.write("Belum ada aktivitas tercatat.")

# --- MENU LAINNYA (Buat Tiket & Statistik) ---
elif menu == "Buat Tiket":
    st.markdown("<div class='main-header'>📝 Submit Ticket</div>", unsafe_allow_html=True)
    # ... (Kode form input sama seperti sebelumnya) ...
    # Tambahkan add_log("CREATE", f"User {user} membuat tiket baru") jika ingin dicatat
