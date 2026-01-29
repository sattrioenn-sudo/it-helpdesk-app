import streamlit as st
import pymysql
import pandas as pd
import certifi
from datetime import datetime, timedelta
import io

# --- 1. KONFIGURASI & THEME ---
st.set_page_config(page_title="IT Kemasan", page_icon="🎫", layout="wide")

# --- 2. LOGIKA USER PERSISTENT & PRIVILEGES ---
@st.cache_resource
def get_auth_state():
    return {"logged_in": False, "user_name": ""}

# Inisialisasi Hak Akses di Session State (Agar bisa diatur dinamis)
if 'user_privileges' not in st.session_state:
    # Default: Semua user di secrets diberikan akses penuh di awal
    # Format: { 'username': { 'input_ticket': True, 'hapus_ticket': True, ... } }
    default_privs = {}
    for user in st.secrets["auth"]:
        default_privs[user] = {
            "input_ticket": True,
            "hapus_ticket": True,
            "input_barang": True,
            "hapus_barang": True
        }
    st.session_state.user_privileges = default_privs

auth = get_auth_state()
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = auth["logged_in"]
if 'user_name' not in st.session_state:
    st.session_state.user_name = auth["user_name"]

# --- FUNGSI CEK AKSES ---
def has_access(priv_name):
    user = st.session_state.user_name
    return st.session_state.user_privileges.get(user, {}).get(priv_name, False)

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

