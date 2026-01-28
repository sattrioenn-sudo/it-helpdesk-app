import streamlit as st
import pymysql
import pandas as pd
import certifi
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="IT Helpdesk Pro v2.0", 
    page_icon="🎫", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- SISTEM AUDIT LOG (MEMORI SESI) ---
if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = []

def add_log(action, details):
    log_entry = {
        "Waktu": datetime.now().strftime('%H:%M:%S'),
        "User": st.session_state.user_name.upper() if 'user_name' in st.session_state else "GUEST",
        "Aksi": action,
        "Detail": details
    }
    st.session_state.audit_logs.insert(0, log_entry)

# --- UI ENHANCEMENT (CSS) ---
st.markdown("""
    <style>
    /* Background & Font */
    .stApp { background-color: var(--background-color); }
    
    /* Global Card Style */
    div[data-testid="metric-container"] {
        background-color: rgba(28, 131, 225, 0.1);
        border: 1px solid rgba(28, 131, 225, 0.3);
        padding: 15px; border-radius: 12px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.05);
    }
    
    /* Header & Clock Styling */
    .header-container {
        text-align: center; padding: 20px;
        background: linear-gradient(90deg, rgba(2,0,36,0) 0%, rgba(28,131,225,0.1) 50%, rgba(2,0,36,0) 100%);
        border-radius: 20px; margin-bottom: 25px;
    }
    .digital-clock {
        font-family: 'Courier New', monospace;
        color: #10b981; font-size: 24px; font-weight: bold;
    }
    
    /* Button Styles */
    .stButton>button {
        border-radius: 8px; font-weight: 600; transition: 0.3s;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(0,0,0,0.1); }
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
    st.markdown("<h1 style='text-align: center; color: #1d4ed8;'>🎫 IT-PRO</h1>", unsafe_allow_html=True)
    
    # Live Clock Display
    now = datetime.now()
    st.markdown(f"""
        <div style="text-align: center; border: 1px solid #1d4ed8; padding: 10px; border-radius: 10px; margin-bottom: 20px;">
            <div class="digital-clock">{now.strftime('%H:%M:%S')}</div>
            <div style="font-size: 12px; opacity: 0.7;">{now.strftime('%A, %d %B %Y')}</div>
        </div>
    """, unsafe_allow_html=True)

    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("LOGIN", use_container_width=True, type="primary"):
            auth = st.secrets["auth"]
            if u in auth and p == auth[u]:
                st.session_state.logged_in = True
                st.session_state.user_name = u
                add_log("LOGIN", "Sesi dimulai")
                st.rerun()
            else: st.error("Akses Ditolak")
    else:
        st.success(f"Online: **{st.session_state.user_name.upper()}**")
        if st.button("LOGOUT", use_container_width=True):
            add_log("LOGOUT", "Sesi berakhir")
            st.session_state.logged_in = False
            st.rerun()

# --- NAVIGASI ---
if st.session_state.logged_in:
    menu = st.sidebar.selectbox("📂 NAVIGATION", ["Dashboard & Monitoring", "Security Audit Log", "Analytics", "Submit Ticket"])
else:
    menu = "Submit Ticket"

# --- MENU: SUBMIT TICKET ---
if menu == "Submit Ticket":
    st.markdown("<div class='header-container'><h1>📝 IT Support Request</h1></div>", unsafe_allow_html=True)
    
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("main_form", clear_on_submit=True):
            user = st.text_input("👤 Nama Pelapor")
            cabang = st.selectbox("🏢 Lokasi Cabang", st.secrets["master"]["daftar_cabang"])
            issue = st.text_area("🛠 Detail Masalah")
            urgency = st.select_slider("🔥 Prioritas", options=["Low", "Medium", "High"])
            
            if st.form_submit_button("🚀 KIRIM TIKET", use_container_width=True):
                if user and issue:
                    db = get_connection()
                    cursor = db.cursor()
                    cursor.execute("INSERT INTO tickets (nama_user, cabang, masalah, prioritas, status) VALUES (%s, %s, %s, %s, 'Open')", (user, cabang, issue, urgency))
                    db.close()
                    add_log("TICKET", f"Tiket baru dari {user}")
                    st.success("Tiket Berhasil Terkirim!")
                    st.balloons()

# --- MENU: DASHBOARD & MONITORING ---
elif menu == "Dashboard & Monitoring" and st.session_state.logged_in:
    st.markdown("<div class='header-container'><h1>📊 Monitoring Dashboard</h1></div>", unsafe_allow_html=True)
    
    # Data Fetching
    db = get_connection()
    df = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", db)
    db.close()

    # Search & Action Row
    s_col, r_col = st.columns([4, 1])
    query = s_col.text_input("🔍 Cari Masalah/User/ID", placeholder="Ketik untuk memfilter...")
    if r_col.button("🔄 Force Refresh", use_container_width=True): st.rerun()

    if query:
        df = df[df.apply(lambda r: r.astype(str).str.contains(query, case=False).any(), axis=1)]

    # Top Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total", len(df))
    m2.metric("Open", len(df[df['status'] == 'Open']), delta="Alert", delta_color="inverse")
    m3.metric("Progress", len(df[df['status'] == 'In Progress']))
    m4.metric("Solved", len(df[df['status'] == 'Solved']))

    st.dataframe(df, use_container_width=True, hide_index=True)

    # Database Tools
    st.divider()
    t1, t2 = st.columns(2)
    with t1:
        with st.expander("⚙️ Update Status"):
            id_up = st.selectbox("ID Tiket", df['id'].tolist() if not df.empty else [None], key="u")
            st_up = st.selectbox("Status Baru", ["Open", "In Progress", "Solved", "Closed"])
            if st.button("UPDATE", type="primary", use_container_width=True):
                db = get_connection()
                cur = db.cursor()
                cur.execute("UPDATE tickets SET status=%s WHERE id=%s", (st_up, id_up))
                db.close()
                add_log("UPDATE", f"Tiket #{id_up} -> {st_up}")
                st.rerun()
    with t2:
        with st.expander("🗑️ Hapus Tiket"):
            id_dl = st.selectbox("ID Tiket", df['id'].tolist() if not df.empty else [None], key="d")
            if st.button("DELETE PERMANENT", use_container_width=True):
                db = get_connection()
                cur = db.cursor()
                cur.execute("DELETE FROM tickets WHERE id=%s", (id_dl))
                db.close()
                add_log("DELETE", f"Menghapus Tiket #{id_dl}")
                st.rerun()

# --- MENU: SECURITY AUDIT LOG ---
elif menu == "Security Audit Log" and st.session_state.logged_in:
    st.markdown("<div class='header-container'><h1>🛡️ Security Audit Log</h1></div>", unsafe_allow_html=True)
    if st.session_state.audit_logs:
        st.table(pd.DataFrame(st.session_state.audit_logs))
    else: st.info("Belum ada log aktivitas untuk sesi ini.")

# --- MENU: ANALYTICS ---
elif menu == "Analytics" and st.session_state.logged_in:
    st.markdown("<div class='header-container'><h1>📈 Data Analytics</h1></div>", unsafe_allow_html=True)
    db = get_connection()
    df_an = pd.read_sql("SELECT status, cabang FROM tickets", db)
    db.close()
    if not df_an.empty:
        c1, c2 = st.columns(2)
        c1.write("**Beban Tiket per Cabang**")
        c1.bar_chart(df_an['cabang'].value_counts())
        c2.write("**Distribusi Status**")
        c2.line_chart(df_an['status'].value_counts())
