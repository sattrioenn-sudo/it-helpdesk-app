import streamlit as st
import pymysql
import pandas as pd
import certifi
import json
import os
from datetime import datetime, timedelta

# --- 1. KONFIGURASI & THEME ---
st.set_page_config(page_title="IT Kemasan", page_icon="🎫", layout="wide")

# --- 2. STORAGE VIRTUAL ---
def load_data(file, default):
    if os.path.exists(file):
        with open(file, 'r') as f: return json.load(f)
    return default

def save_data(file, data):
    with open(file, 'w') as f: json.dump(data, f)

if 'custom_keterangan' not in st.session_state:
    st.session_state.custom_keterangan = load_data('keterangan_it.json', {})
if 'user_permissions' not in st.session_state:
    st.session_state.user_permissions = load_data('permissions_it.json', {"admin": ["Input", "Edit", "Hapus", "Export", "Security"]})

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
    user_perms = st.session_state.user_permissions.get(user, ["Input"])
    return perm in user_perms

# --- 4. UI ENHANCEMENT (CUSTOM CSS) ---
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at 50% 50%, #0f172a 0%, #020617 100%); }
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        padding: 15px; border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .clock-inner {
        background: rgba(59, 130, 246, 0.1); 
        border-radius: 15px; padding: 10px; text-align: center;
        border: 1px solid rgba(59, 130, 246, 0.3); margin-bottom: 20px;
    }
    .digital-clock {
        font-family: 'JetBrains Mono', monospace; color: #60a5fa;
        font-size: 24px; font-weight: 800;
    }
    .stButton>button {
        border-radius: 8px !important;
        transition: all 0.3s ease;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(37, 99, 235, 0.4);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. SIDEBAR DENGAN GRAFIK ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #60a5fa;'>🎫 IT-KEMASAN</h2>", unsafe_allow_html=True)
    wib = get_wib_now()
    st.markdown(f'''
        <div class="clock-inner">
            <div class="digital-clock">{wib.strftime("%H:%M:%S")}</div>
            <div style="color: #94a3b8; font-size: 11px;">{wib.strftime("%A, %d %b %Y")}</div>
        </div>
    ''', unsafe_allow_html=True)

    if st.session_state.logged_in:
        st.markdown(f"<p style='text-align: center;'>User: <b>{st.session_state.user_name.upper()}</b></p>", unsafe_allow_html=True)
        menu_list = ["Dashboard Monitor", "📦 Inventory Spareparts"]
        if has_access("Export"): menu_list.append("Export & Reporting")
        if has_access("Security"): menu_list.append("Security Log")
        menu = st.selectbox("📂 MENU NAVIGASI", menu_list)
        
        if st.button("🔒 LOGOUT", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

        # --- GRAFIK TREND TIKET DI SIDEBAR ---
        st.markdown("---")
        st.markdown("<p style='font-size: 12px; color: #60a5fa; text-align: center; font-weight: bold;'>TICKET STATUS TREND</p>", unsafe_allow_html=True)
        try:
            db = get_connection()
            df_graph = pd.read_sql("SELECT status, COUNT(*) as qty FROM tickets GROUP BY status", db)
            db.close()
            if not df_graph.empty:
                st.bar_chart(df_graph.set_index('status'), height=150)
            else:
                st.caption("Belum ada data tiket.")
        except:
            st.caption("Database sedang sibuk...")
    else:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("🔓 LOGIN", use_container_width=True):
            if u in st.secrets["auth"] and p == st.secrets["auth"][u]:
                st.session_state.logged_in = True
                st.session_state.user_name = u
                st.rerun()

if not st.session_state.logged_in:
    st.info("👋 Silakan login di sidebar untuk mengakses sistem.")
    st.stop()

# --- 6. DASHBOARD MONITOR ---
if menu == "Dashboard Monitor":
    st.markdown("### 📊 IT Support Metrics")
    db = get_connection()
    df = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", db)
    
    # Perbaikan: Menggunakan CAST agar jumlah stok bulat (tanpa desimal)
    query_sp = """
        SELECT nama_part, kode_part, kategori, CAST(SUM(jumlah) AS SIGNED) as total 
        FROM spareparts 
        WHERE keterangan LIKE '%%[APPROVED]%%' 
        GROUP BY nama_part, kode_part, kategori 
        HAVING total > 0
    """
    df_stok = pd.read_sql(query_sp, db)
    db.close()

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Total Tiket", len(df))
    m2.metric("🔴 Open", len(df[df['status'] == 'Open']))
    m3.metric("🟡 In Progress", len(df[df['status'] == 'In Progress']))
    m4.metric("🟢 Solved", len(df[df['status'] == 'Solved']))

    st.markdown("---")
    df['Keterangan IT'] = df['id'].apply(lambda x: st.session_state.custom_keterangan.get(str(x), "-"))
    st.dataframe(df[['id', 'nama_user', 'cabang', 'masalah', 'status', 'prioritas', 'waktu', 'Keterangan IT']], use_container_width=True, hide_index=True)

    col_a, col_b = st.columns([1, 1])
    with col_a:
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
        with st.expander("🛠️ Update Status & Sparepart"):
            id_sel = st.selectbox("Pilih ID Tiket", df['id'].tolist())
            st_sel = st.selectbox("Status", ["Open", "In Progress", "Solved", "Closed"])
            ganti = st.checkbox("Gunakan Sparepart?")
            sp_data, qty = None, 0
            
            if ganti and not df_stok.empty:
                # Perbaikan Tampilan: Bersih tanpa desimal (1.0)
                df_stok['opt'] = df_stok['nama_part'] + " | S/N: " + df_stok['kode_part']
                pilih_sp = st.selectbox("Pilih Barang", df_stok['opt'].tolist())
                sp_data = df_stok[df_stok['opt'] == pilih_sp].iloc[0]
                qty = st.number_input(f"Jumlah (Stok: {int(sp_data['total'])})", 1, int(sp_data['total']), 1)
            
            ket_tambahan = st.text_input("Catatan IT", value=st.session_state.custom_keterangan.get(str(id_sel), ""))
            if st.button("Konfirmasi Update", use_container_width=True):
                db = get_connection(); cur = db.cursor()
                cur.execute("UPDATE tickets SET status=%s WHERE id=%s", (st_sel, id_sel))
                ket_final = ket_tambahan
                if ganti and sp_data is not None:
                    ket_final += f" [Ganti: {sp_data['nama_part']} x{qty}]"
                    cur.execute("INSERT INTO spareparts (nama_part, kode_part, kategori, jumlah, keterangan, waktu) VALUES (%s,%s,%s,%s,%s,%s)", (sp_data['nama_part'], sp_data['kode_part'], sp_data['kategori'], -qty, f"[APPROVED] [KELUAR] Tiket #{id_sel}", get_wib_now().strftime('%Y-%m-%d %H:%M:%S')))
                st.session_state.custom_keterangan[str(id_sel)] = ket_final
                save_data('keterangan_it.json', st.session_state.custom_keterangan)
                db.commit(); db.close(); st.rerun()

# --- 7. MENU LAINNYA ---
elif menu == "📦 Inventory Spareparts":
    try:
        from spareparts import show_sparepart_menu
        show_sparepart_menu(get_connection, get_wib_now, lambda a, d: None)
    except Exception as e: st.error(f"Gagal memuat modul spareparts: {e}")

elif menu == "Export & Reporting":
    st.markdown("### 📂 Export Data Tiket")
    db = get_connection(); df_ex = pd.read_sql("SELECT * FROM tickets", db); db.close()
    df_ex['Keterangan_IT'] = df_ex['id'].apply(lambda x: st.session_state.custom_keterangan.get(str(x), "-"))
    st.dataframe(df_ex, use_container_width=True)
    st.download_button("📥 DOWNLOAD CSV", df_ex.to_csv(index=False).encode('utf-8'), "IT_Report_Full.csv", use_container_width=True)

elif menu == "Security Log":
    st.markdown("### 🛡️ System Audit Log")
    st.dataframe(pd.DataFrame(st.session_state.get('audit_logs', [])), use_container_width=True)
