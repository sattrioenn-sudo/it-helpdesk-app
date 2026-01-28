import streamlit as st
import pymysql
import pandas as pd
import certifi
import requests

# Konfigurasi halaman
st.set_page_config(page_title="IT Helpdesk Pro", page_icon="🎫", layout="wide")

# --- FUNGSI LOGIN ---
def login():
    st.sidebar.title("🔐 Admin Login")
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        user_input = st.sidebar.text_input("Username")
        pw_input = st.sidebar.text_input("Password", type="password")
        if st.sidebar.button("Login"):
            if user_input == st.secrets["auth"]["admin_user"] and pw_input == st.secrets["auth"]["admin_password"]:
                st.session_state.logged_in = True
                st.sidebar.success("Login Berhasil!")
                st.rerun()
            else:
                st.sidebar.error("Username/Password Salah")
    else:
        if st.sidebar.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()

# Fungsi Kirim Notifikasi Telegram
def send_telegram(user, issue, priority):
    token = st.secrets["telegram"]["token"]
    chat_id = st.secrets["telegram"]["chat_id"]
    pesan = f"⚠️ *TIKET BARU MASUK*\n\n👤 *User:* {user}\n🔥 *Prioritas:* {priority}\n🛠 *Masalah:* {issue}"
    url = f"https://api.telegram.org/bot{token}/sendMessage?chat_id={chat_id}&text={pesan}&parse_mode=Markdown"
    try:
        requests.get(url, timeout=5)
    except:
        pass

# Fungsi koneksi ke TiDB Cloud
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

# --- JALANKAN FUNGSI LOGIN ---
login()

st.sidebar.divider()
st.sidebar.title("⚙️ IT Control Center")

# Filter Menu berdasarkan status login
if st.session_state.logged_in:
    menu = st.sidebar.radio("Menu", ["Buat Tiket", "Daftar Tiket", "Statistik"])
else:
    menu = st.sidebar.radio("Menu", ["Buat Tiket"])
    st.sidebar.info("Login untuk akses Dashboard Admin")

# --- MENU 1: BUAT TIKET (Akses Semua Orang) ---
if menu == "Buat Tiket":
    st.header("📝 Buat Laporan Baru")
    with st.form("ticket_form", clear_on_submit=True):
        user = st.text_input("Nama User / Departemen")
        issue = st.text_area("Detail Masalah IT")
        priority = st.select_slider("Tingkat Prioritas", options=["Low", "Medium", "High"])
        
        submitted = st.form_submit_button("Kirim Laporan")
        if submitted and user and issue:
            try:
                db = get_connection()
                cursor = db.cursor()
                query = "INSERT INTO tickets (nama_user, masalah, prioritas, status) VALUES (%s, %s, %s, 'Open')"
                cursor.execute(query, (user, issue, priority))
                db.close()
                send_telegram(user, issue, priority)
                st.success("Tiket terkirim! Tim IT sudah dinotifikasi.")
                st.balloons()
            except Exception as e:
                st.error(f"Error: {e}")

# --- MENU 2 & 3: HANYA UNTUK ADMIN ---
elif menu == "Daftar Tiket" and st.session_state.logged_in:
    st.header("📊 Dashboard Monitoring")
    db = get_connection()
    df = pd.read_sql("SELECT * FROM tickets ORDER BY waktu DESC", db)
    db.close()

    if not df.empty:
        col1, col2 = st.columns(2)
        with col1:
            f_status = st.multiselect("Status", options=df['status'].unique(), default=df['status'].unique())
        with col2:
            f_priority = st.multiselect("Prioritas", options=df['prioritas'].unique(), default=df['prioritas'].unique())

        filtered_df = df[(df['status'].isin(f_status)) & (df['prioritas'].isin(f_priority))]
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("✅ Update Status")
        col_id, col_stat, col_btn = st.columns([1, 2, 1])
        with col_id:
            selected_id = st.selectbox("ID Tiket", filtered_df['id'].tolist())
        with col_stat:
            new_status = st.selectbox("Status Baru", ["Open", "In Progress", "Solved", "Closed"])
        with col_btn:
            st.write("")
            if st.button("Update"):
                db = get_connection()
                cursor = db.cursor()
                cursor.execute("UPDATE tickets SET status=%s WHERE id=%s", (new_status, selected_id))
                db.close()
                st.rerun()
    else:
        st.info("Belum ada tiket.")

elif menu == "Statistik" and st.session_state.logged_in:
    st.header("📈 Analitik Support")
    db = get_connection()
    df = pd.read_sql("SELECT status, COUNT(*) as jumlah FROM tickets GROUP BY status", db)
    db.close()

    if not df.empty:
        col1, col2 = st.columns([1, 2])
        with col1:
            st.write("Ringkasan Status")
            st.table(df)
        with col2:
            st.bar_chart(df.set_index('status'))
