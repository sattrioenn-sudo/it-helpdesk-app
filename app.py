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

# --- AUDIT LOG SYSTEM (IN-MEMORY) ---
if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = []

def add_log(action, details):
    log_entry = {
        "Waktu": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "User": st.session_state.user_name.upper() if 'user_name' in st.session_state else "SYSTEM",
        "Aksi": action,
        "Detail": details
    }
    st.session_state.audit_logs.insert(0, log_entry)

# --- CUSTOM CSS (ADAPTIVE & MODERN) ---
st.markdown("""
    <style>
    .main { padding: 1.5rem; }
    /* Metric Card Styling */
    div[data-testid="metric-container"] {
        background-color: rgba(128, 128, 128, 0.05); 
        border: 1px solid rgba(128, 128, 128, 0.1);
        padding: 20px; border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.02);
    }
    .main-header {
        font-size: 32px; font-weight: 800; text-align: center;
        margin-bottom: 5px; color: var(--text-color);
    }
    .sub-header {
        text-align: center; color: #6b7280; font-size: 14px; margin-bottom: 30px;
    }
    /* Form & Expander Styling */
    [data-testid="stForm"], .stExpander {
        border: 1px solid rgba(128, 128, 128, 0.2) !important;
        border-radius: 15px !important;
    }
    /* Buttons */
    .stButton>button { border-radius: 8px; font-weight: 600; }
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
        st.markdown("<h1 style='text-align: center;'>🎫 IT-PRO</h1>", unsafe_allow_html=True)
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False
        
        if not st.session_state.logged_in:
            st.write("---")
            u_input = st.text_input("Username", key="login_u")
            p_input = st.text_input("Password", type="password", key="login_p")
            if st.button("Masuk Ke Sistem", use_container_width=True, type="primary"):
                users = st.secrets["auth"]
                if u_input in users and p_input == users[u_input]:
                    st.session_state.logged_in = True
                    st.session_state.user_name = u_input
                    add_log("LOGIN", "Berhasil masuk ke dashboard")
                    st.rerun()
                else:
                    st.error("Credential Salah")
        else:
            st.success(f"Operator: **{st.session_state.user_name.upper()}**")
            if st.button("Keluar (Logout)", use_container_width=True):
                add_log("LOGOUT", "Keluar dari sistem")
                st.session_state.logged_in = False
                st.rerun()

login()

if st.session_state.logged_in:
    menu = st.sidebar.selectbox("📂 NAVIGASI", ["Daftar Tiket", "Security Log", "Statistik", "Buat Tiket", "Management User"])
else:
    menu = "Buat Tiket"

# --- MENU 1: BUAT TIKET ---
if menu == "Buat Tiket":
    st.markdown("<div class='main-header'>📝 Submit Support Ticket</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Silakan lengkapi formulir kendala di bawah ini</div>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("ticket_form", clear_on_submit=True):
            user = st.text_input("👤 Nama Pelapor / Departemen")
            cabang = st.selectbox("🏢 Cabang", st.secrets["master"]["daftar_cabang"])
            issue = st.text_area("🛠 Detail Masalah IT")
            priority = st.select_slider("🔥 Tingkat Urgensi", options=["Low", "Medium", "High"])
            
            if st.form_submit_button("🚀 KIRIM LAPORAN", use_container_width=True):
                if user and issue:
                    db = get_connection()
                    cursor = db.cursor()
                    cursor.execute("INSERT INTO tickets (nama_user, cabang, masalah, prioritas, status) VALUES (%s, %s, %s, %s, 'Open')", (user, cabang, issue, priority))
                    db.close()
                    add_log("CREATE", f"Tiket baru dibuat oleh {user} ({cabang})")
                    st.success("Tiket Berhasil Terkirim!")
                    st.balloons()
                else:
                    st.warning("Nama dan Masalah wajib diisi!")

# --- MENU 2: DAFTAR TIKET (MONITORING & SEARCH) ---
elif menu == "Daftar Tiket" and st.session_state.logged_in:
    st.markdown("<div class='main-header'>📊 Monitoring & Knowledge Base</div>", unsafe_allow_html=True)
    st.markdown(f"<div class='sub-header'>Sesi Aktif: {st.session_state.user_name.upper()}</div>", unsafe_allow_html=True)

    # Database Pull
    try:
        db = get_connection()
        df = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", db)
        db.close()
    except:
        st.error("Koneksi database terputus. Coba refresh.")
        df = pd.DataFrame()

    # Search & Refresh Row
    col_s, col_r = st.columns([5, 1])
    search_q = col_s.text_input("🔍 Cari (User, Cabang, atau Detail Masalah)", placeholder="Cari data...")
    if col_r.button("🔄 Refresh", use_container_width=True):
        st.rerun()
    
    if search_q:
        df = df[df.apply(lambda row: row.astype(str).str.contains(search_q, case=False).any(), axis=1)]

    # Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Tiket", len(df))
    m2.metric("🔴 Open", len(df[df['status'] == 'Open']))
    m3.metric("🟡 In Progress", len(df[df['status'] == 'In Progress']))
    m4.metric("🟢 Solved", len(df[df['status'] == 'Solved']))

    st.dataframe(df, use_container_width=True, hide_index=True)

    # Action Panel
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        with st.expander("🔄 Update Status Pekerjaan"):
            if not df.empty:
                id_upd = st.selectbox("Pilih ID Tiket", df['id'].tolist(), key="upd_id")
                new_stat = st.selectbox("Set Status Baru", ["Open", "In Progress", "Solved", "Closed"])
                if st.button("Konfirmasi Update", type="primary", use_container_width=True):
                    db = get_connection()
                    cursor = db.cursor()
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if new_stat in ["Solved", "Closed"] else None
                    cursor.execute("UPDATE tickets SET status=%s, waktu_selesai=%s WHERE id=%s", (new_stat, now, id_upd))
                    db.close()
                    add_log("UPDATE", f"Tiket #{id_upd} diubah status ke {new_stat}")
                    st.toast(f"Update Berhasil!")
                    st.rerun()

    with c2:
        with st.expander("🗑️ Hapus Tiket"):
            if not df.empty:
                id_del = st.selectbox("Pilih ID Hapus", df['id'].tolist(), key="del_id")
                st.warning(f"Hapus ID #{id_del}?")
                if st.button("Hapus Permanen", use_container_width=True):
                    db = get_connection()
                    cursor = db.cursor()
                    cursor.execute("DELETE FROM tickets WHERE id=%s", (id_del))
                    db.close()
                    add_log("DELETE", f"Menghapus tiket #{id_del}")
                    st.toast("Data telah dihapus!")
                    st.rerun()

# --- MENU 3: SECURITY LOG ---
elif menu == "Security Log" and st.session_state.logged_in:
    st.markdown("<div class='main-header'>🛡️ Security Audit Log</div>", unsafe_allow_html=True)
    st.markdown("<div class='sub-header'>Riwayat Aktivitas Admin (Sesi Ini)</div>", unsafe_allow_html=True)
    
    if st.session_state.audit_logs:
        st.table(pd.DataFrame(st.session_state.audit_logs))
    else:
        st.info("Belum ada aktivitas tercatat di sesi ini.")

# --- MENU 4: STATISTIK ---
elif menu == "Statistik" and st.session_state.logged_in:
    st.markdown("<div class='main-header'>📈 IT Performance Metrics</div>", unsafe_allow_html=True)
    db = get_connection()
    df_s = pd.read_sql("SELECT status, cabang FROM tickets", db)
    db.close()
    
    if not df_s.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Beban Kerja per Cabang**")
            st.bar_chart(df_s['cabang'].value_counts(), color="#3b82f6")
        with col2:
            st.write("**Persentase Status Tiket**")
            st.bar_chart(df_s['status'].value_counts(), color="#10b981")

# --- MENU 5: MANAGEMENT USER ---
elif menu == "Management User" and st.session_state.logged_in:
    st.markdown("<div class='main-header'>👤 Staff IT Terdaftar</div>", unsafe_allow_html=True)
    st.table([{"Operator": u, "Role": "Admin/Staff IT"} for u in st.secrets["auth"]])
