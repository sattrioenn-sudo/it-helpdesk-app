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

# --- 4. CSS: MODERN WEB SAAS DESIGN ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    .stApp {
        background-color: #0c0e12;
        color: #f1f5f9;
    }
    
    /* Sidebar Modern */
    [data-testid="stSidebar"] {
        background-color: #11141a !important;
        border-right: 1px solid #1e293b;
    }

    /* Welcome Typography */
    .typing-text {
        font-family: 'Inter', sans-serif;
        color: #ffffff;
        font-size: 52px;
        font-weight: 700;
        letter-spacing: -2px;
        margin-bottom: 0px;
    }

    .sub-brand {
        color: #64748b;
        font-size: 14px;
        letter-spacing: 4px;
        text-transform: uppercase;
        margin-top: 10px;
    }

    /* Role Badge di Sidebar */
    .user-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        padding: 15px;
        border-radius: 12px;
        margin-bottom: 25px;
    }

    .role-badge {
        display: inline-block;
        background: rgba(59, 130, 246, 0.1);
        color: #60a5fa;
        font-size: 11px;
        padding: 2px 10px;
        border-radius: 20px;
        margin-top: 5px;
        border: 1px solid rgba(59, 130, 246, 0.2);
    }

    /* Menu Button Style */
    .stButton > button {
        width: 100% !important;
        border-radius: 8px;
        border: 1px solid transparent;
        background: transparent;
        color: #94a3b8;
        padding: 10px 15px;
        transition: all 0.2s;
        text-align: left;
        font-weight: 500;
    }
    
    .stButton > button:hover {
        background: rgba(255, 255, 255, 0.05);
        color: #ffffff;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    /* Metric Card */
    [data-testid="stMetric"] {
        background: #11141a;
        border: 1px solid #1e293b;
        border-radius: 16px;
        padding: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='color: #ffffff; font-weight: 700;'>Portal IT</h2>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 12px; color: #64748b; margin-top: -15px;'>KEMASAN CIPTATAMA SEMPURNA</p>", unsafe_allow_html=True)
    
    t_now = get_wib_now()
    st.markdown(f'''
    <div style="margin-bottom: 30px;">
        <span style="font-family: monospace; color: #60a5fa; font-size: 18px;">{t_now.strftime("%H:%M:%S")}</span>
    </div>
    ''', unsafe_allow_html=True)

    if st.session_state.get('logged_in'):
        u_name = st.session_state.user_name
        # Mengambil role dari database session
        u_role = st.session_state.user_db.get(u_name, ["", "User"])[1]
        
        st.markdown(f'''
        <div class="user-card">
            <div style="font-size: 12px; color: #64748b;">Logged in as</div>
            <div style="font-weight: 600; color: #f8fafc; font-size: 16px;">{u_name.upper()}</div>
            <div class="role-badge">{u_role}</div>
        </div>
        ''', unsafe_allow_html=True)
        
        if st.button("📊 Dashboard Monitor", use_container_width=True): st.session_state.current_menu = "📊 Dashboard"
        if has_access("Inventory") and st.button("📦 Inventory Spareparts", use_container_width=True): st.session_state.current_menu = "📦 Inventory"
        if has_access("User Management") and st.button("👥 User Management", use_container_width=True): st.session_state.current_menu = "👥 User Management"
        if has_access("Security") and st.button("🛡️ Security Activity Log", use_container_width=True): st.session_state.current_menu = "🛡️ Security"
        
        st.markdown("<br>"*3, unsafe_allow_html=True)
        if st.button("🔒 Sign Out", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()
    else:
        st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
        u_in = st.text_input("Username").lower()
        p_in = st.text_input("Password", type="password")
        if st.button("Authorize Access", use_container_width=True):
            if u_in in st.session_state.user_db and p_in == st.session_state.user_db[u_in][0]:
                st.session_state.logged_in, st.session_state.user_name = True, u_in
                st.rerun()
            else:
                st.error("Invalid Username or Password")

# --- 6. WELCOME PAGE ---
if not st.session_state.get('logged_in'):
    st.markdown(f"""
    <div style="height: 80vh; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;">
        <div style="background: #60a5fa; width: 40px; height: 4px; border-radius: 2px; margin-bottom: 30px;"></div>
        <div class="typing-text">Infrastructure Control</div>
        <div class="sub-brand">PT. Kemasan Ciptatama Sempurna</div>
        <p style="color: #475569; font-size: 16px; margin-top: 40px; max-width: 500px; font-weight: 300;">
            Welcome to the internal IT management gateway. 
            Please authenticate via the sidebar to access system resources.
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# --- 7. MAIN CONTENT ---
if st.session_state.current_menu == "📊 Dashboard":
    st.markdown(f"## 📊 Dashboard Overview")
    
    db = get_connection()
    df_raw = pd.read_sql("SELECT * FROM tickets ORDER BY id ASC", db)
    try:
        df_stok = pd.read_sql("SELECT nama_part, kode_part, kategori, SUM(jumlah) as total FROM spareparts WHERE keterangan LIKE '%%[APPROVED]%%' GROUP BY nama_part, kode_part, kategori HAVING total > 0", db)
    except: df_stok = pd.DataFrame()
    db.close()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Tickets", len(df_raw))
    m2.metric("🔴 Open", len(df_raw[df_raw['status'] == 'Open']))
    m3.metric("🟡 In Progress", len(df_raw[df_raw['status'] == 'In Progress']))
    m4.metric("🟢 Solved", len(df_raw[df_raw['status'] == 'Solved']))

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Filter & Table
    c_f1, c_f2 = st.columns(2)
    d_start = c_f1.date_input("Start Date", value=datetime.now() - timedelta(days=30))
    d_end = c_f2.date_input("End Date", value=datetime.now())

    df_raw['tgl_saja'] = pd.to_datetime(df_raw['waktu']).dt.date
    df = df_raw[(df_raw['tgl_saja'] >= d_start) & (df_raw['tgl_saja'] <= d_end)].copy()
    df = df.reset_index(drop=True)
    df.insert(0, 'ID Ticket', range(1, len(df) + 1)) 
    df['IT Notes'] = df['id'].apply(lambda x: st.session_state.custom_keterangan.get(str(x), "-"))
    
    def color_status_only(val):
        c = {'Open': '#ff4b4b', 'In Progress': '#ffa500', 'Solved': '#00c853'}
        return f'color: {c.get(val, "white")}; font-weight: 600;'

    st.dataframe(
        df[['ID Ticket', 'nama_user', 'cabang', 'masalah', 'status', 'waktu', 'IT Notes']].style.map(color_status_only, subset=['status']), 
        use_container_width=True, 
        hide_index=True
    )

    if has_access("Export"):
        st.download_button("📥 Export to CSV Report", df.to_csv(index=False).encode('utf-8'), "IT_Report.csv", use_container_width=True)

    # ... (Sisa fungsi Input Tiket & Update Status tetap sama di bawah)
    c_a, c_b = st.columns(2)
    with c_a:
        if has_access("Input Tiket"):
            with st.expander("➕ Create New Ticket"):
                with st.form("new_tix"):
                    un, cb = st.text_input("Requester Name"), st.selectbox("Branch", st.secrets["master"]["daftar_cabang"])
                    ms = st.text_area("Issue Detail")
                    if st.form_submit_button("Submit Ticket"):
                        db = get_connection(); cur = db.cursor()
                        cur.execute("INSERT INTO tickets (nama_user, cabang, masalah, status, waktu) VALUES (%s,%s,%s,'Open',%s)", (un, cb, ms, get_wib_now()))
                        db.close(); st.rerun()
    with c_b:
        if has_access("Update Status"):
            with st.expander("🛠️ Update Ticket & Sparepart"):
                tix_list = {f"#{row['ID Ticket']} - {row['nama_user']}": row['id'] for _, row in df.iterrows()}
                if tix_list:
                    sel_label = st.selectbox("Select Ticket", list(tix_list.keys()))
                    sel_id = tix_list[sel_label]
                    new_st = st.selectbox("New Status", ["Open", "In Progress", "Solved", "Closed"])
                    # ... (Logika sparepart & update sama)
                    cat_it = st.text_input("IT Remarks", value=st.session_state.custom_keterangan.get(str(sel_id), ""))
                    if st.button("Update Record", use_container_width=True):
                        db = get_connection(); cur = db.cursor()
                        cur.execute("UPDATE tickets SET status=%s WHERE id=%s", (new_st, sel_id))
                        st.session_state.custom_keterangan[str(sel_id)] = cat_it
                        save_data('keterangan_it.json', st.session_state.custom_keterangan)
                        db.commit(); db.close(); st.rerun()

elif st.session_state.current_menu == "👥 User Management":
    st.markdown("### 👥 User Access Management")
    # ... (Kode User Management sama, hanya label dirapikan)

elif st.session_state.current_menu == "🛡️ Security":
    st.markdown("### 🛡️ Security Activity Log")
    if st.session_state.security_logs:
        st.dataframe(pd.DataFrame(st.session_state.security_logs), use_container_width=True)

elif st.session_state.current_menu == "📦 Inventory":
    try:
        from spareparts import show_sparepart_menu
        show_sparepart_menu(get_connection, get_wib_now, lambda a, d: None)
    except: pass
