import streamlit as st
import pandas as pd

def show_sparepart_menu(get_connection, get_wib_now, add_log):
    db_name = st.secrets["tidb"]["database"]
    user_aktif = st.session_state.user_name.upper()
    
    st.markdown("## ⚙️ Advanced Sparepart System")
    
    tab_view, tab_input, tab_manage = st.tabs(["📦 Stock Monitoring", "➕ Input Barang", "🛠️ Kelola Data"])
    
    # --- TAB 1: VIEW DATA ---
    with tab_view:
        st.markdown("<div class='action-header'>Log Inventaris Aktif</div>", unsafe_allow_html=True)
        try:
            db = get_connection()
            db.select_db(db_name)
            # Ambil data dari database
            query = f"SELECT id, nama_part, kode_part, kategori, jumlah, keterangan, waktu FROM {db_name}.spareparts ORDER BY id DESC"
            df = pd.read_sql(query, db)
            db.close()
            
            if not df.empty:
                # LOGIKA ID VIRTUAL: Membuat nomor urut baru agar tampilan tetap cantik (1, 2, 3...)
                # Kita balik urutannya agar nomor 1 adalah data paling lama, atau tetap sesuai urutan list
                df = df.reset_index(drop=True)
                df.insert(0, 'No', range(1, len(df) + 1))
                
                # Sembunyikan ID asli database dari tampilan (tapi tetap ada di background)
                df_display = df.drop(columns=['id'])
                
                # Mempercantik tampilan kolom
                df_display.columns = ['No', 'Nama Barang', 'Serial Number', 'Kategori', 'Stok', 'User & Catatan', 'Waktu Input']
                st.dataframe(df_display, use_container_width=True, hide_index=True)
                st.caption(f"Total: {len(df)} item terdaftar.")
            else:
                st.info("Gudang kosong. Belum ada data sparepart.")
        except Exception as e:
            st.error(f"Gagal memuat data: {e}")

    # --- TAB 2: INPUT DATA ---
    with tab_input:
        st.markdown("<div class='action-header'>Form Input Barang Baru</div>", unsafe_allow_html=True)
        with st.form("form_sp_pro", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                p_name = st.text_input("Nama Barang", placeholder="Contoh: RAM DDR4 16GB")
                p_code = st.text_input("Serial Number / Kode", placeholder="S/N: 123456xxx")
            with c2:
                p_cat = st.selectbox("Kategori", ["Hardware", "Network", "Peripheral", "CCTV", "Other"])
                p_qty = st.number_input("Jumlah Stock", min_value=1, step=1)
            
            p_desc_input = st.text_area("Catatan Tambahan (Opsional)")
            
            if st.form_submit_button("KONFIRMASI SIMPAN 🚀", use_container_width=True):
                if p_name and p_code:
                    try:
                        catatan_final = f"By: {user_aktif} | {p_desc_input}" if p_desc_input else f"By: {user_aktif}"
                        db = get_connection()
                        db.select_db(db_name)
                        cur = db.cursor()
                        waktu_wib = get_wib_now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        sql = f"INSERT INTO {db_name}.spareparts (nama_part, kode_part, kategori, jumlah, keterangan, waktu) VALUES (%s, %s, %s, %s, %s, %s)"
                        cur.execute(sql, (p_name, p_code, p_cat, p_qty, catatan_final, waktu_wib))
                        db.close()
                        
                        add_log("SPAREPART", f"Input {p_name}")
                        st.toast(f"Berhasil simpan {p_name}!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Gagal simpan: {e}")
                else:
                    st.warning("Nama dan S/N wajib diisi!")

    # --- TAB 3: MANAGE (DELETE) ---
    with tab_manage:
        st.markdown("<div class='action-header'>Penghapusan Data</div>", unsafe_allow_html=True)
        try:
            db = get_connection()
            db.select_db(db_name)
            # Tetap ambil ID asli untuk proses penghapusan di background
            df_manage = pd.read_sql(f"SELECT id, nama_part, kode_part FROM {db_name}.spareparts", db)
            
            if not df_manage.empty:
                # Dropdown tetap menggunakan ID asli database agar tidak salah hapus
                options = {row['id']: f"{row['nama_part']} ({row['kode_part']})" for _, row in df_manage.iterrows()}
                selected_id = st.selectbox("Pilih Barang yang akan dihapus", options.keys(), format_func=lambda x: options[x])
                
                if st.button("HAPUS PERMANEN 🗑️", use_container_width=True):
                    cur = db.cursor()
                    cur.execute(f"DELETE FROM {db_name}.spareparts WHERE id = %s", (selected_id,))
                    db.close()
                    add_log("DELETE_SP", f"Hapus ID #{selected_id}")
                    st.rerun()
            else:
                st.info("Tidak ada data.")
            db.close()
        except Exception as e:
            st.error(f"Error: {e}")
