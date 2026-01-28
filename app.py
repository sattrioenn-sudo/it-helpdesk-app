import streamlit as st
import pymysql
import pandas as pd
import certifi
from datetime import datetime, timedelta

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="IT Helpdesk Pro v2.0", 
    page_icon="🎫", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- FUNGSI WAKTU WIB ---
def get_wib_now():
    # Mengonversi waktu server (UTC) ke WIB (UTC+7)
    return datetime.now() + timedelta(hours=7)

# --- SISTEM AUDIT LOG (MEMORI SESI) ---
if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = []

def add_log(action, details):
    log_entry = {
        "Waktu": get_wib_now().strftime('%H:%M:%S'),
        "User": st.session_state.user_name.upper() if 'user_name' in st.session_state else "GUEST",
        "Aksi": action,
        "Detail": details
    }
    st.session_state.audit_logs.insert(0, log_entry)

# --- UI ENHANCEMENT (CSS) ---
st.markdown("""
    <style>
    .stApp { background-color: var(--background-color); }
    
    /* Card Style */
    div[data-testid="metric-container"] {
        background-color: rgba(28, 131, 225, 0.07);
        border: 1px solid rgba(28, 131, 225, 0.2);
        padding: 15px; border-radius: 12px;
    }
    
    /* Header Container */
    .header-container {
        text-align: center; padding: 15px;
        background: linear-gradient(90deg, rgba(2,0,36,0) 0%, rgba(28,131,225,0.1) 50%, rgba(2,0,36,0) 100%);
        border-radius: 15px; margin-bottom: 20px;
    }
    
    /* Digital Clock */
    .digital-clock {
        font-family: 'Courier New', monospace;
        color: #10b981; font-size: 26px; font-weight: bold;
        text-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
    }

    /* Table Fix */
    .stDataFrame { border-radius: 10px; overflow: hidden; }
    </style>
    """, unsafe_allow_html=True)

# --- DATABASE CONNECTION ---
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

# --- SIDEBAR & AUTH ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #1d4ed8; margin-bottom:0;'>🎫 IT-PRO</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; opacity:0.6; font-size:12px;'>Management System v2.0</p>", unsafe_allow_html=True)
    
    # LIVE CLOCK WIB
    wib = get_wib_now()
    st.markdown(f"""
        <div style="text-align: center; border: 1px solid rgba(29, 78, 216, 0.3); padding: 10px; border-radius: 12px; margin: 10px 0 20px 0; background: rgba(29, 78, 216, 0.05);">
            <div class="digital-clock">{wib.strftime('%H:%M:%S')}</div>
            <div style="font-size: 12px; font-weight: 600;">{wib.strftime('%A')}</div>
            <div style="font-size: 11px; opacity: 0.7;">{wib.strftime('%d %B %Y')}</div>
            <div style="font-size: 9px; color: #10b981; margin-top:5px;">● ASIA/JAKARTA (WIB)</div>
        </div>
    """, unsafe_allow_html=True)

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("🔓 MASUK", use_container_width=True, type="primary"):
            auth = st.secrets["auth"]
            if u in auth and p == auth[u]:
                st.session_state.logged_in = True
                st.session_state.user_name = u
                add_log("LOGIN", "Berhasil masuk")
                st.rerun()
            else: st.error("Akses Ditolak")
    else:
        st.info(f"👤 **{st.session_state.user_name.upper()}**")
        if st.button("🔒 KELUAR", use_container_width=True):
            add_log("LOGOUT", "Keluar sistem")
            st.session_state.logged_in = False
            st.rerun()

# --- NAVIGASI ---
if st.session_state.logged_in:
    menu = st.sidebar.selectbox("📂 MENU UTAMA", ["Dashboard", "Security Log", "Analytics", "Buat Tiket"])
else:
    menu = "Buat Tiket"

