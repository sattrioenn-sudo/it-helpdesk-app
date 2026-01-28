import streamlit as st
import pymysql
import pandas as pd

# Konfigurasi halaman
st.set_page_config(page_title="IT Helpdesk", page_icon="🎫", layout="wide")

# Fungsi koneksi ke TiDB Cloud
def get_connection():
    return pymysql.connect(
        host=st.secrets["tidb"]["host"],
        port=st.secrets["tidb"]["port"],
        user=st.secrets["tidb"]["user"],
        password=st.secrets["tidb"]["password"],
        database=st.secrets["tidb"]["database"],
        autocommit=True,
        ssl={'ca': 'etc/ssl/certs/ca-certificates.crt'} # Opsional, sesuaikan jika TiDB minta SSL
    )

# --- SIDEBAR: FILTER & NAVIGASI ---
st.sidebar.title("⚙️ Control Panel")
menu = st.sidebar.radio("Menu", ["Buat Tiket", "Daftar Tiket"])

# --- MENU 1: BUAT TIKET ---
if menu == "Buat Tiket":
    st.header("📝 Buat Laporan Baru")
    with st.form("ticket_form", clear_on_submit=True):
        user = st.text_input("Nama User / Departemen")
        issue = st.text_area("Detail Masalah IT")
        priority = st.select_slider("Tingkat Prioritas", options=["Low", "Medium", "High"])
        
        submitted = st.form_submit_button("Kirim Laporan")
        if submitted:
            if user and issue:
                db = get_connection()
                cursor = db.cursor()
                query = "INSERT INTO tickets (nama_user, masalah, prioritas, status) VALUES (%s, %s, %s, 'Open')"
                cursor.execute(query, (user, issue, priority))
                db.close()
                st.success(f"Tiket untuk {user} berhasil dikirim!")
                st.balloons()
            else:
                st.error("Mohon isi semua field!")

# --- MENU 2: DAFTAR TIKET (MANAJEMEN) ---
elif menu == "Daftar Tiket":
    st.header("📊 Dashboard Monitoring Tiket")
    
    db = get_connection()
    df = pd.read_sql("SELECT * FROM tickets ORDER BY waktu DESC", db)
    db.close()

    # Filter di atas tabel
    col1, col2 = st.columns(2)
    with col1:
        f_status = st.multiselect("Filter Status", options=df['status'].unique(), default=df['status'].unique())
    with col2:
        f_priority = st.multiselect("Filter Prioritas", options=df['prioritas'].unique(), default=df['prioritas'].unique())

    filtered_df = df[(df['status'].isin(f_status)) & (df['prioritas'].isin(f_priority))]
    
    # Tampilkan Data
    st.dataframe(filtered_df, use_container_width=True, hide_index=True)

    # --- FITUR UPDATE STATUS ---
    st.divider()
    st.subheader("✅ Update Status Tiket")
    ticket_ids = filtered_df['id'].tolist()
    
    if ticket_ids:
        col_id, col_stat, col_btn = st.columns([1, 2, 1])
        with col_id:
            selected_id = st.selectbox("Pilih ID Tiket", ticket_ids)
        with col_stat:
            new_status = st.selectbox("Ubah Status Menjadi", ["Open", "In Progress", "Solved", "Closed"])
        with col_btn:
            st.write(" ") # Padding
            if st.button("Update Sekarang"):
                db = get_connection()
                cursor = db.cursor()
                cursor.execute("UPDATE tickets SET status=%s WHERE id=%s", (new_status, selected_id))
                db.close()
                st.toast(f"Tiket #{selected_id} diperbarui ke {new_status}!", icon="🚀")
                st.rerun()
    else:
        st.info("Tidak ada tiket untuk di-update.")
