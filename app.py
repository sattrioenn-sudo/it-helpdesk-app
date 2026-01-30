import streamlit as st
import pymysql
import pandas as pd
import certifi
import json
import os
from datetime import datetime, timedelta

# --- 1. KONFIGURASI & THEME (SOLID DARK) ---
st.set_page_config(page_title="IT Support - KCS", page_icon="🎫", layout="wide")

# --- 2. STORAGE VIRTUAL ---
def load_data(file, default):
    if os.path.exists(file):
        try:
            with open(file, 'r') as f: return json.load(f)
        except: return default
    return default

def save_data(file, data):
    with open(file, 'w') as f: json.dump(data, f)

if 'custom_keterangan' not in st.session_state:
    st.session_state.custom_keterangan = load_data('keterangan_it.json', {})
if 'user_db' not in st.session_state:
    default_users = {"admin": ["kcs_2026", "Admin", ["Dashboard", "Input Tiket", "Update Status", "Inventory", "Export", "Security", "User Management", "Hapus Tiket"]]}
    st.session_state.user_db = load_data('users_it.json', default_users)
if 'security_logs' not in st.session_state:
    st.session_state.security_logs = load_data('security_logs.json', [])
if 'current_menu' not in st.session_state:
    st.session_state.current_menu = "📊 Dashboard"

# --- 3. FUNGSI UTAMA ---
def get_wib_now():
    return datetime.utcnow() + timedelta(hours=7)

def add_log(action, detail):
    log_entry = {
        "timestamp": get_wib_now().strftime('%Y-%m-%d %H:%M:%S'),
        "user": st.session_state.get("user_name", "SYSTEM"),
        "action": action,
        "detail": detail
    }
    st.session_state.security_logs.insert(0, log_entry)
    save_data('security_logs.json', st.session_state.security_logs[:500])

def get_connection():
    return pymysql.connect(
        host=st.secrets["tidb"]["host"], port=int(st.secrets["tidb"]["port"]),
        user=st.secrets["tidb"]["user"], password=st.secrets["tidb"]["password"],
        database=st.secrets["tidb"]["database"], autocommit=True, ssl={'ca': certifi.where()}
    )

def has_access(perm):
    user = st.session_state.get("user_name", "").lower()
    user_data = st.session_state.user_db.get(user, [None, None, ["Dashboard"]])
    return perm in user_data[2]