# --- MENU: BUAT TIKET ---
if menu == "Buat Tiket":
    st.markdown("<div class='header-container'><h1>📝 Form Laporan Kendala</h1></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("main_form", clear_on_submit=True):
            user = st.text_input("Nama Pelapor")
            cabang = st.selectbox("Lokasi Cabang", st.secrets["master"]["daftar_cabang"])
            issue = st.text_area("Detail Masalah")
            urgency = st.select_slider("Prioritas", options=["Low", "Medium", "High"])
            if st.form_submit_button("KIRIM LAPORAN 🚀", use_container_width=True):
                if user and issue:
                    db = get_connection()
                    cursor = db.cursor()
                    cursor.execute("INSERT INTO tickets (nama_user, cabang, masalah, prioritas, status) VALUES (%s, %s, %s, %s, 'Open')", (user, cabang, issue, urgency))
                    db.close()
                    add_log("TICKET", f"Tiket baru dari {user}")
                    st.success(f"✅ Tiket terkirim pada {get_wib_now().strftime('%H:%M')} WIB")
                    st.balloons()
                else: st.warning("Mohon isi nama dan detail masalah!")

# --- MENU: DASHBOARD & MONITORING ---
elif menu == "Dashboard" and st.session_state.logged_in:
    st.markdown("<div class='header-container'><h1>📊 Dashboard Monitoring</h1></div>", unsafe_allow_html=True)
    
    db = get_connection()
    df = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", db)
    db.close()

    # Search & Action
    s_col, r_col = st.columns([5, 1])
    query = s_col.text_input("🔍 Pencarian Cepat", placeholder="Ketik nama, cabang, atau masalah...")
    if r_col.button("🔄 Refresh", use_container_width=True): st.rerun()

    if query:
        df = df[df.apply(lambda r: r.astype(str).str.contains(query, case=False).any(), axis=1)]

    # Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total", len(df))
    m2.metric("Open", len(df[df['status'] == 'Open']), delta="Urgensi", delta_color="inverse")
    m3.metric("Progress", len(df[df['status'] == 'In Progress']))
    m4.metric("Solved", len(df[df['status'] == 'Solved']))

    st.dataframe(df, use_container_width=True, hide_index=True)

    # Action Panel
    st.divider()
    t1, t2 = st.columns(2)
    with t1:
        with st.expander("🛠️ Update Status Pekerjaan"):
            if not df.empty:
                id_up = st.selectbox("ID Tiket", df['id'].tolist(), key="u")
                st_up = st.selectbox("Status", ["Open", "In Progress", "Solved", "Closed"])
                if st.button("SIMPAN PERUBAHAN", type="primary"):
                    db = get_connection()
                    cur = db.cursor()
                    cur.execute("UPDATE tickets SET status=%s WHERE id=%s", (st_up, id_up))
                    db.close()
                    add_log("UPDATE", f"Tiket #{id_up} diubah ke {st_up}")
                    st.rerun()
    with t2:
        with st.expander("🗑️ Hapus Data"):
            if not df.empty:
                id_dl = st.selectbox("ID Tiket", df['id'].tolist(), key="d")
                if st.button("HAPUS PERMANEN", use_container_width=True):
                    db = get_connection()
                    cur = db.cursor()
                    cur.execute("DELETE FROM tickets WHERE id=%s", (id_dl))
                    db.close()
                    add_log("DELETE", f"Menghapus Tiket #{id_dl}")
                    st.rerun()

# --- MENU: SECURITY AUDIT LOG ---
elif menu == "Security Log" and st.session_state.logged_in:
    st.markdown("<div class='header-container'><h1>🛡️ Security Audit Trail</h1></div>", unsafe_allow_html=True)
    if st.session_state.audit_logs:
        st.dataframe(pd.DataFrame(st.session_state.audit_logs), use_container_width=True, hide_index=True)
    else: st.info("Sesi baru dimulai. Belum ada aktivitas.")

# --- MENU: ANALYTICS ---
elif menu == "Analytics" and st.session_state.logged_in:
    st.markdown("<div class='header-container'><h1>📈 Support Analytics</h1></div>", unsafe_allow_html=True)
    db = get_connection()
    df_an = pd.read_sql("SELECT status, cabang FROM tickets", db)
    db.close()
    if not df_an.empty:
        c1, c2 = st.columns(2)
        c1.subheader("Beban Kerja per Lokasi")
        c1.bar_chart(df_an['cabang'].value_counts())
        c2.subheader("Distribusi Status")
        c2.area_chart(df_an['status'].value_counts())
