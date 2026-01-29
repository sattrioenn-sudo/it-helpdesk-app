import streamlit as st
import pandas as pd

def show_sparepart_menu(get_connection, get_wib_now, add_log):
    db_name = st.secrets["tidb"]["database"]
    user_aktif = st.session_state.user_name.upper()
    waktu_sekarang = get_wib_now().strftime('%Y-%m-%d %H:%M:%S')
    
    st.markdown("## ⚙️ Advanced Inventory & Transaction")
    
    tab_view, tab_transaksi, tab_approve, tab_manage = st.tabs([
        "📦 Stock Monitoring", "🔄 Mutasi Barang", "✅ Approval Center", "🛠️ Kelola Data"
    ])
    
    # --- TAB 1: VIEW DATA (ID SELALU URUT DARI 1) ---
    with tab_view:
        st.markdown("<div class='action-header'>Log Inventaris Aktif</div>", unsafe_allow_html=True)
        try:
            db = get_connection(); db.select_db(db_name)
            # Ambil data, urutkan berdasarkan waktu/id terbaru di atas
            df = pd.read_sql(f"SELECT * FROM {db_name}.spareparts ORDER BY id DESC", db); db.close()
            
            if not df.empty:
                # REVISI: Paksa Reset Index agar ID yang tampil selalu mulai dari 1
                df = df.reset_index(drop=True)
                # Tambahkan kolom 'No' di posisi paling kiri
                df.insert(0, 'No', range(1, len(df) + 1))
                
                # Deteksi Status
                df['Status'] = df['keterangan'].apply(lambda x: "🟡 Pending" if "[PENDING]" in str(x) else "🟢 Approved")
                
                # HAPUS KOLOM 'id' ASLI DATABASE AGAR TIDAK MEMBINGUNGKAN USER
                df_display = df.drop(columns=['id'])
                
                # Nama Kolom yang rapi
                df_display.columns = ['No', 'Barang', 'S/N', 'Kategori', 'Stok', 'Info & User', 'Waktu Masuk', 'Status']
                
                f_status = st.multiselect("Filter Status:", ["🟡 Pending", "🟢 Approved"], default=["🟡 Pending", "🟢 Approved"])
                df_filtered = df_display[df_display['Status'].isin(f_status)]
                
                st.dataframe(df_filtered, use_container_width=True, hide_index=True)
                st.caption(f"Menampilkan {len(df_filtered)} item.")
            else:
                st.info("Gudang kosong.")
        except Exception as e:
            st.error(f"Error View: {e}")

    # --- TAB 2: MUTASI ---
    with tab_transaksi:
        st.markdown("<div class='action-header'>Input Mutasi Barang</div>", unsafe_allow_html=True)
        with st.form("form_mutasi", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                m_type = st.selectbox("Jenis Mutasi", ["Barang Masuk", "Barang Keluar"])
                m_name = st.text_input("Nama Barang")
            with col2:
                m_sn = st.text_input("Serial Number / Kode")
                m_qty = st.number_input("Jumlah", min_value=1, step=1)
            
            m_cat = st.selectbox("Kategori", ["Hardware", "Network", "Peripheral", "CCTV", "Other"])
            m_note = st.text_area("Alasan / Catatan")
            
            if st.form_submit_button("AJUKAN SEKARANG 🚀", use_container_width=True):
                if m_name and m_sn:
                    try:
                        prefix = "[PENDING] [MASUK]" if m_type == "Barang Masuk" else "[PENDING] [KELUAR]"
                        ket_final = f"{prefix} | Oleh: {user_aktif} | Note: {m_note}"
                        db = get_connection(); db.select_db(db_name); cur = db.cursor()
                        sql = f"INSERT INTO {db_name}.spareparts (nama_part, kode_part, kategori, jumlah, keterangan, waktu) VALUES (%s,%s,%s,%s,%s,%s)"
                        cur.execute(sql, (m_name, m_sn, m_cat, m_qty, ket_final, waktu_sekarang))
                        db.close()
                        add_log("MUTASI", f"Ajukan {m_type}: {m_name}")
                        st.toast(f"✅ Berhasil!"); st.rerun()
                    except Exception as e: st.error(f"Gagal: {e}")

    # --- TAB 3: APPROVAL CENTER (PAKAI NO URUT JUGA) ---
    with tab_approve:
        st.markdown("<div class='action-header'>Menunggu Persetujuan Admin</div>", unsafe_allow_html=True)
        try:
            db = get_connection(); db.select_db(db_name)
            df_app = pd.read_sql(f"SELECT * FROM {db_name}.spareparts WHERE keterangan LIKE '%[PENDING]%'", db)
            
            if not df_app.empty:
                # Beri nomor urut visual di expander
                for i, row in enumerate(df_app.iterrows(), 1):
                    item = row[1]
                    with st.expander(f"Antrean #{i} | 📌 {item['nama_part']} ({item['jumlah']} unit)"):
                        st.info(f"Detail: {item['keterangan']}")
                        # Tombol tetap pakai item['id'] di backend agar akurat, tapi user lihat Antrean #1, #2...
                        if st.button(f"SETUJUI ANTREAN #{i}", key=f"btn_app_{item['id']}", use_container_width=True):
                            new_ket = item['keterangan'].replace("[PENDING]", "[APPROVED]")
                            cur = db.cursor()
                            cur.execute(f"UPDATE {db_name}.spareparts SET keterangan = %s WHERE id = %s", (new_ket, item['id']))
                            db.close(); add_log("APPROVE", f"Approved {item['nama_part']}"); st.rerun()
            else:
                st.success("Semua bersih! ✅")
        except Exception as e: st.error(e)

    # --- TAB 4: KELOLA DATA (HAPUS BERDASARKAN NAMA & WAKTU) ---
    with tab_manage:
        st.markdown("<div class='action-header'>Hapus Data (Admin Only)</div>", unsafe_allow_html=True)
        try:
            db = get_connection(); db.select_db(db_name)
            df_manage = pd.read_sql(f"SELECT id, nama_part, kode_part, waktu FROM {db_name}.spareparts ORDER BY id DESC", db)
            
            if not df_manage.empty:
                # User memilih berdasarkan Nama dan Waktu (Tanpa melihat ID Database yang berantakan)
                # Kita buat label pilihan yang bersih
                options = {row['id']: f"Barang: {row['nama_part']} | SN: {row['kode_part']} | Masuk: {row['waktu']}" for _, row in df_manage.iterrows()}
                
                selected_db_id = st.selectbox("Pilih data yang ingin dibuang:", 
                                         options.keys(), 
                                         format_func=lambda x: options[x])
                
                st.warning("⚠️ Data akan dihapus selamanya dari sistem.")
                if st.button("YA, HAPUS SEKARANG 🗑️", use_container_width=True):
                    cur = db.cursor()
                    cur.execute(f"DELETE FROM {db_name}.spareparts WHERE id = %s", (selected_db_id,))
                    db.close()
                    add_log("DELETE_SP", f"Hapus Item: {options[selected_db_id]}")
                    st.toast("Terhapus!"); st.rerun()
            else:
                st.info("Tidak ada data.")
        except Exception as e: st.error(e)