# --- 4. UI CSS (SOLID & PROFESSIONAL) ---
st.markdown("""
    <style>
    .stApp { background-color: #0f172a; color: #f8fafc; }
    [data-testid="stSidebar"] { background-color: #1e293b !important; border-right: 1px solid #334155; }
    [data-testid="stMetric"] { background: #1e293b; border: 1px solid #334155; padding: 20px; border-radius: 12px; }
    .stButton > button { width: 100% !important; border-radius: 8px; border: 1px solid #334155; background: #0f172a; color: #f8fafc; text-align: left; }
    .stButton > button:hover { border-color: #3b82f6; background: #1e293b; }
    .user-profile { background: #0f172a; padding: 15px; border-radius: 10px; border: 1px solid #334155; border-left: 5px solid #3b82f6; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.markdown("<h2 style='color: #3b82f6;'>IT TERMINAL</h2>", unsafe_allow_html=True)
    
    if st.session_state.get('logged_in'):
        u_name = st.session_state.user_name
        u_role = st.session_state.user_db.get(u_name, ["", "User"])[1]
        st.markdown(f'<div class="user-profile"><b>{u_name.upper()}</b><br><span style="color:#3b82f6; font-size:12px;">{u_role}</span></div>', unsafe_allow_html=True)
        
        if st.button("📊 DASHBOARD MONITOR"): st.session_state.current_menu = "📊 Dashboard"
        if has_access("Inventory") and st.button("📦 INVENTORY PARTS"): st.session_state.current_menu = "📦 Inventory"
        if has_access("User Management") and st.button("👥 MANAJEMEN USER"): st.session_state.current_menu = "👥 User Management"
        if has_access("Security") and st.button("🛡️ SECURITY LOG"): st.session_state.current_menu = "🛡️ Security"
        
        st.markdown("<br>"*5, unsafe_allow_html=True)
        if st.button("🔒 LOGOUT"):
            st.session_state.logged_in = False
            st.rerun()
    else:
        u_in = st.text_input("User")
        p_in = st.text_input("Pass", type="password")
        if st.button("LOGIN"):
            if u_in.lower() in st.session_state.user_db and p_in == st.session_state.user_db[u_in.lower()][0]:
                st.session_state.logged_in, st.session_state.user_name = True, u_in.lower()
                st.rerun()

if not st.session_state.get('logged_in'): st.stop()

# --- 6. MENU: DASHBOARD (FULL DATA) ---
if st.session_state.current_menu == "📊 Dashboard":
    st.subheader("📊 IT Operational Status")
    db = get_connection()
    df_raw = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", db)
    try:
        df_stok = pd.read_sql("SELECT nama_part, kode_part, kategori, SUM(jumlah) as total FROM spareparts WHERE keterangan LIKE '%%[APPROVED]%%' GROUP BY nama_part, kode_part, kategori HAVING total > 0", db)
    except: df_stok = pd.DataFrame()
    db.close()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Tiket", len(df_raw))
    m2.metric("Open", len(df_raw[df_raw['status'] == 'Open']))
    m3.metric("Process", len(df_raw[df_raw['status'] == 'In Progress']))
    m4.metric("Solved", len(df_raw[df_raw['status'] == 'Solved']))

    # Filter Luas agar data tidak hilang
    st.markdown("### Data Explorer")
    f1, f2 = st.columns(2)
    d_start = f1.date_input("Dari", value=datetime(2024, 1, 1))
    d_end = f2.date_input("Sampai", value=datetime.now() + timedelta(days=1))

    df_raw['tgl'] = pd.to_datetime(df_raw['waktu']).dt.date
    df = df_raw[(df_raw['tgl'] >= d_start) & (df_raw['tgl'] <= d_end)].copy()
    df['Note_IT'] = df['id'].apply(lambda x: st.session_state.custom_keterangan.get(str(x), "-"))

    st.dataframe(df[['id', 'nama_user', 'cabang', 'masalah', 'status', 'waktu', 'Note_IT']], use_container_width=True, hide_index=True)

    # Export & Forms
    if has_access("Export"):
        st.download_button("📥 DOWNLOAD CSV", df.to_csv(index=False).encode('utf-8'), "IT_Data.csv")

    c1, c2 = st.columns(2)
    with c1:
        if has_access("Input Tiket"):
            with st.expander("➕ TIKET BARU"):
                with st.form("f_new"):
                    un, cb = st.text_input("User"), st.selectbox("Cabang", st.secrets["master"]["daftar_cabang"])
                    ms = st.text_area("Masalah")
                    if st.form_submit_button("Kirim"):
                        db = get_connection(); cur = db.cursor()
                        cur.execute("INSERT INTO tickets (nama_user, cabang, masalah, status, waktu) VALUES (%s,%s,%s,'Open',%s)", (un, cb, ms, get_wib_now()))
                        db.close(); add_log("Create Ticket", f"User {un}"); st.rerun()
    with c2:
        if has_access("Update Status"):
            with st.expander("🛠️ UPDATE STATUS"):
                t_list = {f"#{row['id']} - {row['nama_user']}": row['id'] for _, row in df.iterrows()}
                if t_list:
                    sel = st.selectbox("Pilih Tiket", list(t_list.keys()))
                    n_st = st.selectbox("Status", ["Open", "In Progress", "Solved", "Closed"])
                    rem = st.text_input("Catatan")
                    if st.button("Update"):
                        db = get_connection(); cur = db.cursor()
                        cur.execute("UPDATE tickets SET status=%s WHERE id=%s", (n_st, t_list[sel]))
                        st.session_state.custom_keterangan[str(t_list[sel])] = rem
                        save_data('keterangan_it.json', st.session_state.custom_keterangan)
                        db.commit(); db.close(); add_log("Update Ticket", f"ID {t_list[sel]} to {n_st}"); st.rerun()

# --- 7. MENU: INVENTORY (MODUL PEMANGGIL) ---
elif st.session_state.current_menu == "📦 Inventory":
    st.subheader("📦 Inventory Spareparts Management")
    try:
        from spareparts import show_sparepart_menu
        show_sparepart_menu(get_connection, get_wib_now, add_log)
    except Exception as e:
        st.error(f"Gagal memuat modul inventory. Pastikan file spareparts.py ada. Error: {e}")

# --- 8. MENU: USER MANAGEMENT (LENGKAP) ---
elif st.session_state.current_menu == "👥 User Management":
    st.subheader("👥 User Access Control")
    user_list = list(st.session_state.user_db.keys())
    sel_u = st.selectbox("Pilih User", ["-- Tambah Baru --"] + user_list)
    
    is_edit = sel_u != "-- Tambah Baru --"
    v_p = st.session_state.user_db[sel_u][0] if is_edit else ""
    v_r = st.session_state.user_db[sel_u][1] if is_edit else ""
    v_m = st.session_state.user_db[sel_u][2] if is_edit else ["Dashboard"]

    with st.form("form_user"):
        new_u = st.text_input("Username", value=sel_u if is_edit else "").lower()
        new_p = st.text_input("Password", value=v_p)
        new_r = st.text_input("Role Name", value=v_r)
        
        perms = ["Dashboard", "Input Tiket", "Update Status", "Inventory", "Export", "User Management", "Security", "Hapus Tiket"]
        st.write("Hak Akses Menu:")
        cols = st.columns(3)
        final_perms = [p for i, p in enumerate(perms) if cols[i%3].checkbox(p, value=p in v_m)]
        
        if st.form_submit_button("Simpan User"):
            st.session_state.user_db[new_u] = [new_p, new_r, final_perms]
            save_data('users_it.json', st.session_state.user_db)
            add_log("User Management", f"Saved user {new_u}")
            st.success("User disimpan!"); st.rerun()

# --- 9. MENU: SECURITY LOG (LENGKAP) ---
elif st.session_state.current_menu == "🛡️ Security":
    st.subheader("🛡️ Security Activity Log")
    if st.session_state.security_logs:
        log_df = pd.DataFrame(st.session_state.security_logs)
        st.dataframe(log_df, use_container_width=True)
        if st.button("Clear Logs (Admin Only)"):
            if st.session_state.user_name == "admin":
                st.session_state.security_logs = []
                save_data('security_logs.json', [])
                st.rerun()
    else:
        st.info("Belum ada aktivitas tercatat.")
