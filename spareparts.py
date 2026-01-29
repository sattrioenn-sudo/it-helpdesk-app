import streamlit as st
import pandas as pd

def show_sparepart_menu(get_connection, get_wib_now, add_log):
    db_name = st.secrets["tidb"]["database"]
    user_aktif = st.session_state.user_name.upper()
    
    st.markdown("## ⚙️ Advanced Inventory & Transaction")
    
    tab_view, tab_transaksi, tab_approve, tab_manage = st.tabs([
        "📦 Stock Monitoring", "🔄 Mutasi Barang", "✅ Approval Center", "🛠️ Kelola Data"
    ])
    
    # --- TAB 1: VIEW DATA ---
    with tab_view:
        st.markdown("<div class='action-header'>Log Inventaris Aktif</div>", unsafe_allow_html=True)
        try:
            db = get_connection(); db.select_db(db_name)
            df = pd.read_sql(f"SELECT * FROM {db_name}.spareparts ORDER BY id DESC", db); db.close()
            
            if not df.empty:
                # Logika ID Virtual & Filter Approved
                df = df.reset_index(drop=True)
                df.insert(0, 'No', range(1, len(df) + 1))
                
                # Tambahkan kolom Status secara visual berdasarkan teks di keterangan
                df['Status'] = df['keterangan'].apply(lambda x: "🟡 Pending" if "[PENDING]" in str(x) else "🟢 Approved")
                
                df_display = df.drop(columns=['id'])
                df_display.columns = ['No', 'Barang', 'S/N', 'Kategori', 'Stok', 'Info & User', 'Waktu', 'Status']
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else:
                st.info("Gudang kosong.")
        except Exception as e:
            st.error(f"Error: {e}")

    # --- TAB 2: MUTASI (MASUK/KELUAR) ---
    with tab_transaksi:
        st.markdown("<div class='action-header'>Input Mutasi Barang (Pending)</div>", unsafe_allow_html=True)
        with st.form("form_mutasi"):
            col1, col2 = st.columns(2)
            with col1:
                m_type = st.radio("Jenis Mutasi", ["Barang Masuk", "Barang Keluar"])
                m_name = st.text_input("Nama Barang")
            with col2:
                m_sn = st.text_input("Serial Number")
                m_qty = st.number_input("Jumlah", min_value=1)
            
            m_cat = st.selectbox("Kategori", ["Hardware", "Network", "Peripheral", "CCTV", "Other"])
            m_note = st.text_area("Alasan/Tujuan")
            
            if st.form_submit_button("AJUKAN MUTASI 🚀"):
                if m_name and m_sn:
                    try:
                        # Kita tandai dengan [PENDING] dan Jenis Mutasi
                        prefix = "[PENDING] [MASUK]" if m_type == "Barang Masuk" else "[PENDING] [KELUAR]"
                        ket_final = f"{prefix} | Oleh: {user_aktif} | Note: {m_note}"
                        
                        db = get_connection(); db.select_db(db_name); cur = db.cursor()
                        waktu = get_wib_now().strftime('%Y-%m-%d %H:%M:%S')
                        sql = f"INSERT INTO {db_name}.spareparts (nama_part, kode_part, kategori, jumlah, keterangan, waktu) VALUES (%s,%s,%s,%s,%s,%s)"
                        cur.execute(sql, (m_name, m_sn, m_cat, m_qty, ket_final, waktu))
                        db.close()
                        
                        add_log("MUTASI", f"Pengajuan {m_type}: {m_name}")
                        st.toast("Pengajuan terkirim! Menunggu approval."); st.rerun()
                    except Exception as e: st.error(e)

    # --- TAB 3: APPROVAL CENTER ---
    with tab_approve:
        st.markdown("<div class='action-header'>Persetujuan Mutasi Barang</div>", unsafe_allow_html=True)
        db = get_connection(); db.select_db(db_name)
        df_app = pd.read_sql(f"SELECT * FROM {db_name}.spareparts WHERE keterangan LIKE '%[PENDING]%'", db)
        
        if not df_app.empty:
            for _, row in df_app.iterrows():
                with st.expander(f"📌 {row['nama_part']} ({row['jumlah']} pcs) - {row['kode_part']}"):
                    st.write(f"**Detail:** {row['keterangan']}")
                    if st.button(f"APPROVE ID {row['id']}", key=f"app_{row['id']}"):
                        new_ket = row['keterangan'].replace("[PENDING]", "[APPROVED]")
                        cur = db.cursor()
                        cur.execute(f"UPDATE {db_name}.spareparts SET keterangan = %s WHERE id = %s", (new_ket, row['id']))
                        db.close(); add_log("APPROVE", f"Approved ID {row['id']}"); st.rerun()
        else:
            st.success("Semua mutasi sudah di-approve! ✅")

    # --- TAB 4: MANAGE ---
    with tab_manage:
        # Fitur hapus tetap ada seperti sebelumnya
        db = get_connection(); db.select_db(db_name)
        df_del = pd.read_sql(f"SELECT id, nama_part FROM {db_name}.spareparts", db)
        if not df_del.empty:
            sel_id = st.selectbox("Hapus Data Permanen", df_del['id'].tolist(), format_func=lambda x: f"ID {x}")
            if st.button("HAPUS 🗑️"):
                cur = db.cursor(); cur.execute(f"DELETE FROM {db_name}.spareparts WHERE id = %s", (sel_id,))
                db.close(); st.rerun()
