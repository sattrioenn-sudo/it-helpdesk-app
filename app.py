import streamlit as st
import pymysql
import pandas as pd
import certifi
from datetime import datetime, timedelta
import io

# --- 1. KONFIGURASI & THEME ---
st.set_page_config(page_title="IT Kemasan", page_icon="🎫", layout="wide")

# --- 2. LOGIKA USER PERSISTENT & PRIVILEGES ---
if 'user_privileges' not in st.session_state:
    default_privs = {}
    for user in st.secrets["auth"]:
        default_privs[user] = {
            "input_ticket": True, "hapus_ticket": True,
            "input_barang": True, "hapus_barang": True
        }
    st.session_state.user_privileges = default_privs

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_name' not in st.session_state:
    st.session_state.user_name = ""

def has_access(priv_name):
    user = st.session_state.user_name
    return st.session_state.user_privileges.get(user, {}).get(priv_name, False)

# --- 3. DATABASE & TIME ---
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

# --- 4. CSS CUSTOM ---
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
        padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 25px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. LOGIKA AUDIT LOG ---
if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = []

def add_log(action, details):
    waktu = get_wib_now().strftime('%H:%M:%S')
    st.session_state.audit_logs.insert(0, {"Waktu": waktu, "User": st.session_state.user_name.upper(), "Aksi": action, "Detail": details})

