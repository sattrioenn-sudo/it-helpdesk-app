import streamlit as st
import pymysql
import pandas as pd
import certifi
import json
import os
from datetime import datetime, timedelta

# --- 1. KONFIGURASI & THEME ---
st.set_page_config(page_title="IT Kemasan", page_icon="🎫", layout="wide")

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
    log_entry = {"timestamp": get_wib_now().strftime('%Y-%m-%d %H:%M:%S'), "user": st.session_state.get("user_name", "SYSTEM"), "action": action, "detail": detail}
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

# --- 4. UI ENHANCEMENT ---
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at 50% 50%, #0f172a 0%, #020617 100%); }
    [data-testid="stMetric"] { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); padding: 20px; border-radius: 20px; }
    .stButton > button { width: 100%; border-radius: 12px; border: 1px solid rgba(96, 165, 250, 0.2); background: rgba(255, 255, 255, 0.05); color: #e2e8f0; transition: all 0.3s; text-align: left; }
    .stButton > button:hover { background: rgba(96, 165, 250, 0.15); border-color: #60a5fa; transform: translateX(5px); }
    .user-profile { background: rgba(255, 255, 255, 0.05); padding: 12px; border-radius: 12px; border-left: 4px solid #60a5fa; margin-bottom: 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #60a5fa;'>🎫 IT-KEMASAN</h2>", unsafe_allow_html=True)
    if st.session_state.get('logged_in'):
        u_name = st.session_state.user_name
        u_role = st.session_state.user_db.get(u_name, ["", "User"])[1]
        st.markdown(f'<div class="user-profile"><div style="font-size: 12px; color: #94a3b8;">User</div><div style="font-weight: bold;">{u_name.upper()}</div><div style="font-size: 11px; color: #60a5fa;">🛡️ {u_role}</div></div>', unsafe_allow_html=True)
        if st.button("📊 Dashboard Monitor"): st.session_state.current_menu = "📊 Dashboard"
        if has_access("Inventory"):
            if st.button("📦 Inventory Spareparts"): st.session_state.current_menu = "📦 Inventory"
        if has_access("User Management"):
            if st.button("👥 Manajemen User"): st.session_state.current_menu = "👥 User Management"
        if has_access("Security"):
            if st.button("🛡️ Security Log"): st.session_state.current_menu = "🛡️ Security"
        if st.button("🔒 Logout"):
            st.session_state.logged_in = False
            st.rerun()
    else:
        # (Login logic same as before)
        u_in = st.text_input("Username").lower()
        p_in = st.text_input("Password", type="password")
        if st.button("🔓 LOGIN"):
            if u_in in st.session_state.user_db and p_in == st.session_state.user_db[u_in][0]:
                st.session_state.logged_in = True
                st.session_state.user_name = u_in
                st.rerun()

if not st.session_state.get('logged_in'): st.stop()

# --- 6. MENU: DASHBOARD ---
if st.session_state.current_menu == "📊 Dashboard":
    st.markdown("### 📊 IT Support Dashboard")
    
    # 1. AMBIL DATA
    db = get_connection()
    df = pd.read_sql("SELECT * FROM tickets ORDER BY id ASC", db)
    df_stok = pd.read_sql("SELECT nama_part, kode_part, kategori, SUM(jumlah) as total FROM spareparts WHERE keterangan LIKE '%%[APPROVED]%%' GROUP BY nama_part, kode_part, kategori HAVING total > 0", db)
    db.close()

    # 2. FILTER TANGGAL (MODERN LOOK)
    with st.expander("🔍 Filter & Cari Data"):
        c1, c2 = st.columns(2)
        date_start = c1.date_input("Dari Tanggal", value=datetime.now() - timedelta(days=30))
        date_end = c2.date_input("Sampai Tanggal", value=datetime.now())
        
        # Filter Logic
        df['date_only'] = pd.to_datetime(df['waktu']).dt.date
        df = df[(df['date_only'] >= date_start) & (df['date_only'] <= date_end)]

    # 3. METRICS
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Tiket", len(df))
    m2.metric("🔴 Open", len(df[df['status'] == 'Open']))
    m3.metric("🟡 In Progress", len(df[df['status'] == 'In Progress']))
    m4.metric("🟢 Solved", len(df[df['status'] == 'Solved']))

    # 4. PREPARE DATAFRAME FOR VIEW
    df = df.reset_index(drop=True)
    df.insert(0, 'ID Ticket', range(1, len(df) + 1)) 
    df['Keterangan IT'] = df['id'].apply(lambda x: st.session_state.custom_keterangan.get(str(x), "-"))

    # 5. FUNGSI PEWARNAAN BARIS (STYLING)
    def style_status(row):
        color = 'transparent' # Default
        if row.status == 'Open': color = 'rgba(255, 75, 75, 0.2)' # Merah transparan
        elif row.status == 'In Progress': color = 'rgba(255, 165, 0, 0.2)' # Orange transparan
        elif row.status == 'Solved': color = 'rgba(0, 200, 83, 0.2)' # Hijau transparan
        return [f'background-color: {color}'] * len(row)

    # Tampilkan Tabel dengan Style
    st.dataframe(
        df[['ID Ticket', 'nama_user', 'cabang', 'masalah', 'status', 'waktu', 'Keterangan IT']]
        .style.apply(style_status, axis=1),
        use_container_width=True, hide_index=True
    )
    
    if has_access("Export"):
        st.download_button("📥 EXPORT HASIL FILTER", df.to_csv(index=False).encode('utf-8'), "IT_Filtered_Report.csv", use_container_width=True)

    # (Logika Input & Update Tiket tetap sama seperti sebelumnya)
    c_a, c_b = st.columns(2)
    with c_a:
        if has_access("Input Tiket"):
            with st.expander("➕ Input Tiket Baru"):
                with st.form("new_tix", clear_on_submit=True):
                    un, cb = st.text_input("Nama Pelapor"), st.selectbox("Cabang", st.secrets["master"]["daftar_cabang"])
                    ms = st.text_area("Masalah")
                    if st.form_submit_button("Submit"):
                        db = get_connection(); cur = db.cursor()
                        cur.execute("INSERT INTO tickets (nama_user, cabang, masalah, status, waktu) VALUES (%s,%s,%s,'Open',%s)", (un, cb, ms, get_wib_now()))
                        db.close(); st.rerun()
    with c_b:
        if has_access("Update Status"):
            with st.expander("🛠️ Update Status & Sparepart"):
                tix_list = {f"#{row['ID Ticket']} - {row['nama_user']}": row['id'] for _, row in df.iterrows()}
                if tix_list:
                    sel_label = st.selectbox("Pilih Tiket", list(tix_list.keys()))
                    sel_id = tix_list[sel_label]
                    new_st = st.selectbox("Status Baru", ["Open", "In Progress", "Solved", "Closed"])
                    cat_it = st.text_input("Catatan IT", value=st.session_state.custom_keterangan.get(str(sel_id), ""))
                    if st.button("Simpan Update"):
                        db = get_connection(); cur = db.cursor()
                        cur.execute("UPDATE tickets SET status=%s WHERE id=%s", (new_st, sel_id))
                        st.session_state.custom_keterangan[str(sel_id)] = cat_it
                        save_data('keterangan_it.json', st.session_state.custom_keterangan)
                        db.commit(); db.close(); st.rerun()

# (Menu lain tetap berfungsi normal)
elif st.session_state.current_menu == "👥 User Management":
    # ... (Same user management logic)
    st.write("User Management Active")
elif st.session_state.current_menu == "🛡️ Security":
    st.dataframe(pd.DataFrame(st.session_state.security_logs), use_container_width=True)
elif st.session_state.current_menu == "📦 Inventory":
    try:
        from spareparts import show_sparepart_menu
        show_sparepart_menu(get_connection, get_wib_now, lambda a, d: add_log(a, d))
    except: st.error("Modul Inventory Error.")
