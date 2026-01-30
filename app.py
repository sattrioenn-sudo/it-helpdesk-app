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
    [data-testid="stMetric"] { background: rgba(255, 255, 255, 0.03); border: 1px solid rgba(255, 255, 255, 0.1); padding: 20px; border-radius: 20px; backdrop-filter: blur(10px); }
    
    /* Tombol Seragam */
    .stButton > button { 
        width: 100% !important; 
        border-radius: 12px; 
        border: 1px solid rgba(96, 165, 250, 0.2); 
        background: rgba(255, 255, 255, 0.05); 
        color: #e2e8f0; 
        padding: 10px 20px; 
        transition: all 0.3s; 
        text-align: left; 
        margin-bottom: 5px; 
    }
    .stButton > button:hover { 
        background: rgba(96, 165, 250, 0.15); 
        border-color: #60a5fa; 
        color: #ffffff; 
        box-shadow: 0 0 15px rgba(96, 165, 250, 0.3); 
        transform: translateX(5px); 
    }
    
    div[data-testid="stDataFrame"] { background: rgba(30, 41, 59, 0.4); border: 1px solid rgba(96, 165, 250, 0.2); border-radius: 15px; padding: 10px; }
    .user-profile { background: rgba(255, 255, 255, 0.05); padding: 12px; border-radius: 12px; border-left: 4px solid #60a5fa; margin-bottom: 20px; }
    .filter-section { background: rgba(255, 255, 255, 0.02); padding: 15px; border-radius: 15px; border: 1px dashed rgba(96, 165, 250, 0.3); margin: 15px 0; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. LOGIC SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #60a5fa; margin-bottom: 0;'>🎫 IT-KEMASAN</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 11px; color: #94a3b8; margin-bottom: 20px;'>PT. Kemasan Ciptatama Sempurna</p>", unsafe_allow_html=True)
    
    if st.session_state.get('logged_in'):
        u_name = st.session_state.user_name
        u_role = st.session_state.user_db.get(u_name, ["", "User"])[1]
        st.markdown(f'''<div class="user-profile"><div style="font-size: 12px; color: #94a3b8;">Active User</div><div style="font-weight: bold;">{u_name.upper()}</div><div style="font-size: 11px; color: #60a5fa;">🛡️ {u_role}</div></div>''', unsafe_allow_html=True)
        
        # Semua tombol pakai use_container_width agar seragam
        if st.button("📊 Dashboard Monitor", use_container_width=True): 
            st.session_state.current_menu = "📊 Dashboard"
        
        if has_access("Inventory"):
            if st.button("📦 Inventory Spareparts", use_container_width=True): 
                st.session_state.current_menu = "📦 Inventory"
        
        if has_access("User Management"):
            if st.button("👥 Manajemen User", use_container_width=True): 
                st.session_state.current_menu = "👥 User Management"
        
        if has_access("Security"):
            if st.button("🛡️ Security Log", use_container_width=True): 
                st.session_state.current_menu = "🛡️ Security"
        
        st.markdown("---")
        if st.button("🔒 Logout System", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
    else:
        u_in = st.text_input("Username").lower()
        p_in = st.text_input("Password", type="password")
        if st.button("🔓 LOGIN", use_container_width=True):
            if u_in in st.session_state.user_db and p_in == st.session_state.user_db[u_in][0]:
                st.session_state.logged_in, st.session_state.user_name = True, u_in
                st.rerun()

if not st.session_state.get('logged_in'): st.stop()

# --- 6. MENU: DASHBOARD ---
if st.session_state.current_menu == "📊 Dashboard":
    st.markdown("### 📊 IT Support Dashboard")
    db = get_connection()
    df_raw = pd.read_sql("SELECT * FROM tickets ORDER BY id ASC", db)
    df_stok = pd.read_sql("SELECT nama_part, kode_part, kategori, SUM(jumlah) as total FROM spareparts WHERE keterangan LIKE '%%[APPROVED]%%' GROUP BY nama_part, kode_part, kategori HAVING total > 0", db)
    db.close()

    # Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Tiket", len(df_raw))
    m2.metric("🔴 Open", len(df_raw[df_raw['status'] == 'Open']))
    m3.metric("🟡 In Progress", len(df_raw[df_raw['status'] == 'In Progress']))
    m4.metric("🟢 Solved", len(df_raw[df_raw['status'] == 'Solved']))

    # Filter Box
    st.markdown('<div class="filter-section">', unsafe_allow_html=True)
    c_f1, c_f2 = st.columns(2)
    d_start = c_f1.date_input("Filter Dari", value=datetime.now() - timedelta(days=30))
    d_end = c_f2.date_input("Filter Sampai", value=datetime.now())
    st.markdown('</div>', unsafe_allow_html=True)

    df_raw['tgl_saja'] = pd.to_datetime(df_raw['waktu']).dt.date
    df = df_raw[(df_raw['tgl_saja'] >= d_start) & (df_raw['tgl_saja'] <= d_end)].copy()

    df = df.reset_index(drop=True)
    df.insert(0, 'ID Ticket', range(1, len(df) + 1)) 
    df['Keterangan IT'] = df['id'].apply(lambda x: st.session_state.custom_keterangan.get(str(x), "-"))
    
    def color_status_only(val):
        colors = {'Open': '#ff4b4b', 'In Progress': '#ffa500', 'Solved': '#00c853'}
        return f'color: {colors.get(val, "white")}; font-weight: bold;'

    st.dataframe(df[['ID Ticket', 'nama_user', 'cabang', 'masalah', 'status', 'waktu', 'Keterangan IT']].style.map(color_status_only, subset=['status']), use_container_width=True, hide_index=True)
    
    if has_access("Export"):
        st.download_button("📥 DOWNLOAD CSV", df.to_csv(index=False).encode('utf-8'), "IT_Report.csv", use_container_width=True)

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
                    
                    pakai_sp = st.checkbox("Gunakan Sparepart?")
                    sp_data, qty = None, 0
                    if pakai_sp and not df_stok.empty:
                        df_stok['opt'] = df_stok['nama_part'] + " | S/N: " + df_stok['kode_part']
                        pilih_sp = st.selectbox("Pilih Barang", df_stok['opt'].tolist())
                        sp_data = df_stok[df_stok['opt'] == pilih_sp].iloc[0]
                        qty = st.number_input(f"Jumlah (Stok: {int(sp_data['total'])})", 1, int(sp_data['total']), 1)
                    
                    cat_it = st.text_input("Catatan IT", value=st.session_state.custom_keterangan.get(str(sel_id), ""))
                    if st.button("Simpan Update", use_container_width=True):
                        db = get_connection(); cur = db.cursor()
                        cur.execute("UPDATE tickets SET status=%s WHERE id=%s", (new_st, sel_id))
                        final_ket = cat_it
                        if pakai_sp and sp_data is not None:
                            final_ket += f" [Ganti: {sp_data['nama_part']} x{qty}]"
                            cur.execute("INSERT INTO spareparts (nama_part, kode_part, kategori, jumlah, keterangan, waktu) VALUES (%s,%s,%s,%s,%s,%s)", (sp_data['nama_part'], sp_data['kode_part'], sp_data['kategori'], -qty, f"[APPROVED] Tiket #{sel_id}", get_wib_now()))
                        st.session_state.custom_keterangan[str(sel_id)] = final_ket
                        save_data('keterangan_it.json', st.session_state.custom_keterangan)
                        db.commit(); db.close(); st.rerun()

# --- 7. MENU: USER MANAGEMENT ---
elif st.session_state.current_menu == "👥 User Management":
    st.markdown("### 👥 User Access Management")
    user_options = list(st.session_state.user_db.keys())
    sel_user = st.selectbox("🔍 Pilih User", ["-- Tambah User Baru --"] + user_options)
    v_pass, v_role, v_perms, is_edit = "", "", ["Dashboard"], False
    if sel_user != "-- Tambah User Baru --":
        d = st.session_state.user_db[sel_user]
        v_pass, v_role, v_perms, is_edit = d[0], d[1], d[2], True

    with st.form("user_form"):
        n_u = st.text_input("Username", value=sel_user if is_edit else "", disabled=is_edit).lower()
        n_p, n_r = st.text_input("Password", value=v_pass), st.text_input("Role", value=v_role)
        st.write("Izin Akses:")
        c1, c2 = st.columns(2)
        i1, i2, i3 = c1.checkbox("Dashboard", value="Dashboard" in v_perms), c1.checkbox("Input Tiket", value="Input Tiket" in v_perms), c1.checkbox("Update Status", value="Update Status" in v_perms)
        i4, i5, i6, i7 = c2.checkbox("Inventory", value="Inventory" in v_perms), c2.checkbox("Export", value="Export" in v_perms), c2.checkbox("User Management", value="User Management" in v_perms), c2.checkbox("Security", value="Security" in v_perms)
        
        if st.form_submit_button("Simpan User", use_container_width=True):
            new_perms = [p for p, val in zip(["Dashboard", "Input Tiket", "Update Status", "Inventory", "Export", "User Management", "Security"], [i1, i2, i3, i4, i5, i6, i7]) if val]
            st.session_state.user_db[n_u] = [n_p, n_r, new_perms]
            save_data('users_it.json', st.session_state.user_db)
            st.rerun()

elif st.session_state.current_menu == "🛡️ Security":
    st.markdown("### 🛡️ Security Audit Log")
    st.dataframe(pd.DataFrame(st.session_state.security_logs), use_container_width=True)

elif st.session_state.current_menu == "📦 Inventory":
    try:
        from spareparts import show_sparepart_menu
        show_sparepart_menu(get_connection, get_wib_now, lambda a, d: add_log(a, d))
    except: st.error("Data Sudah Terhapus!.")