# --- 6. SIDEBAR ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: white;'>🎫 IT-Kemasan</h1>", unsafe_allow_html=True)
    if not st.session_state.logged_in:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("🔓 SIGN IN", use_container_width=True, type="primary"):
            if u in st.secrets["auth"] and p == st.secrets["auth"][u]:
                st.session_state.logged_in = True
                st.session_state.user_name = u
                add_log("LOGIN", "Masuk Dashboard")
                st.rerun()
            else: st.error("Credential Salah!")
    else:
        st.markdown(f"<p style='text-align: center;'>Operator: <b>{st.session_state.user_name.upper()}</b></p>", unsafe_allow_html=True)
        menu = st.selectbox("📂 MAIN MENU", ["Dashboard Monitor", "📦 Inventory Spareparts", "Export & Reporting", "User Management"])
        if st.button("🔒 LOGOUT", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

# --- 7. MENU LOGIC ---
if not st.session_state.logged_in: menu = "Quick Input Mode"

# --- HALAMAN 1: DASHBOARD MONITOR ---
if menu == "Dashboard Monitor" and st.session_state.logged_in:
    st.markdown("## 📊 Monitoring Center")
    db = get_connection(); df = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", db); db.close()
    
    # --- KEMBALIKAN METRIK DASHBOARD ---
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Tickets", len(df))
    c2.metric("🔴 Open", len(df[df['status'] == 'Open']))
    c3.metric("🟡 In Progress", len(df[df['status'] == 'In Progress']))
    c4.metric("🟢 Solved", len(df[df['status'] == 'Solved']))

    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("<div class='action-header'>⚡ Action Center</div>", unsafe_allow_html=True)
    col_input, col_ctrl = st.columns(2)
    
    with col_input:
        with st.expander("🆕 Input Tiket Baru", expanded=True):
            if has_access("input_ticket"):
                with st.form("form_ticket", clear_on_submit=True):
                    u_in = st.text_input("Nama")
                    i_in = st.text_area("Kendala")
                    if st.form_submit_button("KIRIM", use_container_width=True):
                        if u_in and i_in:
                            db = get_connection(); cur = db.cursor()
                            cur.execute("INSERT INTO tickets (nama_user, masalah, status, waktu) VALUES (%s,%s,'Open',%s)", (u_in, i_in, get_wib_now().strftime('%Y-%m-%d %H:%M:%S')))
                            db.close(); add_log("INPUT", f"Tiket: {u_in}"); st.rerun()
            else: st.warning("🚫 Akses Input Tiket Dinonaktifkan.")

    with col_ctrl:
        with st.expander("🔄 Control Tiket", expanded=True):
            if not df.empty:
                id_target = st.selectbox("Pilih ID", df['id'].tolist())
                c_save, c_del = st.columns(2)
                with c_save:
                    if st.button("💾 UPDATE STATUS", use_container_width=True):
                        add_log("UPDATE", f"ID #{id_target}"); st.toast("Status Updated!")
                with c_del:
                    # HARD LOCK DELETE: Cek akses sebelum eksekusi SQL
                    btn_del = st.button("🗑️ HAPUS TICKET", use_container_width=True, disabled=not has_access("hapus_ticket"))
                    if btn_del:
                        if has_access("hapus_ticket"):
                            db = get_connection(); cur = db.cursor()
                            cur.execute("DELETE FROM tickets WHERE id=%s", (id_target,))
                            db.close(); add_log("DELETE", f"Hapus Tiket #{id_target}"); st.rerun()
                        else: st.error("Aksi Ilegal!")

# --- HALAMAN 4: USER MANAGEMENT ---
elif menu == "User Management" and st.session_state.logged_in:
    st.markdown("## 👤 User Access Management")
    st.info("Atur hak akses secara real-time. Pengaturan ini tersimpan selama sesi aktif.")
    
    for u_name in list(st.secrets["auth"].keys()):
        with st.expander(f"HAK AKSES: {u_name.upper()}"):
            c1, c2, c3, c4 = st.columns(4)
            st.session_state.user_privileges[u_name]["input_ticket"] = c1.toggle("Input Tiket", value=st.session_state.user_privileges[u_name]["input_ticket"], key=f"it_{u_name}")
            st.session_state.user_privileges[u_name]["hapus_ticket"] = c2.toggle("Hapus Tiket", value=st.session_state.user_privileges[u_name]["hapus_ticket"], key=f"ht_{u_name}")
            st.session_state.user_privileges[u_name]["input_barang"] = c3.toggle("Input Barang", value=st.session_state.user_privileges[u_name]["input_barang"], key=f"ib_{u_name}")
            st.session_state.user_privileges[u_name]["hapus_barang"] = c4.toggle("Hapus Barang", value=st.session_state.user_privileges[u_name]["hapus_barang"], key=f"hb_{u_name}")
    
    if st.button("💾 SIMPAN PERUBAHAN", use_container_width=True, type="primary"):
        st.success("Hak akses berhasil diperbarui!"); st.rerun()

# --- HALAMAN INVENTORY & EXPORT (Sesuai Code Awal) ---
elif menu == "📦 Inventory Spareparts" and st.session_state.logged_in:
    try:
        from spareparts import show_sparepart_menu
        show_sparepart_menu(get_connection, get_wib_now, add_log)
    except Exception as e: st.error(f"Module Error: {e}")

elif menu == "Export & Reporting" and st.session_state.logged_in:
    st.markdown("## 📂 Export Report")
    db = get_connection(); df_ex = pd.read_sql("SELECT * FROM tickets", db); db.close()
    st.dataframe(df_ex, use_container_width=True)
    st.download_button("📥 DOWNLOAD CSV", df_ex.to_csv(index=False).encode('utf-8'), "Report.csv", "text/csv")

elif menu == "Quick Input Mode":
    st.markdown("<h1 style='text-align: center;'>📝 Form Laporan IT</h1>", unsafe_allow_html=True)
    with st.form("form_guest"):
        u_g = st.text_input("Nama"); i_g = st.text_area("Kendala")
        if st.form_submit_button("KIRIM", use_container_width=True):
            if u_g and i_g:
                db = get_connection(); cur = db.cursor()
                cur.execute("INSERT INTO tickets (nama_user, masalah, status, waktu) VALUES (%s,%s,'Open',%s)", (u_g, i_g, get_wib_now().strftime('%Y-%m-%d %H:%M:%S')))
                db.close(); st.success("Laporan terkirim!")
