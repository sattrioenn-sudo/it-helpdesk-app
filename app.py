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

# --- 4. CSS: PROFESSIONAL ENGINEERING DESIGN (STATIC) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    .stApp {
        background-color: #0b0e14;
        color: #cfd8e3;
    }
    
    /* Sidebar Engineering Style */
    [data-testid="stSidebar"] {
        background-color: #0f121a !important;
        border-right: 1px solid #232936;
    }

    /* Professional Title */
    .brand-title {
        font-size: 24px;
        font-weight: 700;
        color: #ffffff;
        letter-spacing: -0.5px;
        margin-bottom: 0px;
    }
    
    .brand-sub {
        font-size: 10px;
        color: #5c6b89;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-bottom: 20px;
    }

    /* Metric Cards - Clean & Bordered */
    div[data-testid="stMetric"] {
        background-color: #141820;
        border: 1px solid #232936;
        border-radius: 10px;
        padding: 15px;
    }

    /* Clean Sidebar Buttons */
    .stButton > button {
        width: 100% !important;
        border-radius: 6px;
        border: 1px solid transparent;
        background: transparent;
        color: #8a99af;
        padding: 8px 12px;
        transition: all 0.2s;
        text-align: left;
        font-size: 14px;
    }
    
    .stButton > button:hover {
        background: #1c222d;
        color: #ffffff;
        border: 1px solid #323a49;
    }

    /* User Profile Card */
    .user-profile {
        background: #141820;
        border: 1px solid #232936;
        padding: 12px;
        border-radius: 8px;
        margin-bottom: 20px;
    }

    /* Status Label Styling */
    .status-badge {
        padding: 2px 8px;
        border-radius: 4px;
        font-size: 12px;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. SIDEBAR ---
with st.sidebar:
    st.markdown('<p class="brand-title">KCS <span style="color:#3b82f6">INFRA</span></p>', unsafe_allow_html=True)
    st.markdown('<p class="brand-sub">IT Support Terminal</p>', unsafe_allow_html=True)

    if st.session_state.get('logged_in'):
        u_name = st.session_state.user_name
        u_role = st.session_state.user_db.get(u_name, ["", "User"])[1]
        
        st.markdown(f'''
        <div class="user-profile">
            <div style="font-size: 10px; color: #5c6b89;">OPERATOR ACTIVE</div>
            <div style="font-weight: 600; color: #ffffff; font-size: 15px;">{u_name.upper()}</div>
            <div style="font-size: 11px; color: #3b82f6; margin-top: 2px;">{u_role}</div>
        </div>
        ''', unsafe_allow_html=True)
        
        # Menu Navigation
        if st.button("📊  DASHBOARD MONITOR"): st.session_state.current_menu = "📊 Dashboard"
        if has_access("Inventory") and st.button("📦  INVENTORY PARTS"): st.session_state.current_menu = "📦 Inventory"
        if has_access("User Management") and st.button("👥  USER MANAGEMENT"): st.session_state.current_menu = "👥 User Management"
        if has_access("Security") and st.button("🛡️  SECURITY LOGS"): st.session_state.current_menu = "🛡️ Security"
        
        st.markdown("<br>"*4, unsafe_allow_html=True)
        if st.button("🔒  TERMINATE SESSION"):
            st.session_state.logged_in = False
            st.rerun()
    else:
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        u_in = st.text_input("Username").lower()
        p_in = st.text_input("Password", type="password")
        if st.button("AUTHORIZE ACCESS"):
            if u_in in st.session_state.user_db and p_in == st.session_state.user_db[u_in][0]:
                st.session_state.logged_in, st.session_state.user_name = True, u_in
                st.rerun()
            else: st.error("Access Refused")

# --- 6. WELCOME PAGE ---
if not st.session_state.get('logged_in'):
    st.markdown(f"""
    <div style="height: 70vh; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;">
        <h1 style="font-size: 48px; font-weight: 800; color: #ffffff; letter-spacing: -2px;">System Locked</h1>
        <p style="color: #5c6b89; font-size: 16px; margin-top: 10px;">Please authenticate via the terminal to access IT resources.</p>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

# --- 7. MAIN CONTENT ---
if st.session_state.current_menu == "📊 Dashboard":
    st.markdown("<h2 style='font-weight: 700; color: white;'>Dashboard Overview</h2>", unsafe_allow_html=True)
    
    db = get_connection()
    df_raw = pd.read_sql("SELECT * FROM tickets ORDER BY id ASC", db)
    db.close()

    # Metrics Row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Tickets", len(df_raw))
    m2.metric("Open Issue", len(df_raw[df_raw['status'] == 'Open']))
    m3.metric("Processing", len(df_raw[df_raw['status'] == 'In Progress']))
    m4.metric("Completed", len(df_raw[df_raw['status'] == 'Solved']))

    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    
    # Filter Section - DISET DEFAULT LUAS SUPAYA DATA TIDAK HILANG
    st.markdown("### Data Explorer")
    c_f1, c_f2 = st.columns(2)
    # Default mulai dari tahun 2020 supaya data lama tetap muncul
    d_start = c_f1.date_input("Filter Date From", value=datetime(2020, 1, 1))
    d_end = c_f2.date_input("Filter Date To", value=datetime.now())

    df_raw['tgl_saja'] = pd.to_datetime(df_raw['waktu']).dt.date
    df = df_raw[(df_raw['tgl_saja'] >= d_start) & (df_raw['tgl_saja'] <= d_end)].copy()
    df = df.reset_index(drop=True)
    df.insert(0, 'ID Ticket', range(1, len(df) + 1)) 
    df['IT Notes'] = df['id'].apply(lambda x: st.session_state.custom_keterangan.get(str(x), "-"))
    
    def color_status_only(val):
        c = {'Open': '#ff4b4b', 'In Progress': '#ffa500', 'Solved': '#00c853'}
        return f'color: {c.get(val, "white")}; font-weight: 700;'

    st.dataframe(
        df[['ID Ticket', 'nama_user', 'cabang', 'masalah', 'status', 'waktu', 'IT Notes']].style.map(color_status_only, subset=['status']), 
        use_container_width=True, 
        hide_index=True
    )

    # Actions Section
    st.markdown("---")
    c_a, c_b = st.columns(2)
    with c_a:
        if has_access("Input Tiket"):
            with st.expander("➕ CREATE NEW TICKET"):
                with st.form("new_tix"):
                    un = st.text_input("Requester Name")
                    cb = st.selectbox("Branch", st.secrets["master"]["daftar_cabang"])
                    ms = st.text_area("Issue Detail")
                    if st.form_submit_button("Submit to Database"):
                        db = get_connection(); cur = db.cursor()
                        cur.execute("INSERT INTO tickets (nama_user, cabang, masalah, status, waktu) VALUES (%s,%s,%s,'Open',%s)", (un, cb, ms, get_wib_now()))
                        db.close(); st.success("Data Saved Successfully"); st.rerun()
    with c_b:
        if has_access("Update Status"):
            with st.expander("🛠️ UPDATE TICKET STATUS"):
                tix_list = {f"#{row['ID Ticket']} - {row['nama_user']}": row['id'] for _, row in df.iterrows()}
                if tix_list:
                    sel_label = st.selectbox("Select Target Ticket", list(tix_list.keys()))
                    sel_id = tix_list[sel_label]
                    new_st = st.selectbox("Assign New Status", ["Open", "In Progress", "Solved", "Closed"])
                    cat_it = st.text_input("IT Remarks", value=st.session_state.custom_keterangan.get(str(sel_id), ""))
                    if st.button("Commit Changes", use_container_width=True):
                        db = get_connection(); cur = db.cursor()
                        cur.execute("UPDATE tickets SET status=%s WHERE id=%s", (new_st, sel_id))
                        st.session_state.custom_keterangan[str(sel_id)] = cat_it
                        save_data('keterangan_it.json', st.session_state.custom_keterangan)
                        db.commit(); db.close(); st.success("Update Successful"); st.rerun()

    if has_access("Export"):
        st.download_button("📥 EXPORT DATA TO CSV", df.to_csv(index=False).encode('utf-8'), "IT_Data_Report.csv", use_container_width=True)

# ... (Menu lain tetap ada namun tersembunyi sesuai hak akses)
