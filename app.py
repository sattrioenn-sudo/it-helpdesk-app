import streamlit as st
import pymysql
import pandas as pd
import certifi
import json
import os
from datetime import datetime, timedelta

# --- 1. KONFIGURASI & THEME (TETAP) ---
st.set_page_config(page_title="IT Kemasan", page_icon="🎫", layout="wide")

# --- 2. STORAGE VIRTUAL (DIPERBARUI) ---
def load_data(file, default):
    if os.path.exists(file):
        with open(file, 'r') as f: return json.load(f)
    return default

def save_data(file, data):
    with open(file, 'w') as f: json.dump(data, f)

# Inisialisasi Data JSON
if 'custom_keterangan' not in st.session_state:
    st.session_state.custom_keterangan = load_data('keterangan_it.json', {})

# Fitur Baru: Manajemen User & Hak Akses (Disimpan Permanen)
if 'user_db' not in st.session_state:
    # Format: {username: [password, role, [list_izin]]}
    default_users = {"admin": ["kcs_2026", "Admin", ["Dashboard", "Input Tiket", "Update Status", "Inventory", "Export", "Security", "Hapus Tiket"]]}
    st.session_state.user_db = load_data('users_it.json', default_users)

# Fitur Baru: Registry Waktu Solved (Virtual)
if 'solved_times' not in st.session_state:
    st.session_state.solved_times = load_data('solved_times.json', {})

# --- 3. FUNGSI UTAMA ---
def get_wib_now():
    return datetime.utcnow() + timedelta(hours=7)

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

def has_access(perm):
    user = st.session_state.get("user_name", "").lower()
    user_data = st.session_state.user_db.get(user, [None, None, ["Dashboard"]])
    return perm in user_data[2]

