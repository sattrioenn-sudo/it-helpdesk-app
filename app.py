import streamlit as st
import pymysql
import pandas as pd
import certifi
import json
import os
from datetime import datetime, timedelta

# --- 1. KONFIGURASI ---
st.set_page_config(page_title="IT Support System - KCS", page_icon="🎫", layout="wide")

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

# --- 4. CSS UPGRADE (MINIMALIST & ANIMATED) ---
st.markdown("""
    <style>
    /* Reset & Clean Background */
    .stApp {
        background-color: #0e1117;
        color: #e0e0e0;
    }
    
    /* Typing Animation Effect */
    .typing-container {
        font-family: 'Courier New', Courier, monospace;
        display: inline-block;
    }
    
    .typing-text {
        overflow: hidden;
        border-right: .15em solid #60a5fa;
        white-space: nowrap;
        margin: 0 auto;
        letter-spacing: .10em;
        animation: 
            typing 3.5s steps(40, end),
            blink-caret .75s step-end infinite;
        font-size: 45px;
        font-weight: bold;
        color: #60a5fa;
    }

    @keyframes typing {
        from { width: 0 }
        to { width: 100% }
    }

    @keyframes blink-caret {
        from, to { border-color: transparent }
        50% { border-color: #60a5fa; }
    }

    /* Floating Simple Icon */
    .floating-icon {
        animation: float 3s ease-in-out infinite;
        font-size: 60px;
        margin-bottom: 20px;
        display: block;
    }

    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-15px); }
        100% { transform: translateY(0px); }
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: #0a0c10 !important;
        border-right: 1px solid #1e293b;
    }

    /* Minimalist Buttons */
    .stButton > button {
        width: 100% !important;
        border-radius: 5px;
        border: 1px solid #1e293b;
        background: transparent;
        color: #94a3b8;
        padding: 10px;
        transition: 0.3s;
        text-align: left;
    }
    
    .stButton > button:hover {
        border-color: #60a5fa;
        color: #ffffff;
        background: rgba(96, 165, 250, 0.05);
    }

    .clock-box {
        border: 1px solid #1e293b;
        border-radius: 10px;
        padding: 10px;
        text-align: center;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. SIDEBAR LOGIC ---
with st.sidebar:
    st.markdown("<h3 style='text-align: center; color: #60a5fa;'>IT-CONTROL</h3>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; font-size: 10px; color: #475569; margin-top:-15px;'>PT. KEMASAN CIPTATAMA SEMPURNA</p>", unsafe_allow_html=True)
    
    t_now = get_wib_now()
    st.markdown(f'''
    <div class="clock-box">
        <div style="font-family: monospace; color: white; font-size: 22px;">{t_now.strftime("%H:%M:%S")}</div>
        <div style="font-size: 10px; color: #475569;">{t_now.strftime("%d %b %Y")}</div>
    </div>
    ''', unsafe_allow_html=True)

    if st.session_state.get('logged_in'):
        u_name = st.session_state.user_name
        st.markdown(f"<p style='font-size: 11px; color: #475569;'>USER: <b style='color:#60a5fa;'>{u_name.upper()}</b></p>", unsafe_allow_html=True)
        
        if st.button("📊 Dashboard", use_container_width=True): st.session_state.current_menu = "📊 Dashboard"
        if has_access("Inventory") and st.button("📦 Inventory", use_container_width=True): st.session_state.current_menu = "📦 Inventory"
        if has_access("User Management") and st.button("👥 User Mgmt", use_container_width=True): st.session_state.current_menu = "👥 User Management"
        if has_access("Security") and st.button("🛡️ Security", use_container_width=True): st.session_state.current_menu = "🛡️ Security"
        
        st.markdown("---")
        if st.button("🔒 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
    else:
        u_in = st.text_input("User").lower()
        p_in = st.text_input("Pass", type="password")
        if st.button("🔓 LOGIN", use_container_width=True):
            if u_in in st.session_state.user_db and p_in == st.session_state.user_db[u_in][0]:
                st.session_state.logged_in, st.session_state.user_name = True, u_in
                st.rerun()

# --- 6. FULL SCREEN WELCOME UI (ANIMATED & MINIMALIST) ---
if not st.session_state.get('logged_in'):
    st.markdown(f"""
    <div style="height: 80vh; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;">
        <div class="floating-icon">🛡️</div>
        <div class="typing-container">
            <div class="typing-text">SYSTEM ACCESS AUTHORIZATION</div>
        </div>
        <div style="width: 50px; height: 2px; background: #60a5fa; margin: 20px 0;"></div>
        <p style="color: #475569; font-family: monospace; font-size: 14px; letter-spacing: 3px;">
            INTERNAL IT PORTAL | PT. KCS
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# --- 7. MAIN APP CONTENT ---
if st.session_state.current_menu == "📊 Dashboard":
    st.markdown("### 📊 Dashboard Monitor")
    db = get_connection()
    df_raw = pd.read_sql("SELECT * FROM tickets ORDER BY id ASC", db)
    try:
        df_stok = pd.read_sql("SELECT nama_part, kode_part, kategori, SUM(jumlah) as total FROM spareparts WHERE keterangan LIKE '%%[APPROVED]%%' GROUP BY nama_part, kode_part, kategori HAVING total > 0", db)
    except: df_stok = pd.DataFrame()
    db.close()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Tiket", len(df_raw))
    m2.metric("🔴 Open", len(df_raw[df_raw['status'] == 'Open']))
    m3.metric("🟡 In Progress", len(df_raw[df_raw['status'] == 'In Progress']))
    m4.metric("🟢 Solved", len(df_raw[df_raw['status'] == 'Solved']))

    st.markdown('<div style="padding: 10px; border-bottom: 1px solid #1e293b; margin-bottom: 20px;"></div>', unsafe_allow_html=True)
    
    c_f1, c_f2 = st.columns(2)
    d_start = c_f1.date_input("Filter Dari", value=datetime.now() - timedelta(days=30))
    d_end = c_f2.date_input("Filter Sampai", value=datetime.now())

    df_raw['tgl_saja'] = pd.to_datetime(df_raw['waktu']).dt.date
    df = df_raw[(df_raw['tgl_saja'] >= d_start) & (df_raw['tgl_saja'] <= d_end)].copy()
    df = df.reset_index(drop=True)
    df.insert(0, 'ID Ticket', range(1, len(df) + 1)) 
    df['Keterangan IT'] = df['id'].apply(lambda x: st.session_state.custom_keterangan.get(str(x), "-"))
    
    def color_status_only(val):
        c = {'Open': '#ff4b4b', 'In Progress': '#ffa500', 'Solved': '#00c853'}
        return f'color: {c.get(val, "white")}; font-weight: bold;'

    st.dataframe(df[['ID Ticket', 'nama_user', 'cabang', 'masalah', 'status', 'waktu', 'Keterangan IT']].style.map(color_status_only, subset=['status']), use_container_width=True, hide_index=True)

    if has_access("Export"):
        st.download_button("📥 DOWNLOAD REPORT CSV", df.to_csv(index=False).encode('utf-8'), "IT_Report.csv", use_container_width=True)

    c_a, c_b = st.columns(2)
    with c_a:
        if has_access("Input Tiket"):
            with st.expander("➕ Input Tiket Baru"):
                with st.form("new_tix"):
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
                        df_stok['opt'] = df_stok['nama_part'] + " | " + df_stok['kode_part']
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

elif st.session_state.current_menu == "👥 User Management":
    st.markdown("### 👥 User Access Management")
    user_options = list(st.session_state.user_db.keys())
    sel_user = st.selectbox("🔍 Pilih User", ["-- Tambah Baru --"] + user_options)
    v_pass, v_role, v_perms, is_edit = "", "", ["Dashboard"], False
    if sel_user != "-- Tambah Baru --":
        d = st.session_state.user_db[sel_user]; v_pass, v_role, v_perms, is_edit = d[0], d[1], d[2], True
    with st.form("u_form"):
        n_u = st.text_input("Username", value=sel_user if is_edit else "").lower()
        n_p, n_r = st.text_input("Password", value=v_pass), st.text_input("Role", value=v_role)
        perms = ["Dashboard", "Input Tiket", "Update Status", "Inventory", "Export", "User Management", "Security"]
        cols = st.columns(2)
        new_perms = [p for i, p in enumerate(perms) if cols[i%2].checkbox(p, value=p in v_perms)]
        if st.form_submit_button("Simpan"):
            st.session_state.user_db[n_u] = [n_p, n_r, new_perms]
            save_data('users_it.json', st.session_state.user_db); st.rerun()

elif st.session_state.current_menu == "🛡️ Security":
    st.markdown("### 🛡️ Security Audit Log")
    if st.session_state.security_logs:
        st.dataframe(pd.DataFrame(st.session_state.security_logs), use_container_width=True)

elif st.session_state.current_menu == "📦 Inventory":
    try:
        from spareparts import show_sparepart_menu
        show_sparepart_menu(get_connection, get_wib_now, lambda a, d: None)
    except: pass
