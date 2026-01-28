import streamlit as st
import pymysql
import pandas as pd
import certifi
import requests
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="IT Helpdesk Pro", 
    page_icon="🎫", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM UI DESIGN (CSS) ---
st.markdown("""
    <style>
    /* Mengubah font dan background */
    .main { background-color: #f8f9fa; }
    
    /* Mempercantik Card Statistik */
    div[data-testid="stMetricValue"] { font-size: 28px; color: #007bff; }
    div[data-testid="metric-container"] {
        background-color: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        border: 1px solid #eee;
    }
    
    /* Tombol Kustom */
    .stButton>button {
        border-radius: 8px;
        transition: all 0.3s;
        border: none;
        font-weight: 600;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    
    /* Sidebar Styling */
    .css-1d391kg { background-color: #1e293b; }
    [data-testid="stSidebar"] { background-image: linear-gradient(#1e293b, #0f172a); color: white; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNGSI LOGIN ---
def login():
    with st.sidebar:
        st.title("🔐 IT Portal")
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False
        
        if not st.session_state.logged_in:
            with st.container():
                user_input = st.text_input("Username", placeholder="Masukkan username")
                pw_input = st.text_input("Password", type="password", placeholder="******")
                if st.button("Login", use_container_width=True):
                    users_dict = st.secrets["auth"]
                    if user_input in users_dict and pw_input == users_dict[user_input]:
                        st.session_state.logged_in = True
                        st.session_state.user_name = user_input
                        st.rerun()
                    else:
                        st.error("Invalid Credentials")
        else:
            st.success(f"Online: **{st.session_state.user_name.upper()}**")
            if st.button("Logout", use_container_width=True, type="secondary"):
                st.session_state.logged_in = False
                st.rerun()

# --- FUNGSI HELPER ---
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

def send_telegram(user, cabang, issue, priority):
    token = st.secrets["telegram"]["token"]
    chat_id = st.secrets["telegram"]["chat_id"]
    pesan = f"⚠️ *TIKET BARU MASUK*\n\n👤 *User:* {user}\n🏢 *Cabang:* {cabang}\n🔥 *Prioritas:* {priority}\n🛠 *Masalah:* {issue}"
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={pesan}&parse_mode=Markdown"
    try: requests.get(url, timeout=5)
    except: pass

# --- JALANKAN LOGIN & SIDEBAR ---
login()
st.sidebar.divider()

if st.session_state.logged_in:
    menu = st.sidebar.selectbox("🧭 Navigasi Menu", ["Daftar Tiket", "Buat Tiket", "Statistik", "Management User"])
else:
    menu = "Buat Tiket"
    st.sidebar.warning("Akses Admin Terkunci")

# --- MENU 1: BUAT TIKET (UI Modern Form) ---
if menu == "Buat Tiket":
    st.title("📝 Submit IT Ticket")
    st.markdown("Silakan isi detail kendala IT Anda di bawah ini.")
    
    with st.container():
        with st.form("ticket_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                user = st.text_input("👤 Nama Lengkap / Dept", placeholder="Contoh: Budi - Marketing")
            with col2:
                cabang = st.selectbox("🏢 Cabang", st.secrets["master"]["daftar_cabang"])
            
            issue = st.text_area("🛠 Detail Masalah", placeholder="Jelaskan kendala Anda sejelas mungkin...")
            
            col3, col4 = st.columns([2, 1])
            with col3:
                priority = st.select_slider("🔥 Tingkat Prioritas", options=["Low", "Medium", "High"])
            
            st.write("")
            submitted = st.form_submit_button("🚀 Kirim Laporan Sekarang", use_container_width=True)
            
            if submitted:
                if user and issue:
                    try:
                        db = get_connection()
                        cursor = db.cursor()
                        query = "INSERT INTO tickets (nama_user, cabang, masalah, prioritas, status) VALUES (%s, %s, %s, %s, 'Open')"
                        cursor.execute(query, (user, cabang, issue, priority))
                        db.close()
                        send_telegram(user, cabang, issue, priority)
                        st.success("✅ Tiket Anda telah diterima! Tim IT akan segera memproses.")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Koneksi Gagal: {e}")
                else:
                    st.warning("Mohon lengkapi data Anda!")

# --- MENU 2: DAFTAR TIKET (UI Dashboard) ---
elif menu == "Daftar Tiket" and st.session_state.logged_in:
    st.title("📊 Monitoring Center")
    
    db = get_connection()
    df = pd.read_sql("SELECT id, nama_user, cabang, masalah, prioritas, status, waktu FROM tickets ORDER BY id DESC", db)
    db.close()

    # Ringkasan Cepat dalam bentuk Kartu
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Tiket", len(df))
    m2.metric("Open", len(df[df['status'] == 'Open']))
    m3.metric("In Progress", len(df[df['status'] == 'In Progress']))
    m4.metric("Solved", len(df[df['status'] == 'Solved']))

    st.divider()
    
    # Filter Ekspander
    with st.expander("🔍 Filter Data Tiket"):
        c1, c2, c3 = st.columns(3)
        f_status = c1.multiselect("Status", df['status'].unique(), default=df['status'].unique())
        f_priority = c2.multiselect("Prioritas", df['prioritas'].unique(), default=df['prioritas'].unique())
        f_cabang = c3.multiselect("Cabang", df['cabang'].unique(), default=df['cabang'].unique())

    filtered_df = df[(df['status'].isin(f_status)) & (df['prioritas'].isin(f_priority)) & (df['cabang'].isin(f_cabang))]
    
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

    # Update Area
    st.write("")
    with st.expander("⚙️ Aksi Cepat (Update Status)"):
        if not filtered_df.empty:
            u1, u2, u3 = st.columns([1, 2, 1])
            selected_id = u1.selectbox("Pilih ID", filtered_df['id'].tolist())
            new_status = u2.selectbox("Set Status Baru", ["Open", "In Progress", "Solved", "Closed"])
            if u3.button("Simpan Perubahan", use_container_width=True, type="primary"):
                db = get_connection()
                cursor = db.cursor()
                now = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if new_status in ["Solved", "Closed"] else None
                cursor.execute("UPDATE tickets SET status=%s, waktu_selesai=%s WHERE id=%s", (new_status, now, selected_id))
                db.close()
                st.success("Berhasil diupdate!")
                st.rerun()

# --- MENU 3: STATISTIK (UI Visual) ---
elif menu == "Statistik" and st.session_state.logged_in:
    st.title("📈 IT Performance Analytics")
    db = get_connection()
    df_full = pd.read_sql("SELECT status, cabang, prioritas FROM tickets", db)
    db.close()

    tab1, tab2 = st.tabs(["📍 Analisis Cabang", "🚦 Analisis Status"])
    
    with tab1:
        st.subheader("Distribusi Tiket per Cabang")
        st.bar_chart(df_full['cabang'].value_counts(), color="#007bff")
        
    with tab2:
        st.subheader("Persentase Status & Prioritas")
        c1, c2 = st.columns(2)
        c1.write("Berdasarkan Status")
        c1.area_chart(df_full['status'].value_counts())
        c2.write("Berdasarkan Prioritas")
        c2.bar_chart(df_full['prioritas'].value_counts(), color="#ff4b4b")

# --- MENU 4: MANAGEMENT USER ---
elif menu == "Management User" and st.session_state.logged_in:
    st.title("👤 User Management")
    st.info("Daftar staf yang memiliki akses ke sistem admin.")
    
    users = st.secrets["auth"]
    df_users = pd.DataFrame([{"Username": u, "Role": "Admin/IT Staff", "Status": "Active"} for u in users])
    st.table(df_users)
