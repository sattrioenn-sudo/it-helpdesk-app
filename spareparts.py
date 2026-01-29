import streamlit as st
import pandas as pd

def show_sparepart_menu(get_connection, get_wib_now, add_log):
    # Ambil nama DB dari secrets agar tidak hardcoded
    db_name = st.secrets["tidb"]["database"]
    
    st.markdown("## ⚙️ Sparepart Inventory")
    
    tab_view, tab_input = st.tabs(["📦 Stock Monitoring", "➕ Input Barang"])
    
    with tab_view:
        st.markdown("<div class='action-header'>Data Inventaris Sparepart</div>", unsafe_allow_html=True)
        try:
            db = get_connection()
            # 1. PAKSA PILIH DATABASE DI LEVEL SESSION
            db.select_db(db_name) 
            
            # 2. GUNAKAN ALAMAT LENGKAP (db_name.tabel) UNTUK KEAMANAN GANDA
            query = f"SELECT id, nama_part, kode_part, kategori, jumlah, keterangan, waktu FROM {db_name}.spareparts ORDER BY id DESC"
            df = pd.read_sql(query, db)
            db.close()
            
            if not df.empty:
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("Belum ada data sparepart.")
        except Exception as e:
            if "1146" in str(e):
                st.warning(f"Tabel 'spareparts' belum ada di database '{db_name}'.")
                st.info("Silakan buat tabelnya dulu di TiDB Cloud Console.")
            else:
                st.error(f"Gagal memuat data: {e}")

    with tab_input:
        st.markdown("<div class='action-header'>Tambah Sparepart Baru</div>", unsafe_allow_html=True)
        with st.form("form_sp", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                p_name = st.text_input("Nama Barang")
                p_code = st.text_input("Kode/Serial Number")
            with c2:
                p_cat = st.selectbox("Kategori", ["Hardware", "Network", "Peripheral", "CCTV", "Other"])
                p_qty = st.number_input("Jumlah Stock", min_value=0, step=1)
            
            p_desc = st.text_area("Keterangan Tambahan")
            
            if st.form_submit_button("SIMPAN DATA SPAREPART 🚀", use_container_width=True):
                if p_name and p_code:
                    try:
                        db = get_connection()
                        # 3. PAKSA PILIH DATABASE SEBELUM OPERASI WRITE
                        db.select_db(db_name)
                        cur = db.cursor()
                        
                        waktu_wib = get_wib_now().strftime('%Y-%m-%d %H:%M:%S')
                        # 4. GUNAKAN ALAMAT LENGKAP PADA QUERY INSERT
                        sql = f"INSERT INTO {db_name}.spareparts (nama_part, kode_part, kategori, jumlah, keterangan, waktu) VALUES (%s, %s, %s, %s, %s, %s)"
                        
                        cur.execute(sql, (p_name, p_code, p_cat, p_qty, p_desc, waktu_wib))
                        db.close()
                        
                        add_log("SPAREPART", f"Menambah {p_name} ({p_qty} pcs)")
                        st.toast(f"✅ {p_name} Berhasil disimpan!", icon='⚙️')
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error Database: {e}")
                else:
                    st.warning("Nama dan Kode wajib diisi!")
