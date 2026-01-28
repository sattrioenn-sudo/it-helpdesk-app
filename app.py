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
    /* Gradient Background */
    .stApp {
        background: radial-gradient(circle at top right, #0e1117, #1c2533);
    }
    
    /* Glassmorphism Card */
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 20px; border-radius: 15px;
        color: white !important;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0e1117 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    /* Digital Clock Premium */
    .clock-box {
        background: linear-gradient(135deg, #1d4ed8 0%, #10b981 100%);
        padding: 15px; border-radius: 12px; text-align: center;
        margin-bottom: 25px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }
    .digital-clock {
        font-family: 'JetBrains Mono', monospace;
        color: white; font-size: 28px; font-weight: 800;
    }
    
    /* Dataframe Styling */
    .stDataFrame {
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 15px;
    }

    /* Action Center Header */
    .action-header {
        background: rgba(255, 255, 255, 0.05);
        padding: 10px 20px; border-radius: 10px;
        border-left: 5px solid #1d4ed8; margin: 20px 0;
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
    st.markdown("<h1 style='text-align: center; color: white;'>🎫 IT-Kemasan Group</h1>", unsafe_allow_html=True)
    
    # Clock UI
    wib = get_wib_now()
    st.markdown(f"""
        <div class="clock-box">
            <div class="digital-clock">{wib.strftime('%H:%M:%S')}</div>
            <div style="color: white; font-size: 12px; opacity: 0.9;">{wib.strftime('%A, %d %B %Y')}</div>
        </div>
    """, unsafe_allow_html=True)

    if 'logged_in' not in st.session_state: st.session_state.logged_in = False

    if not st.session_state.logged_in:
        with st.container():
            u = st.text_input("Username")
            p = st.text_input("Password", type="password")
            if st.button("🔓 SIGN IN", use_container_width=True, type="primary"):
                if u in st.secrets["auth"] and p == st.secrets["auth"][u]:
                    st.session_state.logged_in = True
                    st.session_state.user_name = u
                    add_log("LOGIN", "Masuk Dashboard")
                    st.rerun()
    else:
        st.markdown(f"<p style='text-align: center;'>Operator: <b>{st.session_state.user_name.upper()}</b></p>", unsafe_allow_html=True)
        if st.button("🔒 LOGOUT", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

# --- 7. MAIN NAVIGATION ---
if st.session_state.logged_in:
    menu = st.sidebar.selectbox("📂 MAIN MENU", ["Dashboard Monitor", "Export & Reporting", "Security Log", "Buat Tiket Baru"])
else:
    menu = "Buat Tiket Baru"

# --- 8. MENU LOGIC ---

# --- MENU: DASHBOARD ---
if menu == "Dashboard Monitor" and st.session_state.logged_in:
    st.markdown("## 📊 Monitoring Center")
    
    # Fetch Data
    db = get_connection()
    df = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", db)
    db.close()

    # Search Box
    q = st.text_input("🔍 Search Console", placeholder="Cari Nama, Cabang, atau Detail Kendala...")
    if q: df = df[df.apply(lambda r: r.astype(str).str.contains(q, case=False).any(), axis=1)]

    # Top Metrics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Tickets", len(df))
    c2.metric("🔴 Open", len(df[df['status'] == 'Open']))
    c3.metric("🟡 In Progress", len(df[df['status'] == 'In Progress']))
    c4.metric("🟢 Solved", len(df[df['status'] == 'Solved']))

    st.dataframe(df, use_container_width=True, hide_index=True)

    # --- ACTION CENTER (Update & Hapus ada di sini) ---
    st.markdown("<div class='action-header'>⚡ Quick Action Center</div>", unsafe_allow_html=True)
    
    col_up, col_del = st.columns(2)
    
    with col_up:
        with st.expander("🔄 Update Status Pekerjaan"):
            if not df.empty:
                id_up = st.selectbox("Pilih ID Tiket", df['id'].tolist(), key="up_select")
                st_up = st.selectbox("Set Status", ["Open", "In Progress", "Solved", "Closed"])
                if st.button("SIMPAN PERUBAHAN", type="primary", use_container_width=True):
                    db = get_connection()
                    cur = db.cursor()
                    cur.execute("UPDATE tickets SET status=%s WHERE id=%s", (st_up, id_up))
                    db.close()
                    add_log("UPDATE", f"ID #{id_up} diubah ke {st_up}")
                    st.toast("Status Berhasil Diperbarui!")
                    st.rerun()

    with col_del:
        with st.expander("🗑️ Hapus Tiket (Admin Only)"):
            if not df.empty:
                id_del = st.selectbox("Pilih ID Hapus", df['id'].tolist(), key="del_select")
                st.error(f"Peringatan: Menghapus ID #{id_del} tidak dapat dibatalkan.")
                if st.button("KONFIRMASI HAPUS", use_container_width=True):
                    db = get_connection()
                    cur = db.cursor()
                    cur.execute("DELETE FROM tickets WHERE id=%s", (id_del))
                    db.close()
                    add_log("DELETE", f"Menghapus Tiket ID #{id_del}")
                    st.toast("Data Terhapus!")
                    st.rerun()

# --- MENU: EXPORT ---
elif menu == "Export & Reporting" and st.session_state.logged_in:
    st.markdown("## 📂 Financial & Operations Report")
    db = get_connection()
    df_ex = pd.read_sql("SELECT * FROM tickets", db)
    db.close()
    
    st.dataframe(df_ex, use_container_width=True)
    csv = df_ex.to_csv(index=False).encode('utf-8')
    st.download_button("📥 DOWNLOAD CSV (EXCEL FRIENDLY)", csv, f"Report_IT_{get_wib_now().strftime('%Y%m%d')}.csv", "text/csv", use_container_width=True)

# --- MENU: SECURITY LOG ---
elif menu == "Security Log" and st.session_state.logged_in:
    st.markdown("## 🛡️ Security Audit Log")
    if st.session_state.audit_logs:
        st.dataframe(pd.DataFrame(st.session_state.audit_logs), use_container_width=True, hide_index=True)
    else: st.info("Belum ada aktivitas terekam.")

# --- MENU: BUAT TIKET ---
elif menu == "Buat Tiket Baru":
    st.markdown("<h1 style='text-align: center;'>📝 Form Laporan IT</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("form_entry", clear_on_submit=True):
            user = st.text_input("Nama Lengkap")
            cabang = st.selectbox("Lokasi Cabang", st.secrets["master"]["daftar_cabang"])
            issue = st.text_area("Deskripsi Kendala")
            prio = st.select_slider("Urgensi", ["Low", "Medium", "High"])
            if st.form_submit_button("KIRIM LAPORAN 🚀", use_container_width=True):
                if user and issue:
                    db = get_connection()
                    cur = db.cursor()
                    cur.execute("INSERT INTO tickets (nama_teknisi, cabang, masalah, prioritas, status) VALUES (%s,%s,%s,%s,'Open')", (user, cabang, issue, prio))
                    db.close()
                    st.success("Tiket Anda telah masuk ke sistem antrean IT.")
                    st.balloons()
