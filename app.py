import streamlit as st
import pymysql
import pandas as pd
import certifi
import json
import os
from datetime import datetime, timedelta

# --- 1. KONFIGURASI & THEME ---
st.set_page_config(page_title="IT Kemasan Pro", page_icon="🎫", layout="wide")

# --- 2. STORAGE VIRTUAL ---
def load_data(file, default):
    if os.path.exists(file):
        try:
            with open(file, 'r') as f: return json.load(f)
        except: return default
    return default

def save_data(file, data):
    with open(file, 'w') as f: json.dump(data, f)

# Inisialisasi State
if 'custom_keterangan' not in st.session_state:
    st.session_state.custom_keterangan = load_data('keterangan_it.json', {})

if 'user_db' not in st.session_state:
    default_users = {"admin": ["kcs_2026", "Admin", ["Dashboard", "Input Tiket", "Update Status", "Inventory", "Export", "Security", "User Management", "Hapus Tiket"]]}
    st.session_state.user_db = load_data('users_it.json', default_users)

if 'solved_times' not in st.session_state:
    st.session_state.solved_times = load_data('solved_times.json', {})

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
    user_data = st.session_state.user_db.get(user, [None, None, ["Dashboard"]])
    return perm in user_data[2]

# --- 4. UI ENHANCEMENT ---
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at 50% 50%, #0f172a 0%, #020617 100%); }
    
    /* Tombol Navigasi Custom */
    .stButton > button {
        border-radius: 10px;
        transition: all 0.3s;
    }
    
    [data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 20px; border-radius: 20px;
    }

    div[data-testid="stDataFrame"] {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(96, 165, 250, 0.2);
        border-radius: 15px; padding: 10px;
    }

    .clock-inner {
        background: rgba(59, 130, 246, 0.1); 
        border-radius: 15px; padding: 10px; text-align: center;
        border: 1px solid rgba(59, 130, 246, 0.3); margin-bottom: 20px;
    }
    .digital-clock { font-family: 'JetBrains Mono', monospace; color: #60a5fa; font-size: 24px; font-weight: 800; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. LOGIC AUTH & SIDEBAR (BUTTON NAVIGATION) ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #60a5fa;'>🎫 IT-KEMASAN</h2>", unsafe_allow_html=True)
    wib = get_wib_now()
    st.markdown(f'''<div class="clock-inner"><div class="digital-clock">{wib.strftime("%H:%M:%S")}</div><div style="color: #94a3b8; font-size: 11px;">{wib.strftime("%A, %d %b %Y")}</div></div>''', unsafe_allow_html=True)

    if st.session_state.logged_in:
        u_name = st.session_state.get("user_name", "GUEST").upper()
        st.markdown(f"<p style='text-align: center;'>User: <b>{u_name}</b></p>", unsafe_allow_html=True)
        st.markdown("---")
        
        # MENU BUTTONS
        if st.button("📊 Dashboard Monitor", use_container_width=True): st.session_state.current_menu = "📊 Dashboard"
        
        if has_access("Inventory"):
            if st.button("📦 Inventory Spareparts", use_container_width=True): st.session_state.current_menu = "📦 Inventory"
            
        if has_access("User Management"):
            if st.button("👥 Manajemen User", use_container_width=True): st.session_state.current_menu = "👥 User Management"
            
        if has_access("Security"):
            if st.button("🛡️ Security Log", use_container_width=True): st.session_state.current_menu = "🛡️ Security"
            
        st.markdown("---")
        if st.button("🔒 LOGOUT", use_container_width=True):
            add_log("LOGOUT", f"User {u_name} keluar")
            st.session_state.logged_in = False
            st.rerun()
    else:
        u_in = st.text_input("Username").lower()
        p_in = st.text_input("Password", type="password")
        if st.button("🔓 LOGIN", use_container_width=True):
            if u_in in st.session_state.user_db and p_in == st.session_state.user_db[u_in][0]:
                st.session_state.logged_in = True
                st.session_state.user_name = u_in
                add_log("LOGIN", "Login sukses")
                st.rerun()
            else: st.error("Kredensial Salah")

if not st.session_state.logged_in:
    st.info("👋 Silakan login di sidebar.")
    st.stop()

# --- 6. MENU LOGIC ---
menu = st.session_state.current_menu

if menu == "📊 Dashboard":
    st.markdown("### 📊 IT Support Dashboard")
    db = get_connection()
    df = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", db)
    
    query_sp = "SELECT nama_part, kode_part, kategori, CAST(SUM(jumlah) AS SIGNED) as total FROM spareparts WHERE keterangan LIKE '%%[APPROVED]%%' GROUP BY nama_part, kode_part, kategori HAVING total > 0"
    df_stok = pd.read_sql(query_sp, db)
    db.close()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Tiket", len(df))
    m2.metric("🔴 Open", len(df[df['status'] == 'Open']))
    m3.metric("🟡 In Progress", len(df[df['status'] == 'In Progress']))
    m4.metric("🟢 Solved", len(df[df['status'] == 'Solved']))

    st.markdown("---")
    
    # REVISI ID TICKET: Ubah visual ID jadi urut 1, 2, 3...
    if not df.empty:
        # Kita buat kolom baru 'ID Ticket' yang isinya urutan terbalik (karena order by id DESC)
        df['ID Ticket'] = range(len(df), 0, -1)
    
    df['Waktu Input'] = pd.to_datetime(df['waktu']).dt.strftime('%d/%m/%Y %H:%M')
    df['Waktu Solved'] = df['id'].apply(lambda x: st.session_state.solved_times.get(str(x), "-"))
    df['Keterangan IT'] = df['id'].apply(lambda x: st.session_state.custom_keterangan.get(str(x), "-"))
    
    def color_status(val):
        color = '#94a3b8'
        if val == 'Open': color = '#ff4b4b'
        elif val == 'In Progress': color = '#ffa500'
        elif val == 'Solved': color = '#00c853'
        return f'color: {color}; font-weight: bold'

    # Menampilkan ID Ticket yang sudah urut di depan
    st.dataframe(
        df[['ID Ticket', 'nama_user', 'cabang', 'masalah', 'status', 'Waktu Input', 'Waktu Solved', 'Keterangan IT']]
        .style.applymap(color_status, subset=['status']),
        use_container_width=True, hide_index=True
    )

    if has_access("Export"):
        st.download_button("📥 DOWNLOAD CSV", df.to_csv(index=False).encode('utf-8'), "IT_Report.csv", use_container_width=True)

    col_a, col_b = st.columns([1, 1])
    with col_a:
        if has_access("Input Tiket"):
            with st.expander("➕ Input Tiket Baru"):
                with st.form("new_ticket", clear_on_submit=True):
                    up_in = st.text_input("Nama Pelapor")
                    cb_in = st.selectbox("Cabang", st.secrets["master"]["daftar_cabang"])
                    ms_in = st.text_area("Masalah")
                    if st.form_submit_button("Submit"):
                        if up_in and ms_in:
                            db = get_connection(); cur = db.cursor()
                            cur.execute("INSERT INTO tickets (nama_user, cabang, masalah, status, waktu) VALUES (%s,%s,%s,'Open',%s)", (up_in, cb_in, ms_in, get_wib_now().strftime('%Y-%m-%d %H:%M:%S')))
                            add_log("INPUT", f"Tiket dari {up_in}")
                            db.close(); st.rerun()

    with col_b:
        if has_access("Update Status"):
            with st.expander("🛠️ Update Status"):
                # Pilih berdasarkan ID asli (hidden) tapi tampilkan info user
                df['pilihan'] = df['id'].astype(str) + " - " + df['nama_user']
                id_sel_raw = st.selectbox("Pilih Tiket", df['pilihan'].tolist())
                id_sel = id_sel_raw.split(" - ")[0]
                
                st_sel = st.selectbox("Status", ["Open", "In Progress", "Solved", "Closed"])
                cat_it = st.text_input("Catatan IT", value=st.session_state.custom_keterangan.get(str(id_sel), ""))
                if st.button("Konfirmasi Update", use_container_width=True):
                    db = get_connection(); cur = db.cursor()
                    cur.execute("UPDATE tickets SET status=%s WHERE id=%s", (st_sel, id_sel))
                    if st_sel == "Solved":
                        st.session_state.solved_times[str(id_sel)] = get_wib_now().strftime('%d/%m/%Y %H:%M')
                    st.session_state.custom_keterangan[str(id_sel)] = cat_it
                    save_data('keterangan_it.json', st.session_state.custom_keterangan)
                    save_data('solved_times.json', st.session_state.solved_times)
                    add_log("UPDATE", f"Tiket ID {id_sel} -> {st_sel}")
                    db.commit(); db.close(); st.rerun()

elif menu == "👥 User Management":
    st.markdown("### 👥 User Management")
    user_options = list(st.session_state.user_db.keys())
    sel_user = st.selectbox("🔍 Pilih User", ["-- Tambah User Baru --"] + user_options)
    st.markdown("---")
    # ... (Logika form user management sama seperti sebelumnya)
    with st.form("user_mgmt"):
        n_u = st.text_input("Username", value=sel_user if sel_user != "-- Tambah User Baru --" else "")
        n_p = st.text_input("Password")
        if st.form_submit_button("Simpan User"):
            st.session_state.user_db[n_u] = [n_p, "Staff", ["Dashboard"]]
            save_data('users_it.json', st.session_state.user_db)
            st.success("User disimpan!")

elif menu == "🛡️ Security":
    st.markdown("### 🛡️ System Audit Log")
    if st.session_state.security_logs:
        st.dataframe(pd.DataFrame(st.session_state.security_logs), use_container_width=True, hide_index=True)
    else: st.write("Belum ada log.")

elif menu == "📦 Inventory":
    try:
        from spareparts import show_sparepart_menu
        show_sparepart_menu(get_connection, get_wib_now, lambda a, d: add_log(a, d))
    except: st.error("Modul Inventory tidak ditemukan.")