# --- 4. UI ENHANCEMENT (TETAP) ---
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at 50% 50%, #0f172a 0%, #020617 100%); }
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px; border-radius: 15px;
    }
    .clock-inner {
        background: rgba(59, 130, 246, 0.1); 
        border-radius: 15px; padding: 10px; text-align: center;
        border: 1px solid rgba(59, 130, 246, 0.3); margin-bottom: 20px;
    }
    .digital-clock { font-family: 'JetBrains Mono', monospace; color: #60a5fa; font-size: 24px; font-weight: 800; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. LOGIC AUTH & SIDEBAR ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #60a5fa;'>🎫 IT-KEMASAN</h2>", unsafe_allow_html=True)
    wib = get_wib_now()
    st.markdown(f'''<div class="clock-inner"><div class="digital-clock">{wib.strftime("%H:%M:%S")}</div><div style="color: #94a3b8; font-size: 11px;">{wib.strftime("%A, %d %b %Y")}</div></div>''', unsafe_allow_html=True)

    if st.session_state.logged_in:
        st.markdown(f"<p style='text-align: center;'>User: <b>{st.session_state.user_name.upper()}</b><br>Role: <small>{st.session_state.user_role}</small></p>", unsafe_allow_html=True)
        
        # Menu Navigasi Dinamis Berdasarkan Izin
        menu_list = ["Dashboard Monitor"]
        if has_access("Inventory"): menu_list.append("📦 Inventory Spareparts")
        if has_access("User Management"): menu_list.append("👥 Manajemen User")
        if has_access("Export"): menu_list.append("Export & Reporting")
        if has_access("Security"): menu_list.append("Security Log")
        
        menu = st.selectbox("📂 MENU NAVIGASI", menu_list)
        
        if st.button("🔒 LOGOUT", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

        # Grafik Trend (TETAP)
        st.markdown("---")
        try:
            db = get_connection()
            df_graph = pd.read_sql("SELECT status, COUNT(*) as qty FROM tickets GROUP BY status", db)
            db.close()
            if not df_graph.empty: st.bar_chart(df_graph.set_index('status'), height=150)
        except: st.caption("Database sedang sibuk...")
    else:
        u = st.text_input("Username").lower()
        p = st.text_input("Password", type="password")
        if st.button("🔓 LOGIN", use_container_width=True):
            if u in st.session_state.user_db and p == st.session_state.user_db[u][0]:
                st.session_state.logged_in = True
                st.session_state.user_name = u
                st.session_state.user_role = st.session_state.user_db[u][1]
                st.rerun()
            else: st.error("Kredensial Salah")

if not st.session_state.logged_in:
    st.info("👋 Silakan login untuk mengakses sistem.")
    st.stop()

# --- 6. MENU: DASHBOARD MONITOR ---
if menu == "Dashboard Monitor":
    st.markdown("### 📊 IT Support Metrics")
    db = get_connection()
    df = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", db)
    
    query_sp = "SELECT nama_part, kode_part, kategori, CAST(SUM(jumlah) AS SIGNED) as total FROM spareparts WHERE keterangan LIKE '%%[APPROVED]%%' GROUP BY nama_part, kode_part, kategori HAVING total > 0"
    df_stok = pd.read_sql(query_sp, db)
    db.close()

    # Perhitungan Waktu Input & Solved
    df['Waktu Input'] = pd.to_datetime(df['waktu']).dt.strftime('%d/%m/%Y %H:%M')
    df['Waktu Solved'] = df['id'].apply(lambda x: st.session_state.solved_times.get(str(x), "-"))

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Tiket", len(df))
    m2.metric("🔴 Open", len(df[df['status'] == 'Open']))
    m3.metric("🟡 In Progress", len(df[df['status'] == 'In Progress']))
    m4.metric("🟢 Solved", len(df[df['status'] == 'Solved']))

    st.markdown("---")
    df['Keterangan IT'] = df['id'].apply(lambda x: st.session_state.custom_keterangan.get(str(x), "-"))
    
    # Menampilkan kolom Waktu Input & Solved di tabel
    st.dataframe(df[['id', 'nama_user', 'cabang', 'masalah', 'status', 'Waktu Input', 'Waktu Solved', 'Keterangan IT']], use_container_width=True, hide_index=True)

    col_a, col_b = st.columns([1, 1])
    with col_a:
        if has_access("Input Tiket"):
            with st.expander("➕ Input Tiket Baru"):
                with st.form("new_ticket", clear_on_submit=True):
                    u_in = st.text_input("Nama Pelapor")
                    c_in = st.selectbox("Cabang", st.secrets["master"]["daftar_cabang"])
                    m_in = st.text_area("Masalah")
                    p_in = st.select_slider("Urgensi", ["Low", "Medium", "High"])
                    if st.form_submit_button("Submit"):
                        if u_in and m_in:
                            db = get_connection(); cur = db.cursor()
                            cur.execute("INSERT INTO tickets (nama_user, cabang, masalah, prioritas, status, waktu) VALUES (%s,%s,%s,%s,'Open',%s)", (u_in, c_in, m_in, p_in, get_wib_now().strftime('%Y-%m-%d %H:%M:%S')))
                            db.close(); st.rerun()

    with col_b:
        if has_access("Update Status"):
            with st.expander("🛠️ Update Status & Sparepart"):
                id_sel = st.selectbox("Pilih ID Tiket", df['id'].tolist())
                st_sel = st.selectbox("Status", ["Open", "In Progress", "Solved", "Closed"])
                ganti = st.checkbox("Gunakan Sparepart?")
                sp_data, qty = None, 0
                
                if ganti and not df_stok.empty:
                    df_stok['opt'] = df_stok['nama_part'] + " | S/N: " + df_stok['kode_part']
                    pilih_sp = st.selectbox("Pilih Barang", df_stok['opt'].tolist())
                    sp_data = df_stok[df_stok['opt'] == pilih_sp].iloc[0]
                    qty = st.number_input(f"Jumlah (Stok: {int(sp_data['total'])})", 1, int(sp_data['total']), 1)
                
                ket_tambahan = st.text_input("Catatan IT", value=st.session_state.custom_keterangan.get(str(id_sel), ""))
                if st.button("Konfirmasi Update", use_container_width=True):
                    db = get_connection(); cur = db.cursor()
                    cur.execute("UPDATE tickets SET status=%s WHERE id=%s", (st_sel, id_sel))
                    
                    # Logic Catat Waktu Solved Otomatis
                    if st_sel == "Solved":
                        st.session_state.solved_times[str(id_sel)] = get_wib_now().strftime('%d/%m/%Y %H:%M')
                        save_data('solved_times.json', st.session_state.solved_times)

                    ket_final = ket_tambahan
                    if ganti and sp_data is not None:
                        ket_final += f" [Ganti: {sp_data['nama_part']} x{qty}]"
                        cur.execute("INSERT INTO spareparts (nama_part, kode_part, kategori, jumlah, keterangan, waktu) VALUES (%s,%s,%s,%s,%s,%s)", (sp_data['nama_part'], sp_data['kode_part'], sp_data['kategori'], -qty, f"[APPROVED] [KELUAR] Tiket #{id_sel}", get_wib_now().strftime('%Y-%m-%d %H:%M:%S')))
                    
                    st.session_state.custom_keterangan[str(id_sel)] = ket_final
                    save_data('keterangan_it.json', st.session_state.custom_keterangan)
                    db.commit(); db.close(); st.rerun()

# --- 7. MENU BARU: MANAJEMEN USER ---
elif menu == "👥 Manajemen User":
    st.markdown("### 👥 User Access Management")
    c1, c2 = st.columns([1, 1.5])
    with c1:
        st.write("**Daftar User**")
        st.table(pd.DataFrame([{"User": k, "Role": v[1]} for k, v in st.session_state.user_db.items()]))
    
    with c2:
        st.write("**Tambah/Edit User**")
        with st.form("user_management"):
            new_u = st.text_input("Username").lower()
            new_p = st.text_input("Password")
            new_r = st.selectbox("Role", ["Staff IT", "Admin", "Manager"])
            st.write("Izin Akses:")
            p_tix = st.checkbox("Input Tiket")
            p_upd = st.checkbox("Update Status")
            p_inv = st.checkbox("Inventory")
            p_exp = st.checkbox("Export")
            p_usr = st.checkbox("User Management")
            p_sec = st.checkbox("Security")
            
            if st.form_submit_button("Simpan User"):
                perms = ["Dashboard"]
                if p_tix: perms.append("Input Tiket")
                if p_upd: perms.append("Update Status")
                if p_inv: perms.append("Inventory")
                if p_exp: perms.append("Export")
                if p_usr: perms.append("User Management")
                if p_sec: perms.append("Security")
                
                st.session_state.user_db[new_u] = [new_p, new_r, perms]
                save_data('users_it.json', st.session_state.user_db)
                st.success("User Berhasil Disimpan!"); st.rerun()

# --- 8. MENU LAINNYA (TETAP) ---
elif menu == "📦 Inventory Spareparts":
    try:
        from spareparts import show_sparepart_menu
        show_sparepart_menu(get_connection, get_wib_now, lambda a, d: None)
    except Exception as e: st.error(f"Gagal memuat modul spareparts: {e}")

elif menu == "Export & Reporting":
    st.markdown("### 📂 Export Data Tiket")
    db = get_connection(); df_ex = pd.read_sql("SELECT * FROM tickets", db); db.close()
    df_ex['Waktu_Input'] = pd.to_datetime(df_ex['waktu']).dt.strftime('%d/%m/%Y %H:%M')
    df_ex['Waktu_Solved'] = df_ex['id'].apply(lambda x: st.session_state.solved_times.get(str(x), "-"))
    df_ex['Keterangan_IT'] = df_ex['id'].apply(lambda x: st.session_state.custom_keterangan.get(str(x), "-"))
    st.dataframe(df_ex[['id', 'nama_user', 'cabang', 'masalah', 'status', 'Waktu_Input', 'Waktu_Solved', 'Keterangan_IT']], use_container_width=True)
    st.download_button("📥 DOWNLOAD CSV", df_ex.to_csv(index=False).encode('utf-8'), "IT_Report_Full.csv", use_container_width=True)

elif menu == "Security Log":
    st.markdown("### 🛡️ System Audit Log")
    st.dataframe(pd.DataFrame(st.session_state.get('audit_logs', [])), use_container_width=True)
