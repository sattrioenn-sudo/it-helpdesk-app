import streamlit as st
import pymysql
import pandas as pd
import certifi
import json
import os
from datetime import datetime, timedelta

# --- 1. KONFIGURASI & THEME ---
st.set_page_config(page_title="IT Kemasan", page_icon="🎫", layout="wide")

# --- 2. STORAGE VIRTUAL (AGAR DATA TIDAK HILANG) ---
def load_data(file, default):
    if os.path.exists(file):
        with open(file, 'r') as f: return json.load(f)
    return default

def save_data(file, data):
    with open(file, 'w') as f: json.dump(data, f)

# Inisialisasi Data Virtual
if 'custom_keterangan' not in st.session_state:
    st.session_state.custom_keterangan = load_data('keterangan_it.json', {})
if 'user_permissions' not in st.session_state:
    # Default: Admin dpt semua, yang lain diatur via menu Security
    st.session_state.user_permissions = load_data('permissions_it.json', {"admin": ["Input", "Edit", "Hapus", "Export", "Security"]})

# --- 3. FUNGSI UTAMA ---
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

def has_access(perm):
    user = st.session_state.get("user_name", "").lower()
    user_perms = st.session_state.user_permissions.get(user, ["Input"]) # Default hanya input
    return perm in user_perms

# --- 4. CSS CUSTOM (TETAP UTUH) ---
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
        "Waktu": waktu, "User": st.session_state.user_name.upper(),
        "Aksi": action, "Detail": details
    })

# --- 6. SIDEBAR ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

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
        
        # Filter menu berdasarkan hak akses
        menu_list = ["Dashboard Monitor", "📦 Inventory Spareparts"]
        if has_access("Export"): menu_list.append("Export & Reporting")
        if has_access("Security"): menu_list.append("Security Log")
        
        menu = st.selectbox("📂 MAIN MENU", menu_list)
        if st.button("🔒 LOGOUT", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

# --- 7. MENU LOGIC ---
if not st.session_state.logged_in:
    menu = "Quick Input Mode"

if menu == "Dashboard Monitor" and st.session_state.logged_in:
    st.markdown("## 📊 Monitoring Center")
    db = get_connection()
    df = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", db)
    db.close()

    # Injeksi Keterangan Virtual agar data tidak hilang
    df['Keterangan'] = df['id'].apply(lambda x: st.session_state.custom_keterangan.get(str(x), "-"))

    df_display = df.rename(columns={'nama_user': 'Nama Teknisi', 'masalah': 'Problem', 'waktu': 'Waktu Laporan'})
    
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
            if has_access("Input"):
                with st.form("form_quick_entry", clear_on_submit=True):
                    u_in = st.text_input("Nama Lengkap")
                    c_in = st.selectbox("Lokasi Cabang", st.secrets["master"]["daftar_cabang"])
                    i_in = st.text_area("Deskripsi Kendala")
                    p_in = st.select_slider("Urgensi", ["Low", "Medium", "High"])
                    if st.form_submit_button("KIRIM LAPORAN 🚀", use_container_width=True):
                        if u_in and i_in:
                            db = get_connection(); cur = db.cursor()
                            cur.execute("INSERT INTO tickets (nama_user, cabang, masalah, prioritas, status, waktu) VALUES (%s,%s,%s,%s,'Open',%s)", (u_in, c_in, i_in, p_in, get_wib_now().strftime('%Y-%m-%d %H:%M:%S')))
                            db.close(); add_log("INPUT", u_in); st.rerun()
            else: st.warning("Anda tidak punya akses Input.")

    with col_ctrl:
        with st.expander("🔄 Update Status & Keterangan", expanded=True):
            if has_access("Edit") and not df.empty:
                id_up = st.selectbox("Pilih ID Tiket", df['id'].tolist())
                current_ket = st.session_state.custom_keterangan.get(str(id_up), "")
                new_ket = st.text_input("Keterangan Hardware (SSD/RAM/dll)", value=current_ket)
                st_up = st.selectbox("Set Status Database", ["Open", "In Progress", "Solved", "Closed"])
                
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    if st.button("💾 SIMPAN SEMUA", use_container_width=True, type="primary"):
                        st.session_state.custom_keterangan[str(id_up)] = new_ket
                        save_data('keterangan_it.json', st.session_state.custom_keterangan)
                        db = get_connection(); cur = db.cursor()
                        cur.execute("UPDATE tickets SET status=%s WHERE id=%s", (st_up, id_up))
                        db.close(); add_log("UPDATE", f"ID #{id_up}"); st.rerun()
                
                with c_btn2:
                    if st.button("🗑️ HAPUS TIKET", use_container_width=True):
                        if has_access("Hapus"):
                            db = get_connection(); cur = db.cursor()
                            cur.execute("DELETE FROM tickets WHERE id=%s", (id_up,))
                            if str(id_up) in st.session_state.custom_keterangan: del st.session_state.custom_keterangan[str(id_up)]
                            save_data('keterangan_it.json', st.session_state.custom_keterangan)
                            db.close(); add_log("DELETE", f"ID #{id_up}"); st.rerun()
                        else: st.error("Akses Hapus Dibatasi")
            else: st.warning("Akses Edit Dibatasi.")

elif menu == "📦 Inventory Spareparts" and st.session_state.logged_in:
    try:
        from spareparts import show_sparepart_menu
        show_sparepart_menu(get_connection, get_wib_now, add_log)
    except Exception as e: st.error(f"Gagal memuat Spareparts: {e}")

elif menu == "Export & Reporting":
    st.markdown("## 📂 Export Data")
    db = get_connection()
    df_ex = pd.read_sql("SELECT * FROM tickets", db); db.close()
    # Tambah keterangan ke hasil export
    df_ex['Keterangan_IT'] = df_ex['id'].apply(lambda x: st.session_state.custom_keterangan.get(str(x), "-"))
    st.dataframe(df_ex, use_container_width=True)
    st.download_button("📥 DOWNLOAD CSV", df_ex.to_csv(index=False).encode('utf-8'), "IT_Report.csv")

elif menu == "Security Log":
    st.markdown("## 🛡️ User Access Control")
    target_user = st.selectbox("Atur Akses User:", list(st.secrets["auth"].keys()))
    current_perms = st.session_state.user_permissions.get(target_user.lower(), ["Input"])
    
    new_perms = st.multiselect("Izin Akses:", ["Input", "Edit", "Hapus", "Export", "Security"], default=current_perms)
    if st.button("Simpan Perizinan"):
        st.session_state.user_permissions[target_user.lower()] = new_perms
        save_data('permissions_it.json', st.session_state.user_permissions)
        st.success(f"Akses {target_user} diperbarui!")
    
    st.divider()
    st.markdown("### 📋 Audit Log")
    st.dataframe(pd.DataFrame(st.session_state.audit_logs), use_container_width=True)

elif menu == "Quick Input Mode":
    st.info("Silakan Login di Sidebar untuk akses penuh.")
