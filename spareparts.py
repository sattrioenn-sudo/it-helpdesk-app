import streamlit as st
import pandas as pd

def show_sparepart_menu(get_connection, get_wib_now, add_log):
    db_name = st.secrets["tidb"]["database"]
    user_aktif = st.session_state.user_name.upper()
    waktu_sekarang = get_wib_now().strftime('%Y-%m-%d %H:%M:%S')
    
    st.markdown("## ⚙️ Smart Inventory System")
    
    tab_view, tab_transaksi, tab_approve, tab_manage = st.tabs([
        "📦 Stock Monitoring", "🔄 Mutasi Barang", "✅ Approval Center", "🛠️ Kelola Data"
    ])
    
    # --- AMBIL DATA STOK UNTUK REFERENSI ---
    try:
        db = get_connection(); db.select_db(db_name)
        df_all = pd.read_sql(f"SELECT * FROM {db_name}.spareparts", db); db.close()
    except:
        df_all = pd.DataFrame()

    # --- TAB 1: VIEW DATA ---
    with tab_view:
        st.markdown("<div class='action-header'>Log Inventaris Aktif</div>", unsafe_allow_html=True)
        if not df_all.empty:
            df = df_all.copy().sort_values(by='id', ascending=False).reset_index(drop=True)
            df.insert(0, 'No', range(1, len(df) + 1))
            df['Status'] = df['keterangan'].apply(lambda x: "🟡 Pending" if "[PENDING]" in str(x) else "🟢 Approved")
            
            df_display = df.drop(columns=['id'])
            df_display.columns = ['No', 'Barang', 'S/N', 'Kategori', 'Stok', 'Info & User', 'Waktu Masuk', 'Status']
            
            f_status = st.multiselect("Filter Status:", ["🟡 Pending", "🟢 Approved"], default=["🟡 Pending", "🟢 Approved"])
            st.dataframe(df_display[df_display['Status'].isin(f_status)], use_container_width=True, hide_index=True)
        else:
            st.info("Gudang kosong.")

    # --- TAB 2: MUTASI (OTOMATIS UNTUK BARANG KELUAR) ---
    with tab_transaksi:
        st.markdown("<div class='action-header'>Input Mutasi Barang</div>", unsafe_allow_html=True)
        
        m_type = st.radio("Pilih Aksi:", ["Barang Masuk", "Barang Keluar"], horizontal=True)
        
        with st.form("form_mutasi_smart", clear_on_submit=True):
            # Logika Otomatis Ambil Data Stok
            if m_type == "Barang Keluar":
                # Hanya ambil barang yang sudah APPROVED untuk dikeluarkan
                df_approved = df_all[df_all['keterangan'].str.contains("\[APPROVED\]", na=False)]
                if not df_approved.empty:
                    # Buat label pilihan agar user mudah memilih
                    pilihan_barang = {row['id']: f"{row['nama_part']} | S/N: {row['kode_part']} (Sisa: {row['jumlah']})" for _, row in df_approved.iterrows()}
                    selected_ref = st.selectbox("Pilih Barang dari Stok:", pilihan_barang.keys(), format_func=lambda x: pilihan_barang[x])
                    
                    # Ambil data dari barang yang dipilih
                    data_ref = df_approved[df_approved['id'] == selected_ref].iloc[0]
                    m_name = data_ref['nama_part']
                    m_sn = data_ref['kode_part']
                    m_cat = data_ref['kategori']
                    st.info(f"Mengeluarkan: {m_name} (S/N: {m_sn})")
                else:
                    st.warning("Tidak ada barang Approved di stok untuk dikeluarkan.")
                    m_name, m_sn, m_cat = "", "", "Other"
            else:
                # Jika barang masuk, input manual seperti biasa
                c1, c2 = st.columns(2)
                with c1: m_name = st.text_input("Nama Barang Baru")
                with c2: m_sn = st.text_input("Serial Number / Kode")
                m_cat = st.selectbox("Kategori", ["Hardware", "Network", "Peripheral", "CCTV", "Other"])

            m_qty = st.number_input("Jumlah Unit", min_value=1, step=1)
            m_note = st.text_area("Catatan/Tujuan (Misal: Dipasang di Ruang Server)")
            
            if st.form_submit_button("AJUKAN SEKARANG 🚀", use_container_width=True):
                if m_name and m_sn:
                    try:
                        tag = "[PENDING] [MASUK]" if m_type == "Barang Masuk" else "[PENDING] [KELUAR]"
                        ket_final = f"{tag} | Oleh: {user_aktif} | Note: {m_note}"
                        
                        db = get_connection(); db.select_db(db_name); cur = db.cursor()
                        sql = f"INSERT INTO {db_name}.spareparts (nama_part, kode_part, kategori, jumlah, keterangan, waktu) VALUES (%s,%s,%s,%s,%s,%s)"
                        cur.execute(sql, (m_name, m_sn, m_cat, m_qty, ket_final, waktu_sekarang))
                        db.close()
                        
                        add_log("MUTASI", f"{m_type}: {m_name}")
                        st.toast("✅ Berhasil diajukan!"); st.rerun()
                    except Exception as e: st.error(e)
                else:
                    st.warning("Lengkapi data barang!")

    # --- TAB 3: APPROVAL CENTER ---
    with tab_approve:
        st.markdown("<div class='action-header'>Menunggu Persetujuan Admin</div>", unsafe_allow_html=True)
        df_pending = df_all[df_all['keterangan'].str.contains("\[PENDING\]", na=False)]
        if not df_pending.empty:
            for i, (_, row) in enumerate(df_pending.iterrows(), 1):
                with st.expander(f"Antrean #{i} | {row['nama_part']} ({row['jumlah']} unit)"):
                    st.write(f"**Detail:** {row['keterangan']}")
                    if st.button(f"APPROVE SEKARANG", key=f"app_{row['id']}", use_container_width=True):
                        new_ket = row['keterangan'].replace("[PENDING]", "[APPROVED]")
                        db = get_connection(); db.select_db(db_name); cur = db.cursor()
                        cur.execute(f"UPDATE {db_name}.spareparts SET keterangan = %s WHERE id = %s", (new_ket, row['id']))
                        db.close(); st.rerun()
        else:
            st.success("Semua permintaan sudah diproses. ✅")

    # --- TAB 4: KELOLA ---
    with tab_manage:
        st.markdown("<div class='action-header'>Hapus Data</div>", unsafe_allow_html=True)
        if not df_all.empty:
            opt = {row['id']: f"{row['nama_part']} ({row['waktu']})" for _, row in df_all.iterrows()}
            sel = st.selectbox("Pilih Data:", opt.keys(), format_func=lambda x: opt[x])
            if st.button("HAPUS 🗑️", use_container_width=True):
                db = get_connection(); db.select_db(db_name); cur = db.cursor()
                cur.execute(f"DELETE FROM {db_name}.spareparts WHERE id = %s", (sel,))
                db.close(); st.rerun()
