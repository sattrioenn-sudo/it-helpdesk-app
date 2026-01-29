import streamlit as st
import pymysql
import pandas as pd
import certifi
from datetime import datetime, timedelta
import io

# --- 1. KONFIGURASI & THEME ---
st.set_page_config(page_title="IT Kemasan", page_icon="🎫", layout="wide")

# --- 2. LOGIKA PERSISTENT SESSION ---
@st.cache_resource
def get_auth_state():
    return {"logged_in": False, "user_name": ""}

auth = get_auth_state()
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = auth["logged_in"]
if 'user_name' not in st.session_state:
    st.session_state.user_name = auth["user_name"]

# Inisialisasi memori untuk Keterangan Custom (Agar tidak merubah DB)
if 'custom_keterangan' not in st.session_state:
    st.session_state.custom_keterangan = {}

# --- 3. FUNGSI WAKTU WIB ---
def get_wib_now():
    return datetime.utcnow() + timedelta(hours=7)

# --- 4. DATABASE CONNECTION ---
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

# --- 5. CSS CUSTOM (TETAP UTUH) ---
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top right, #0e1117, #1c2533); }
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 20px; border-radius: 15px;
        color: white !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #0e1117 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    .clock-box {
        background: linear-gradient(135deg, #1d4ed8 0%, #10b981 100%);
        padding: 15px; border-radius: 12px; text-align: center;
        margin-bottom: 25px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }
    .digital-clock {
        font-family: 'JetBrains Mono', monospace;
        color: white; font-size: 28px; font-weight: 800;
    }
    .stDataFrame { border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; }
    .action-header {
        background: rgba(255, 255, 255, 0.05);
        padding: 10px 20px; border-radius: 10px;
        border-left: 5px solid #1d4ed8; margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 6. LOGIKA AUDIT LOG ---
if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = []

def add_log(action, details):
    waktu = get_wib_now().strftime('%H:%M:%S')
    st.session_state.audit_logs.insert(0, {
        "Waktu": waktu,
        "User": st.session_state.user_name.upper() if st.session_state.user_name else "GUEST",
        "Aksi": action, "Detail": details
    })

# --- 7. SIDEBAR MANAGEMENT ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: white;'>🎫 IT-Kemasan Group</h1>", unsafe_allow_html=True)
    wib = get_wib_now()
    st.markdown(f'<div class="clock-box"><div class="digital-clock">{wib.strftime("%H:%M:%S")}</div></div>', unsafe_allow_html=True)

    if not st.session_state.logged_in:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("🔓 SIGN IN", use_container_width=True, type="primary"):
            if u in st.secrets["auth"] and p == st.secrets["auth"][u]:
                st.session_state.logged_in = True
                st.session_state.user_name = u
                st.rerun()
    else:
        st.markdown(f"<p style='text-align: center;'>Operator: <b>{st.session_state.user_name.upper()}</b></p>", unsafe_allow_html=True)
        menu = st.selectbox("📂 MAIN MENU", ["Dashboard Monitor", "📦 Inventory Spareparts", "Export & Reporting", "Security Log"])
        if st.button("🔒 LOGOUT", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

# --- 8. MENU LOGIC ---
if not st.session_state.logged_in:
    menu = "Quick Input Mode"

if menu == "Dashboard Monitor" and st.session_state.logged_in:
    st.markdown("## 📊 Monitoring Center")
    db = get_connection()
    df = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", db)
    db.close()

    # Gabungkan data Keterangan dari session_state ke DataFrame secara virtual
    df['Keterangan'] = df['id'].apply(lambda x: st.session_state.custom_keterangan.get(x, "-"))

    df_display = df.rename(columns={'nama_user': 'Nama Teknisi', 'masalah': 'Problem', 'waktu': 'Waktu Laporan'})
    
    # Atur urutan kolom agar Keterangan di kanan Problem
    cols = list(df_display.columns)
    if 'Problem' in cols and 'Keterangan' in cols:
        p_idx = cols.index('Problem')
        cols.insert(p_idx + 1, cols.pop(cols.index('Keterangan')))
    df_display = df_display[cols]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Tickets", len(df_display))
    c2.metric("🔴 Open", len(df_display[df_display['status'] == 'Open']))
    c3.metric("🟡 In Progress", len(df_display[df_display['status'] == 'In Progress']))
    c4.metric("🟢 Solved", len(df_display[df_display['status'] == 'Solved']))

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    st.markdown("<div class='action-header'>⚡ Unified Action & Input Center</div>", unsafe_allow_html=True)
    col_input, col_ctrl = st.columns([1.2, 1])
    
    with col_input:
        with st.expander("🆕 Input Tiket Baru", expanded=True):
            with st.form("form_quick_entry", clear_on_submit=True):
                u_in = st.text_input("Nama Lengkap")
                c_in = st.selectbox("Lokasi Cabang", st.secrets["master"]["daftar_cabang"])
                i_in = st.text_area("Deskripsi Kendala")
                p_in = st.select_slider("Urgensi", ["Low", "Medium", "High"])
                if st.form_submit_button("KIRIM LAPORAN 🚀", use_container_width=True):
                    if u_in and i_in:
                        db = get_connection(); cur = db.cursor()
                        cur.execute("INSERT INTO tickets (nama_user, cabang, masalah, prioritas, status, waktu) VALUES (%s,%s,%s,%s,'Open',%s)", (u_in, c_in, i_in, p_in, get_wib_now().strftime('%Y-%m-%d %H:%M:%S')))
                        db.close(); add_log("INPUT", f"Tiket: {u_in}"); st.rerun()

    with col_ctrl:
        with st.expander("🔄 Update Status & Keterangan", expanded=True):
            if not df.empty:
                id_up = st.selectbox("Pilih ID Tiket untuk Edit", df['id'].tolist())
                
                # Input khusus untuk Keterangan Hardware/SSD (Disimpan di session_state)
                current_ket = st.session_state.custom_keterangan.get(id_up, "")
                new_ket = st.text_input("Keterangan Hardware (SSD/RAM/dll)", value=current_ket)
                
                st_up = st.selectbox("Set Status Database", ["Open", "In Progress", "Solved", "Closed"])
                
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    if st.button("💾 SIMPAN SEMUA", use_container_width=True, type="primary"):
                        # Simpan ke session_state (Virtual)
                        st.session_state.custom_keterangan[id_up] = new_ket
                        # Simpan ke database (Status)
                        db = get_connection(); cur = db.cursor()
                        cur.execute("UPDATE tickets SET status=%s WHERE id=%s", (st_up, id_up))
                        db.close(); add_log("UPDATE", f"ID #{id_up} (Ket: {new_ket})"); st.rerun()
                
                with c_btn2:
                    if st.button("🗑️ HAPUS TIKET", use_container_width=True):
                        db = get_connection(); cur = db.cursor()
                        cur.execute("DELETE FROM tickets WHERE id=%s", (id_up,))
                        if id_up in st.session_state.custom_keterangan:
                            del st.session_state.custom_keterangan[id_up]
                        db.close(); add_log("DELETE", f"Hapus ID #{id_up}"); st.rerun()

# --- HALAMAN SPAREPARTS ---
elif menu == "📦 Inventory Spareparts" and st.session_state.logged_in:
    try:
        from spareparts import show_sparepart_menu
        show_sparepart_menu(get_connection, get_wib_now, add_log)
    except Exception as e:
        st.error(f"Error: {e}")

# ... (Halaman Export & Security Log tetap sama sesuai kode awalmu)
