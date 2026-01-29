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

# Memori Virtual (Keterangan & Hak Akses)
if 'custom_keterangan' not in st.session_state:
    st.session_state.custom_keterangan = {}
if 'user_permissions' not in st.session_state:
    # Default: Admin (u) punya semua akses, user lain terbatas
    st.session_state.user_permissions = {
        "admin": ["Input", "Edit", "Hapus", "Export", "Security"],
        "user": ["Input"]
    }

# --- 3. FUNGSI CEK AKSES ---
def check_permission(perm):
    user = st.session_state.user_name
    perms = st.session_state.user_permissions.get(user, ["Input"]) # Default hanya input
    return perm in perms

# --- 4. FUNGSI WAKTU & DATABASE ---
def get_wib_now():
    return datetime.utcnow() + timedelta(hours=7)

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

# --- 5. CSS (TETAP UTUH) ---
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top right, #0e1117, #1c2533); }
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 20px; border-radius: 15px; color: white !important;
    }
    .action-header {
        background: rgba(255, 255, 255, 0.05); padding: 10px 20px; border-radius: 10px;
        border-left: 5px solid #1d4ed8; margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 6. LOGIKA AUDIT LOG ---
if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = []

def add_log(action, details):
    st.session_state.audit_logs.insert(0, {
        "Waktu": get_wib_now().strftime('%H:%M:%S'),
        "User": st.session_state.user_name.upper(),
        "Aksi": action, "Detail": details
    })

# --- 7. SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center;'>🎫 IT-Kemasan</h1>", unsafe_allow_html=True)
    if st.session_state.logged_in:
        st.markdown(f"<p style='text-align: center;'>Operator: <b>{st.session_state.user_name.upper()}</b></p>", unsafe_allow_html=True)
        # Filter menu berdasarkan akses Security
        menu_list = ["Dashboard Monitor", "📦 Inventory Spareparts"]
        if check_permission("Export"): menu_list.append("Export & Reporting")
        if check_permission("Security"): menu_list.append("Security Settings")
        
        menu = st.selectbox("📂 MAIN MENU", menu_list)
        if st.button("🔒 LOGOUT"):
            st.session_state.logged_in = False
            st.rerun()
    else:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("🔓 SIGN IN"):
            if u in st.secrets["auth"] and p == st.secrets["auth"][u]:
                st.session_state.logged_in = True
                st.session_state.user_name = u
                st.rerun()

# --- 8. LOGIC ---
if not st.session_state.logged_in:
    menu = "Quick Input Mode"

# --- DASHBOARD ---
if menu == "Dashboard Monitor":
    db = get_connection()
    df = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", db); db.close()
    
    # Injeksi Keterangan Virtual
    df['Keterangan'] = df['id'].apply(lambda x: st.session_state.custom_keterangan.get(x, "-"))
    
    df_disp = df.rename(columns={'nama_user': 'Nama Teknisi', 'masalah': 'Problem', 'waktu': 'Waktu Laporan'})
    cols = ['id', 'Nama Teknisi', 'Problem', 'Keterangan', 'status', 'Waktu Laporan']
    st.dataframe(df_disp[[c for c in cols if c in df_disp.columns]], use_container_width=True, hide_index=True)

    st.markdown("<div class='action-header'>⚡ Action Center</div>", unsafe_allow_html=True)
    c_in, c_ed = st.columns(2)

    with c_in:
        with st.expander("🆕 Input Tiket"):
            if check_permission("Input"):
                with st.form("f_in", clear_on_submit=True):
                    u_in = st.text_input("Nama"); prob = st.text_area("Masalah")
                    if st.form_submit_button("KIRIM"):
                        db = get_connection(); cur = db.cursor()
                        cur.execute("INSERT INTO tickets (nama_user, masalah, status, waktu) VALUES (%s,%s,'Open',%s)", (u_in, prob, get_wib_now().strftime('%Y-%m-%d %H:%M:%S')))
                        db.close(); add_log("INPUT", u_in); st.rerun()
            else: st.warning("Akses Input Dibatasi")

    with c_ed:
        with st.expander("🔄 Edit / Hapus"):
            if check_permission("Edit"):
                id_up = st.selectbox("ID", df['id'].tolist())
                new_ket = st.text_input("Edit Keterangan SSD/HW", value=st.session_state.custom_keterangan.get(id_up, ""))
                st_up = st.selectbox("Status", ["Open", "In Progress", "Solved"])
                
                b1, b2 = st.columns(2)
                if b1.button("💾 UPDATE"):
                    st.session_state.custom_keterangan[id_up] = new_ket
                    db = get_connection(); cur = db.cursor()
                    cur.execute("UPDATE tickets SET status=%s WHERE id=%s", (st_up, id_up))
                    db.close(); add_log("UPDATE", f"ID {id_up}"); st.rerun()
                
                if b2.button("🗑️ HAPUS"):
                    if check_permission("Hapus"):
                        db = get_connection(); cur = db.cursor()
                        cur.execute("DELETE FROM tickets WHERE id=%s", (id_up))
                        db.close(); add_log("DELETE", f"ID {id_up}"); st.rerun()
                    else: st.error("Akses Hapus Dibatasi")
            else: st.warning("Akses Edit Dibatasi")

# --- EXPORT (FIXED) ---
elif menu == "Export & Reporting":
    st.markdown("## 📂 Export Data")
    db = get_connection()
    df_ex = pd.read_sql("SELECT * FROM tickets", db); db.close()
    # Tambahkan Keterangan Virtual agar data tidak hilang saat di-export
    df_ex['Keterangan_IT'] = df_ex['id'].apply(lambda x: st.session_state.custom_keterangan.get(x, "-"))
    st.dataframe(df_ex, use_container_width=True)
    st.download_button("📥 DOWNLOAD CSV", df_ex.to_csv(index=False).encode('utf-8'), "IT_Report.csv")

# --- SECURITY SETTINGS (USER ACCESS CONTROL) ---
elif menu == "Security Settings":
    st.markdown("## 🛡️ User Access Control (Virtual)")
    
    # Pilih User dari daftar auth di secrets
    target_user = st.selectbox("Pilih User untuk Diatur Aksesnya", list(st.secrets["auth"].keys()))
    
    # Jika user belum ada di permissions, beri default
    if target_user not in st.session_state.user_permissions:
        st.session_state.user_permissions[target_user] = ["Input"]

    st.write(f"Hak Akses Saat Ini untuk **{target_user}**: {st.session_state.user_permissions[target_user]}")
    
    options = ["Input", "Edit", "Hapus", "Export", "Security"]
    new_perms = st.multiselect("Tentukan Hak Akses Baru", options, default=st.session_state.user_permissions[target_user])
    
    if st.button("💾 SIMPAN HAK AKSES"):
        st.session_state.user_permissions[target_user] = new_perms
        add_log("SECURITY", f"Update Akses {target_user}")
        st.success(f"Akses {target_user} berhasil diperbarui!")
        st.rerun()
    
    st.divider()
    st.markdown("### 📋 Audit Log")
    st.dataframe(pd.DataFrame(st.session_state.audit_logs), use_container_width=True)

elif menu == "Quick Input Mode":
    st.write("Guest Mode Aktif")
