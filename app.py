import streamlit as st
import pymysql
import pandas as pd
import certifi
from datetime import datetime, timedelta
import io # Untuk fitur Export Excel

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="IT Helpdesk Pro v2.5", 
    page_icon="🎫", 
    layout="wide"
)

# --- FUNGSI WAKTU WIB ---
def get_wib_now():
    return datetime.now() + timedelta(hours=7)

# --- SISTEM AUDIT LOG ---
if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = []

def add_log(action, details):
    log_entry = {
        "Waktu": get_wib_now().strftime('%H:%M:%S'),
        "User": st.session_state.user_name.upper() if 'user_name' in st.session_state else "GUEST",
        "Aksi": action, "Detail": details
    }
    st.session_state.audit_logs.insert(0, log_entry)

# --- UI STYLE ---
st.markdown("""
    <style>
    /* Status Coloring */
    .status-open { color: #ef4444; font-weight: bold; }
    .status-progress { color: #f59e0b; font-weight: bold; }
    .status-solved { color: #10b981; font-weight: bold; }
    
    div[data-testid="metric-container"] {
        background-color: rgba(28, 131, 225, 0.07);
        border: 1px solid rgba(28, 131, 225, 0.2);
        padding: 15px; border-radius: 12px;
    }
    .digital-clock {
        font-family: 'Courier New', monospace;
        color: #10b981; font-size: 26px; font-weight: bold;
    }
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
    
    # LIVE CLOCK
    wib = get_wib_now()
    st.markdown(f"""<div style="text-align: center; border: 1px solid #1d4ed8; padding: 10px; border-radius: 12px; margin-bottom: 20px;">
        <div class="digital-clock">{wib.strftime('%H:%M:%S')}</div>
        <div style="font-size: 12px;">{wib.strftime('%A, %d %b %Y')}</div>
    </div>""", unsafe_allow_html=True)

    if 'logged_in' not in st.session_state: st.session_state.logged_in = False

    if not st.session_state.logged_in:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("LOGIN", use_container_width=True, type="primary"):
            if u in st.secrets["auth"] and p == st.secrets["auth"][u]:
                st.session_state.logged_in = True
                st.session_state.user_name = u
                add_log("LOGIN", "Masuk sistem")
                st.rerun()
    else:
        st.success(f"User: {st.session_state.user_name.upper()}")
        if st.button("LOGOUT", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

# --- NAVIGATION ---
if st.session_state.logged_in:
    menu = st.sidebar.selectbox("📂 MENU", ["Dashboard", "Laporan (Export)", "Security Log", "Buat Tiket"])
else:
    menu = "Buat Tiket"

# --- MENU: DASHBOARD (WITH SLA WARNING) ---
if menu == "Dashboard" and st.session_state.logged_in:
    st.title("📊 Monitoring Dashboard")
    
    db = get_connection()
    df = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", db)
    db.close()

    # LOGIKA SLA (Tanpa Ubah DB)
    # Jika status masih 'Open' dan sudah lewat 24 jam sejak dibuat, tandai sebagai 'OVERDUE'
    def check_sla(row):
        # Asumsi kolom waktu di DB lo bernama 'waktu_dibuat' atau 'created_at'
        # Jika tidak ada, fitur ini akan skip secara otomatis
        try:
            diff = get_wib_now() - row['created_at']
            if row['status'] == 'Open' and diff.days >= 1:
                return "🚨 OVERDUE"
            return row['status']
        except:
            return row['status']

    df['SLA_Status'] = df.apply(check_sla, axis=1)

    # Search & Metrics
    q = st.text_input("🔍 Cari Data...")
    if q: df = df[df.apply(lambda r: r.astype(str).str.contains(q, case=False).any(), axis=1)]

    st.dataframe(df, use_container_width=True, hide_index=True)

    # Update Action
    with st.expander("⚙️ Quick Update Status"):
        id_up = st.selectbox("Pilih ID", df['id'].tolist() if not df.empty else [None])
        st_up = st.selectbox("Status Baru", ["Open", "In Progress", "Solved", "Closed"])
        if st.button("Update Sekarang"):
            db = get_connection()
            cur = db.cursor()
            cur.execute("UPDATE tickets SET status=%s WHERE id=%s", (st_up, id_up))
            db.close()
            add_log("UPDATE", f"Tiket #{id_up} jadi {st_up}")
            st.rerun()

# --- MENU: LAPORAN (EXPORT EXCEL) ---
elif menu == "Laporan (Export)" and st.session_state.logged_in:
    st.title("📂 Export Laporan IT")
    st.write("Gunakan fitur ini untuk mendownload data tiket ke format CSV (Excel Friendly).")
    
    db = get_connection()
    df_export = pd.read_sql("SELECT * FROM tickets", db)
    db.close()

    if not df_export.empty:
        # Menampilkan data yang akan diexport
        st.dataframe(df_export)
        
        # Tombol Download
        csv = df_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Data Tiket (.CSV)",
            data=csv,
            file_name=f"Laporan_IT_{get_wib_now().strftime('%Y%m%d')}.csv",
            mime='text/csv',
            use_container_width=True
        )
    else:
        st.warning("Tidak ada data untuk diexport.")

# --- MENU: SECURITY LOG ---
elif menu == "Security Log" and st.session_state.logged_in:
    st.title("🛡️ Audit Log")
    st.table(st.session_state.audit_logs)

# --- MENU: BUAT TIKET ---
elif menu == "Buat Tiket":
    st.title("📝 Submit Ticket")
    with st.form("f"):
        u = st.text_input("Nama")
        c = st.selectbox("Cabang", st.secrets["master"]["daftar_cabang"])
        i = st.text_area("Kendala")
        p = st.select_slider("Prioritas", ["Low", "Medium", "High"])
        if st.form_submit_button("KIRIM"):
            db = get_connection()
            cur = db.cursor()
            cur.execute("INSERT INTO tickets (nama_user, cabang, masalah, prioritas, status) VALUES (%s,%s,%s,%s,'Open')", (u,c,i,p))
            db.close()
            st.success("Terkirim!")
            st.balloons()
