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

# --- 4. CSS CUSTOM (PREMIUM UI v4.0) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    .stApp { background: radial-gradient(circle at top right, #10141d, #05070a); }
    
    /* Glassmorphism Cards */
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(15px);
        padding: 25px; border-radius: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
    }

    /* Sidebar */
    section[data-testid="stSidebar"] {
        background-color: rgba(10, 15, 25, 0.8) !important;
        backdrop-filter: blur(10px);
    }

    /* Premium Clock */
    .clock-box {
        background: linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%);
        padding: 20px; border-radius: 20px; text-align: center;
        margin-bottom: 30px; border: 1px solid rgba(255, 255, 255, 0.1);
    }
    .digital-clock { color: white; font-size: 32px; font-weight: 800; }

    /* Action Header */
    .action-header {
        background: linear-gradient(90deg, rgba(29,78,216,0.15) 0%, rgba(29,78,216,0) 100%);
        padding: 15px; border-radius: 15px; border-left: 6px solid #1d4ed8; margin: 25px 0;
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
    st.markdown("<h1 style='text-align: center; color: white; font-size: 22px;'>🎫 IT-KEMASAN PRO</h1>", unsafe_allow_html=True)
    wib = get_wib_now()
    st.markdown(f'<div class="clock-box"><div class="digital-clock">{wib.strftime("%H:%M:%S")}</div><div style="color: white; opacity:0.7; font-size:12px;">{wib.strftime("%A, %d %b %Y")}</div></div>', unsafe_allow_html=True)

    if 'logged_in' not in st.session_state: st.session_state.logged_in = False

    if not st.session_state.logged_in:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("🔓 SIGN IN", use_container_width=True, type="primary"):
            if u in st.secrets["auth"] and p == st.secrets["auth"][u]:
                st.session_state.logged_in = True
                st.session_state.user_name = u
                add_log("LOGIN", "Masuk Dashboard")
                st.rerun()
    else:
        st.markdown(f"<p style='text-align: center;'>Operator: <b style='color:#10b981;'>{st.session_state.user_name.upper()}</b></p>", unsafe_allow_html=True)
        menu = st.selectbox("📂 MENU NAVIGASI", ["Dashboard Monitor", "Export & Reporting", "Security Log", "Buat Tiket Baru"])
        if st.button("🔒 LOGOUT", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

# --- 7. MENU LOGIC ---
if not st.session_state.logged_in:
    menu = "Buat Tiket Baru"

# --- DASHBOARD ---
if menu == "Dashboard Monitor":
    st.markdown("<h2 style='color: white;'>📊 Monitoring Center</h2>", unsafe_allow_html=True)
    db = get_connection()
    df = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", db)
    db.close()

    if 'waktu_selesai' in df.columns:
        df['waktu_selesai'] = df.apply(lambda r: get_wib_now().strftime('%Y-%m-%d %H:%M:%S') if (r['status'] == 'Solved' and (r['waktu_selesai'] is None or str(r['waktu_selesai']) == 'None')) else r['waktu_selesai'], axis=1)

    df_display = df.rename(columns={'nama_user': 'Nama Teknisi'})

    q = st.text_input("🔍 Cari Tiket/Teknisi...", placeholder="Ketik di sini untuk filter data...")
    if q: df_display = df_display[df_display.apply(lambda r: r.astype(str).str.contains(q, case=False).any(), axis=1)]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", len(df_display))
    c2.metric("🔴 Open", len(df_display[df_display['status'] == 'Open']))
    c3.metric("🟡 Progress", len(df_display[df_display['status'] == 'In Progress']))
    c4.metric("🟢 Solved", len(df_display[df_display['status'] == 'Solved']))

    def color_status(val):
        color = '#ffffff'
        if val == 'Open': color = '#ff4b4b'
        elif val == 'In Progress': color = '#faca2b'
        elif val == 'Solved': color = '#00d488'
        return f'color: {color}; font-weight: bold;'

    st.dataframe(df_display.style.map(color_status, subset=['status']), use_container_width=True, hide_index=True)

    st.markdown("<div class='action-header'>⚡ CONTROL PANEL</div>", unsafe_allow_html=True)
    col_up, col_del = st.columns(2)
    with col_up:
        with st.expander("🔄 Update Status Pekerjaan"):
            if not df.empty:
                id_up = st.selectbox("Pilih ID Tiket", df['id'].tolist(), key="up_select")
                st_up = st.selectbox("Set Status", ["Open", "In Progress", "Solved", "Closed"])
                if st.button("SIMPAN PERUBAHAN", type="primary", use_container_width=True):
                    db = get_connection()
                    cur = db.cursor()
                    if st_up == "Solved":
                        cur.execute("UPDATE tickets SET status=%s, waktu_selesai=%s WHERE id=%s", (st_up, get_wib_now().strftime('%Y-%m-%d %H:%M:%S'), id_up))
                    else:
                        cur.execute("UPDATE tickets SET status=%s WHERE id=%s", (st_up, id_up))
                    db.close()
                    add_log("UPDATE", f"ID #{id_up} diubah ke {st_up}")
                    st.toast(f"ID #{id_up} Updated!")
                    st.rerun()
    with col_del:
        with st.expander("🗑️ Hapus Tiket (Admin Only)"):
            if not df.empty:
                id_del = st.selectbox("Pilih ID Hapus", df['id'].tolist(), key="del_select")
                if st.button("KONFIRMASI HAPUS", use_container_width=True):
                    db = get_connection()
                    cur = db.cursor()
                    cur.execute("DELETE FROM tickets WHERE id=%s", (id_del))
                    db.close()
                    add_log("DELETE", f"Hapus Tiket #{id_del}")
                    st.toast("Data Terhapus!")
                    st.rerun()

# --- EXPORT & REPORTING ---
elif menu == "Export & Reporting":
    st.markdown("<h2 style='color: white;'>📂 Financial & Operations Report</h2>", unsafe_allow_html=True)
    db = get_connection()
    df_ex = pd.read_sql("SELECT * FROM tickets", db)
    db.close()
    st.dataframe(df_ex, use_container_width=True)
    csv = df_ex.to_csv(index=False).encode('utf-8')
    st.download_button("📥 DOWNLOAD CSV (EXCEL)", csv, f"Report_IT_{get_wib_now().strftime('%Y%m%d')}.csv", "text/csv", use_container_width=True)

# --- SECURITY LOG ---
elif menu == "Security Log":
    st.markdown("<h2 style='color: white;'>🛡️ Security Audit Log</h2>", unsafe_allow_html=True)
    if st.session_state.audit_logs:
        st.dataframe(pd.DataFrame(st.session_state.audit_logs), use_container_width=True, hide_index=True)
    else: st.info("Belum ada aktivitas terekam.")

# --- BUAT TIKET BARU ---
elif menu == "Buat Tiket Baru":
    st.markdown("<h1 style='text-align: center; color: white;'>📝 Form Laporan IT</h1>", unsafe_allow_html=True)
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
                    cur.execute("INSERT INTO tickets (nama_user, cabang, masalah, prioritas, status) VALUES (%s,%s,%s,%s,'Open')", (user, cabang, issue, prio))
                    db.close()
                    st.success("Laporan berhasil dikirim!")
                    st.balloons()
