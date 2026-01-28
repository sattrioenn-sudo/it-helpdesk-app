import streamlit as st
import pymysql
import pandas as pd
import certifi
import requests
from datetime import datetime

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
def send_telegram(user, cabang, issue, priority):
    token = st.secrets["telegram"]["token"]
    chat_id = st.secrets["telegram"]["chat_id"]
    pesan = f"⚠️ *TIKET BARU MASUK*\n\n👤 *User:* {user}\n🏢 *Cabang:* {cabang}\n🔥 *Prioritas:* {priority}\n🛠 *Masalah:* {issue}"
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

login()
st.sidebar.divider()
st.sidebar.title("⚙️ IT Control Center")

if st.session_state.logged_in:
    menu = st.sidebar.radio("Menu", ["Buat Tiket", "Daftar Tiket", "Statistik"])
else:
    menu = st.sidebar.radio("Menu", ["Buat Tiket"])
    st.sidebar.info("Login untuk akses Dashboard Admin")

# --- MENU 1: BUAT TIKET ---
if menu == "Buat Tiket":
    st.header("📝 Buat Laporan Baru")
    with st.form("ticket_form", clear_on_submit=True):
        col_u, col_c = st.columns(2)
        with col_u:
            user = st.text_input("Nama User / Departemen")
        with col_c:
            # --- MENGAMBIL DATA CABANG DARI SECRETS ---
            list_cabang = st.secrets["master"]["daftar_cabang"]
            cabang = st.selectbox("Cabang Perusahaan", list_cabang)
            
        issue = st.text_area("Detail Masalah IT")
        priority = st.select_slider("Tingkat Prioritas", options=["Low", "Medium", "High"])
        
        submitted = st.form_submit_button("Kirim Laporan")
        if submitted and user and issue:
            try:
                db = get_connection()
                cursor = db.cursor()
                query = "INSERT INTO tickets (nama_user, cabang, masalah, priority, status) VALUES (%s, %s, %s, %s, 'Open')"
                # Pastikan nama kolom 'priority' sesuai dengan di DB (tadi kita pakai prioritas atau priority?)
                # Jika di DB namanya 'prioritas', ganti query di bawah:
                query = "INSERT INTO tickets (nama_user, cabang, masalah, prioritas, status) VALUES (%s, %s, %s, %s, 'Open')"
                cursor.execute(query, (user, cabang, issue, priority))
                db.close()
                send_telegram(user, cabang, issue, priority)
                st.success(f"Tiket dari {cabang} berhasil terkirim!")
                st.balloons()
            except Exception as e:
                st.error(f"Error: {e}")

# --- MENU 2: DAFTAR TIKET (ADMIN) ---
elif menu == "Daftar Tiket" and st.session_state.logged_in:
    st.header("📊 Dashboard Monitoring")
    db = get_connection()
    df = pd.read_sql("SELECT id, nama_user, cabang, masalah, prioritas, status, waktu as 'Waktu Masuk', waktu_selesai as 'Waktu Selesai' FROM tickets ORDER BY id DESC", db)
    db.close()

    if not df.empty:
        c1, c2, c3 = st.columns(3)
        with c1:
            f_status = st.multiselect("Status", options=df['status'].unique(), default=df['status'].unique())
        with c2:
            f_priority = st.multiselect("Prioritas", options=df['prioritas'].unique(), default=df['prioritas'].unique())
        with c3:
            # Gunakan list dari secrets juga untuk filter kalau mau, tapi dari data SQL lebih akurat
            f_cabang = st.multiselect("Cabang", options=df['cabang'].unique(), default=df['cabang'].unique())

        filtered_df = df[(df['status'].isin(f_status)) & (df['prioritas'].isin(f_priority)) & (df['cabang'].isin(f_cabang))]
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("✅ Update Status & Waktu Selesai")
        # Logika update tetap sama seperti sebelumnya
        if not filtered_df.empty:
            col_id, col_stat, col_btn = st.columns([1, 2, 1])
            with col_id:
                selected_id = st.selectbox("Pilih ID Tiket", filtered_df['id'].tolist())
            with col_stat:
                new_status = st.selectbox("Ubah Status", ["Open", "In Progress", "Solved", "Closed"])
            with col_btn:
                st.write("")
                if st.button("Update Sekarang"):
                    db = get_connection()
                    cursor = db.cursor()
                    if new_status in ["Solved", "Closed"]:
                        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        cursor.execute("UPDATE tickets SET status=%s, waktu_selesai=%s WHERE id=%s", (new_status, now, selected_id))
                    else:
                        cursor.execute("UPDATE tickets SET status=%s, waktu_selesai=NULL WHERE id=%s", (new_status, selected_id))
                    db.close()
                    st.rerun()
    else:
        st.info("Belum ada tiket.")

elif menu == "Statistik" and st.session_state.logged_in:
    st.header("📈 Analitik Support")
    db = get_connection()
    df_full = pd.read_sql("SELECT status, cabang FROM tickets", db)
    db.close()

    if not df_full.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.write("Jumlah Tiket per Cabang")
            st.bar_chart(df_full['cabang'].value_counts())
        with col2:
            st.write("Distribusi Status Tiket")
            st.bar_chart(df_full['status'].value_counts())
