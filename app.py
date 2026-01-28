import streamlit as st
import pymysql
import pandas as pd
import certifi

# Konfigurasi halaman
st.set_page_config(page_title="IT Helpdesk", page_icon="🎫", layout="wide")

# Fungsi koneksi ke TiDB Cloud (Sudah diperbaiki)
def get_connection():
    return pymysql.connect(
        host=st.secrets["tidb"]["host"],
        port=int(st.secrets["tidb"]["port"]), # Pastikan port adalah integer
        user=st.secrets["tidb"]["user"],
        password=st.secrets["tidb"]["password"],
        database=st.secrets["tidb"]["database"],
        autocommit=True,
        ssl={'ca': certifi.where()} # Perbaikan FileNotFoundError
    )

# --- SIDEBAR: NAVIGASI ---
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
                try:
                    db = get_connection()
                    cursor = db.cursor()
                    query = "INSERT INTO tickets (nama_user, masalah, prioritas, status) VALUES (%s, %s, %s, 'Open')"
                    cursor.execute(query, (user, issue, priority))
                    db.close()
                    st.success(f"Tiket untuk {user} berhasil dikirim!")
                    st.balloons()
                except Exception as e:
                    st.error(f"Gagal kirim tiket: {e}")
            else:
                st.error("Mohon isi semua field!")

# --- MENU 2: DAFTAR TIKET ---
elif menu == "Daftar Tiket":
    st.header("📊 Dashboard Monitoring Tiket")
    
    try:
        db = get_connection()
        df = pd.read_sql("SELECT * FROM tickets ORDER BY waktu DESC", db)
        db.close()

        if not df.empty:
            # Filter
            col1, col2 = st.columns(2)
            with col1:
                f_status = st.multiselect("Filter Status", options=df['status'].unique(), default=df['status'].unique())
            with col2:
                f_priority = st.multiselect("Filter Prioritas", options=df['prioritas'].unique(), default=df['prioritas'].unique())

            filtered_df = df[(df['status'].isin(f_status)) & (df['prioritas'].isin(f_priority))]
            st.dataframe(filtered_df, use_container_width=True, hide_index=True)

            # Update Status
            st.divider()
            st.subheader("✅ Update Status Tiket")
            col_id, col_stat, col_btn = st.columns([1, 2, 1])
            with col_id:
                selected_id = st.selectbox("Pilih ID Tiket", filtered_df['id'].tolist())
            with col_stat:
                new_status = st.selectbox("Ubah Status", ["Open", "In Progress", "Solved", "Closed"])
            with col_btn:
                st.write(" ")
                if st.button("Update"):
                    db = get_connection()
                    cursor = db.cursor()
                    cursor.execute("UPDATE tickets SET status=%s WHERE id=%s", (new_status, selected_id))
                    db.close()
                    st.toast("Status Berhasil Diperbarui!")
                    st.rerun()
        else:
            st.info("Belum ada tiket yang masuk.")
    except Exception as e:
        st.error(f"Gagal mengambil data: {e}")