# --- 5. CSS CUSTOM ---
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
    .action-header {
        background: rgba(255, 255, 255, 0.05);
        padding: 10px 20px; border-radius: 10px;
        border-left: 5px solid #1d4ed8; margin: 20px 0;
    }
    .clock-box {
        background: linear-gradient(135deg, #1d4ed8 0%, #10b981 100%);
        padding: 15px; border-radius: 12px; text-align: center;
        margin-bottom: 25px;
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
    st.markdown("<h1 style='text-align: center; color: white;'>🎫 IT-Kemasan</h1>", unsafe_allow_html=True)
    wib = get_wib_now()
    st.markdown(f'<div class="clock-box"><div style="color:white; font-size:20px;">{wib.strftime("%H:%M:%S")}</div></div>', unsafe_allow_html=True)

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
                st.error("Credential Salah!")
    else:
        st.markdown(f"<p style='text-align: center;'>Operator: <b>{st.session_state.user_name.upper()}</b></p>", unsafe_allow_html=True)
        # MENU SECURITY LOG DIGANTI KE USER MANAGEMENT
        menu = st.selectbox("📂 MAIN MENU", ["Dashboard Monitor", "📦 Inventory Spareparts", "Export & Reporting", "User Management"])
        if st.button("🔒 LOGOUT", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

if not st.session_state.logged_in:
    menu = "Quick Input Mode"

# --- HALAMAN 1: DASHBOARD MONITOR ---
if menu == "Dashboard Monitor" and st.session_state.logged_in:
    st.markdown("## 📊 Monitoring Center")
    db = get_connection(); df = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", db); db.close()
    
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("<div class='action-header'>⚡ Action Center</div>", unsafe_allow_html=True)
    col_input, col_ctrl = st.columns(2)
    
    with col_input:
        with st.expander("🆕 Input Tiket Baru", expanded=True):
            # CEK AKSES INPUT TICKET
            if has_access("input_ticket"):
                with st.form("form_ticket"):
                    u_in = st.text_input("Nama")
                    i_in = st.text_area("Kendala")
                    if st.form_submit_button("KIRIM", use_container_width=True):
                        db = get_connection(); cur = db.cursor()
                        cur.execute("INSERT INTO tickets (nama_user, masalah, status, waktu) VALUES (%s,%s,'Open',%s)", (u_in, i_in, get_wib_now()))
                        db.close(); add_log("INPUT", f"Tiket: {u_in}"); st.rerun()
            else:
                st.warning("🚫 Anda tidak punya akses Input Tiket.")

    with col_ctrl:
        with st.expander("🔄 Control Tiket", expanded=True):
            if not df.empty:
                id_target = st.selectbox("Pilih ID", df['id'].tolist())
                c_save, c_del = st.columns(2)
                with c_save:
                    if st.button("💾 UPDATE STATUS", use_container_width=True):
                        # Update status (biasanya teknisi bisa update)
                        add_log("UPDATE", f"ID #{id_target}"); st.toast("Updated!")
                with c_del:
                    # CEK AKSES HAPUS TICKET
                    if st.button("🗑️ HAPUS TICKET", use_container_width=True, disabled=not has_access("hapus_ticket")):
                        db = get_connection(); cur = db.cursor()
                        cur.execute("DELETE FROM tickets WHERE id=%s", (id_target,))
                        db.close(); add_log("DELETE", f"ID #{id_target}"); st.rerun()
                    if not has_access("hapus_ticket"):
                        st.caption("Akses hapus dikunci.")

# --- HALAMAN 2: SPAREPART INVENTORY ---
elif menu == "📦 Inventory Spareparts" and st.session_state.logged_in:
    # Mengirimkan status hak akses ke modul sparepart
    try:
        from spareparts import show_sparepart_menu
        # Modifikasi pemanggilan dengan parameter akses
        show_sparepart_menu(get_connection, get_wib_now, add_log)
        
        # Note: Pastikan di spareparts.py, tombol input/hapus dicek menggunakan:
        # if st.session_state.user_privileges[st.session_state.user_name]['input_barang']:
    except Exception as e:
        st.error(f"Error: {e}")

# --- HALAMAN 4: USER MANAGEMENT (PENGGANTI SECURITY LOG) ---
elif menu == "User Management" and st.session_state.logged_in:
    st.markdown("## 👤 User Access Management")
    st.info("Atur hak akses setiap user. Perubahan bersifat sementara (Reset jika aplikasi restart/refresh berat).")
    
    users = list(st.secrets["auth"].keys())
    
    for u_name in users:
        with st.expander(f"User: {u_name.upper()}", expanded=(u_name == st.session_state.user_name)):
            c1, c2, c3, c4 = st.columns(4)
            
            # Update Session State langsung saat checkbox diklik
            st.session_state.user_privileges[u_name]["input_ticket"] = c1.checkbox(
                "Input Ticket", value=st.session_state.user_privileges[u_name]["input_ticket"], key=f"it_{u_name}")
            
            st.session_state.user_privileges[u_name]["hapus_ticket"] = c2.checkbox(
                "Hapus Ticket", value=st.session_state.user_privileges[u_name]["hapus_ticket"], key=f"ht_{u_name}")
            
            st.session_state.user_privileges[u_name]["input_barang"] = c3.checkbox(
                "Input Barang", value=st.session_state.user_privileges[u_name]["input_barang"], key=f"ib_{u_name}")
            
            st.session_state.user_privileges[u_name]["hapus_barang"] = c4.checkbox(
                "Hapus Barang", value=st.session_state.user_privileges[u_name]["hapus_barang"], key=f"hb_{u_name}")

    if st.button("✅ Terapkan Perubahan", use_container_width=True, type="primary"):
        st.success("Hak akses diperbarui!")
        st.rerun()

# --- HALAMAN EXPORT ---
elif menu == "Export & Reporting" and st.session_state.logged_in:
    st.markdown("## 📂 Export Report")
    db = get_connection(); df_ex = pd.read_sql("SELECT * FROM tickets", db); db.close()
    st.dataframe(df_ex, use_container_width=True)

# --- QUICK INPUT (GUEST) ---
elif menu == "Quick Input Mode":
    st.markdown("<h1 style='text-align: center;'>📝 Form Laporan IT</h1>", unsafe_allow_html=True)
    with st.form("form_guest"):
        u_g = st.text_input("Nama"); i_g = st.text_area("Kendala")
        if st.form_submit_button("KIRIM", use_container_width=True):
            db = get_connection(); cur = db.cursor()
            cur.execute("INSERT INTO tickets (nama_user, masalah, status, waktu) VALUES (%s,%s,'Open',%s)", (u_g, i_g, get_wib_now()))
            db.close(); st.success("Terkirim!")
