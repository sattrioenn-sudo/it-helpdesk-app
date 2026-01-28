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
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background: radial-gradient(circle at top right, #10141d, #05070a);
    }

    /* Glassmorphism Metric Cards */
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        backdrop-filter: blur(15px);
        padding: 25px;
        border-radius: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        transition: transform 0.3s ease;
    }
    div[data-testid="metric-container"]:hover {
        transform: translateY(-5px);
        border-color: #1d4ed8;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: rgba(10, 15, 25, 0.8) !important;
        backdrop-filter: blur(10px);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }

    /* Premium Clock */
    .clock-box {
        background: linear-gradient(135deg, #1e40af 0%, #1e3a8a 100%);
        padding: 20px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 30px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 10px 20px rgba(0,0,0,0.4);
    }
    .digital-clock {
        color: #ffffff;
        font-size: 32px;
        font-weight: 800;
        letter-spacing: 2px;
        text-shadow: 0 0 10px rgba(255,255,255,0.3);
    }

    /* Status Tags Styling */
    .stDataFrame {
        border-radius: 20px;
        overflow: hidden;
    }

    /* Action Center Header */
    .action-header {
        background: linear-gradient(90deg, rgba(29,78,216,0.15) 0%, rgba(29,78,216,0) 100%);
        padding: 15px 25px;
        border-radius: 15px;
        border-left: 6px solid #1d4ed8;
        margin: 30px 0 20px 0;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    
    /* Buttons Custom */
    .stButton>button {
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.3s;
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
    st.markdown("<h1 style='text-align: center; color: white; font-size: 24px;'>🎫 IT-KEMASAN PRO</h1>", unsafe_allow_html=True)
    wib = get_wib_now()
    st.markdown(f"""
        <div class="clock-box">
            <div class="digital-clock">{wib.strftime('%H:%M:%S')}</div>
            <div style="color: rgba(255,255,255,0.7); font-size: 13px; font-weight: 600; margin-top: 5px;">{wib.strftime('%A, %d %b %Y')}</div>
        </div>
    """, unsafe_allow_html=True)

    if 'logged_in' not in st.session_state: st.session_state.logged_in = False

    if not st.session_state.logged_in:
        with st.container():
            u = st.text_input("Username", placeholder="Input username...")
            p = st.text_input("Password", type="password", placeholder="Input password...")
            if st.button("🔓 SIGN IN SYSTEM", use_container_width=True, type="primary"):
                if u in st.secrets["auth"] and p == st.secrets["auth"][u]:
                    st.session_state.logged_in = True
                    st.session_state.user_name = u
                    add_log("LOGIN", "Masuk Dashboard")
                    st.rerun()
    else:
        st.markdown(f"""
            <div style='background: rgba(255,255,255,0.05); padding: 15px; border-radius: 15px; text-align: center; margin-bottom: 20px;'>
                <span style='color: rgba(255,255,255,0.6); font-size: 12px;'>ACTIVE OPERATOR</span><br>
                <b style='color: #10b981; font-size: 18px;'>{st.session_state.user_name.upper()}</b>
            </div>
        """, unsafe_allow_html=True)
        if st.button("🔒 LOGOUT", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

# --- 7. MAIN NAVIGATION ---
if st.session_state.logged_in:
    menu = st.sidebar.selectbox("📂 NAVIGATION", ["Dashboard Monitor", "Export & Reporting", "Security Log", "Buat Tiket Baru"])
else:
    menu = "Buat Tiket Baru"

# --- 8. MENU LOGIC ---

if menu == "Dashboard Monitor" and st.session_state.logged_in:
    st.markdown("<h2 style='color: white;'>📊 System Monitoring Center</h2>", unsafe_allow_html=True)
    
    db = get_connection()
    df = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", db)
    db.close()

    # Perbaikan None
    if 'waktu_selesai' in df.columns:
        df['waktu_selesai'] = df.apply(
            lambda r: get_wib_now().strftime('%Y-%m-%d %H:%M:%S') if (r['status'] == 'Solved' and (r['waktu_selesai'] is None or str(r['waktu_selesai']) == 'None')) else r['waktu_selesai'],
            axis=1
        )

    df_display = df.rename(columns={'nama_user': 'Nama Teknisi'})

    # Search Console with Styling
    q = st.text_input("🔍 Filter Dashboard", placeholder="Cari teknisi, lokasi, atau ID tiket...")
    if q: 
        df_display = df_display[df_display.apply(lambda r: r.astype(str).str.contains(q, case=False).any(), axis=1)]

    # Metrics with visual enhancement
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Antrean", len(df_display))
    c2.metric("🔴 OPEN", len(df_display[df_display['status'] == 'Open']))
    c3.metric("🟡 PROGRESS", len(df_display[df_display['status'] == 'In Progress']))
    c4.metric("🟢 SOLVED", len(df_display[df_display['status'] == 'Solved']))

    # Advanced Color Coding for Dataframe
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
                        waktu_fix = get_wib_now().strftime('%Y-%m-%d %H:%M:%S')
                        cur.execute("UPDATE tickets SET status=%s, waktu_selesai=%s WHERE id=%s", (st_up, waktu_fix, id_up))
                    else:
                        cur.execute("UPDATE tickets SET status=%s WHERE id=%s", (st_up, id_up))
                    db.close()
                    add_log("UPDATE", f"ID #{id_up} diubah ke {st_up}")
                    st.toast(f"ID #{id_up} Berhasil Diupdate!", icon="✅")
                    st.rerun()

    with col_del:
        with st.expander("🗑️ Hapus Tiket (Danger Zone)"):
            if not df.empty:
                id_del = st.selectbox("Pilih ID Hapus", df['id'].tolist(), key="del_select")
                st.warning(f"Aksi hapus ID #{id_del} bersifat permanen!")
                if st.button("KONFIRMASI HAPUS", use_container_width=True):
                    db = get_connection()
                    cur = db.cursor()
                    cur.execute("DELETE FROM tickets WHERE id=%s", (id_del))
                    db.close()
                    add_log("DELETE", f"Menghapus Tiket ID #{id_del}")
                    st.toast("Data Terhapus Selamanya!", icon="🔥")
                    st.rerun()

elif menu == "Buat Tiket Baru":
    st.markdown("<h1 style='text-align: center; color: white; margin-bottom: 30px;'>📝 Form Laporan Kendala IT</h1>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        with st.form("form_entry", clear_on_submit=True):
            user = st.text_input("Nama Lengkap Pelapor")
            cabang = st.selectbox("Lokasi Cabang", st.secrets["master"]["daftar_cabang"])
            issue = st.text_area("Deskripsi Masalah")
            prio = st.select_slider("Tingkat Urgensi", ["Low", "Medium", "High"])
            
            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("KIRIM LAPORAN KE IT 🚀", use_container_width=True):
                if user and issue:
                    db = get_connection()
                    cur = db.cursor()
                    cur.execute("INSERT INTO tickets (nama_user, cabang, masalah, prioritas, status) VALUES (%s,%s,%s,%s,'Open')", (user, cabang, issue, prio))
                    db.close()
                    st.success("Tiket Anda telah masuk ke antrean IT. Mohon tunggu teknisi bertugas.")
                    st.balloons()
