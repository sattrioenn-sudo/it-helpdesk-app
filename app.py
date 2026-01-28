import streamlit as st
import pymysql
import pandas as pd
import certifi
from datetime import datetime

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="IT Helpdesk Pro", 
    page_icon="🎫", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- CUSTOM CSS (DARK MODE FRIENDLY & NEUMORPHISM STYLE) ---
st.markdown("""
    <style>
    /* Global Background */
    .main { background-color: #f0f2f6; }
    
    /* Custom Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0e1117;
        color: white;
    }
    
    /* Header Styling */
    .main-header {
        font-size: 36px;
        font-weight: 800;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 20px;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    /* Card Styling */
    .stMetric {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 5px 5px 15px #d1d9e6, -5px -5px 15px #ffffff;
        border: none !important;
    }
    
    /* Form Styling */
    .stForm {
        background-color: white;
        padding: 30px;
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.05);
    }
    
    /* Status Badge Colors */
    .status-open { color: #ef4444; font-weight: bold; }
    .status-progress { color: #f59e0b; font-weight: bold; }
    .status-solved { color: #10b981; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

# --- FUNGSI HELPER KONEKSI ---
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

# --- FUNGSI LOGIN ---
def login():
    with st.sidebar:
        st.markdown("<h1 style='text-align: center; color: white;'>🎫 IT-PRO</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #94a3b8;'>Enterprise Support System</p>", unsafe_allow_html=True)
        st.divider()
        
        if 'logged_in' not in st.session_state:
            st.session_state.logged_in = False
        
        if not st.session_state.logged_in:
            st.subheader("🔐 Staff Access")
            user_input = st.text_input("Username")
            pw_input = st.text_input("Password", type="password")
            if st.button("Sign In", use_container_width=True, type="primary"):
                users_dict = st.secrets["auth"]
                if user_input in users_dict and pw_input == users_dict[user_input]:
                    st.session_state.logged_in = True
                    st.session_state.user_name = user_input
                    st.rerun()
                else:
                    st.error("Access Denied")
        else:
            st.markdown(f"👤 **Operator:** {st.session_state.user_name.capitalize()}")
            if st.button("Logout", use_container_width=True):
                st.session_state.logged_in = False
                st.rerun()

login()
st.sidebar.divider()

# --- LOGIKA NAVIGASI ---
if st.session_state.logged_in:
    menu = st.sidebar.selectbox("📂 MENU UTAMA", ["Daftar Tiket", "Statistik", "Buat Tiket", "Management User"])
else:
    menu = "Buat Tiket"
    st.sidebar.info("Gunakan login admin untuk akses dashboard monitoring.")

# --- MENU 1: BUAT TIKET (UI Modern Form) ---
if menu == "Buat Tiket":
    st.markdown("<div class='main-header'>📝 Submit New Support Ticket</div>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("ticket_form", clear_on_submit=True):
            user = st.text_input("👤 Nama User / Departemen", placeholder="Contoh: Ahmad - Finance")
            cabang = st.selectbox("🏢 Cabang Lokasi", st.secrets["master"]["daftar_cabang"])
            issue = st.text_area("🛠 Detail Kendala IT", placeholder="Jelaskan masalah Anda secara detail...")
            
            c_left, c_right = st.columns(2)
            priority = c_left.select_slider("🔥 Prioritas", options=["Low", "Medium", "High"])
            
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("🚀 KIRIM LAPORAN", use_container_width=True)
            
            if submitted:
                if user and issue:
                    try:
                        db = get_connection()
                        cursor = db.cursor()
                        cursor.execute("INSERT INTO tickets (nama_user, cabang, masalah, prioritas, status) VALUES (%s, %s, %s, %s, 'Open')", (user, cabang, issue, priority))
                        db.close()
                        st.success("✅ Berhasil! Tiket Anda sedang dalam antrean tim IT.")
                        st.balloons()
                    except Exception as e:
                        st.error(f"Database Error: {e}")
                else:
                    st.warning("⚠️ Harap lengkapi semua field!")

# --- MENU 2: DAFTAR TIKET (Admin Dashboard) ---
elif menu == "Daftar Tiket" and st.session_state.logged_in:
    st.markdown(f"<div class='main-header'>📊 IT Monitoring Center</div>", unsafe_allow_html=True)
    
    db = get_connection()
    df = pd.read_sql("SELECT id, nama_user, cabang, masalah, prioritas, status, waktu FROM tickets ORDER BY id DESC", db)
    db.close()

    # Dashboard Metrics
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📦 Total Tiket", len(df))
    m2.metric("🔴 Open", len(df[df['status'] == 'Open']), delta_color="inverse")
    m3.metric("🟡 In Progress", len(df[df['status'] == 'In Progress']))
    m4.metric("🟢 Solved", len(df[df['status'] == 'Solved']))

    st.markdown("<br>", unsafe_allow_html=True)
    
    # Table View dengan Styling
    st.subheader("📑 Database Antrean Tiket")
    st.dataframe(
        df, 
        use_container_width=True, 
        hide_index=True,
        column_config={
            "id": "ID",
            "nama_user": "User",
            "cabang": "Lokasi",
            "masalah": "Deskripsi Masalah",
            "prioritas": st.column_config.SelectboxColumn("Priority", options=["Low", "Medium", "High"]),
            "status": st.column_config.TextColumn("Status"),
            "waktu": "Waktu Masuk"
        }
    )

    # Action Panel
    st.divider()
    act1, act2 = st.columns(2)
    
    with act1:
        with st.expander("🔄 Update Status Pekerjaan"):
            if not df.empty:
                id_upd = st.selectbox("Pilih ID Tiket", df['id'].tolist(), key="upd")
                new_status = st.select_slider("Set Status Ke:", options=["Open", "In Progress", "Solved", "Closed"])
                if st.button("Konfirmasi Update", use_container_width=True, type="primary"):
                    db = get_connection()
                    cursor = db.cursor()
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S') if new_status in ["Solved", "Closed"] else None
                    cursor.execute("UPDATE tickets SET status=%s, waktu_selesai=%s WHERE id=%s", (new_status, now, id_upd))
                    db.close()
                    st.success(f"Tiket #{id_upd} diperbarui!")
                    st.rerun()

    with act2:
        with st.expander("🗑️ Hapus Tiket (Gunakan Hati-hati)"):
            if not df.empty:
                id_del = st.selectbox("Pilih ID Tiket", df['id'].tolist(), key="del")
                st.error("Tindakan ini permanen dan tidak bisa dibatalkan.")
                if st.button("HAPUS SEKARANG", use_container_width=True):
                    db = get_connection()
                    cursor = db.cursor()
                    cursor.execute("DELETE FROM tickets WHERE id=%s", (id_del))
                    db.close()
                    st.toast(f"Tiket #{id_del} Dihapus!")
                    st.rerun()

# --- MENU 3: STATISTIK ---
elif menu == "Statistik" and st.session_state.logged_in:
    st.markdown("<div class='main-header'>📈 IT Support Analytics</div>", unsafe_allow_html=True)
    db = get_connection()
    df_s = pd.read_sql("SELECT status, cabang, prioritas FROM tickets", db)
    db.close()

    if not df_s.empty:
        t1, t2 = st.tabs(["📊 Lokasi & Status", "🔥 Analisis Prioritas"])
        with t1:
            c1, c2 = st.columns(2)
            c1.markdown("### Beban per Cabang")
            c1.bar_chart(df_s['cabang'].value_counts())
            c2.markdown("### Distribusi Status")
            c2.area_chart(df_s['status'].value_counts())
        with t2:
            st.markdown("### Level Urgensi Tiket")
            st.line_chart(df_s['prioritas'].value_counts())
    else:
        st.info("Belum ada data untuk dianalisis.")

# --- MENU 4: MANAGEMENT USER ---
elif menu == "Management User" and st.session_state.logged_in:
    st.markdown("<div class='main-header'>👤 User Management Directory</div>", unsafe_allow_html=True)
    users = st.secrets["auth"]
    
    col_a, col_b, col_c = st.columns([1, 2, 1])
    with col_b:
        st.info("💡 Username & Password dikelola melalui Streamlit Secrets.")
        user_list = [{"No": i+1, "Username": u, "Role": "Administrator IT"} for i, u in enumerate(users)]
        st.table(user_list)
