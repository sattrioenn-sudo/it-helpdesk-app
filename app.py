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

# --- 4. CSS CUSTOM ---
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at 50% 50%, #0f172a 0%, #020617 100%); }
    div[data-testid="metric-container"], .stDataFrame, .stExpander, .stForm {
        background: rgba(255, 255, 255, 0.01) !important;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 20px !important;
    }
    .stButton>button {
        background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%) !important;
        color: white !important; font-weight: bold !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. LOGIKA AUDIT LOG ---
if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = []

def add_log(action, details):
    waktu = get_wib_now().strftime('%H:%M:%S')
    st.session_state.audit_logs.insert(0, {"Waktu": waktu, "User": st.session_state.user_name.upper(), "Aksi": action, "Detail": details})

# --- 6. SIDEBAR MANAGEMENT ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #60a5fa;'>🎫 IT-KEMASAN</h2>", unsafe_allow_html=True)
    wib = get_wib_now()
    if not st.session_state.logged_in:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("🔓 ACCESS SYSTEM", use_container_width=True):
            if u in st.secrets["auth"] and p == st.secrets["auth"][u]:
                st.session_state.logged_in = True
                st.session_state.user_name = u
                st.rerun()
    else:
        st.markdown(f"<p style='text-align: center;'>Operator: <span style='color:#60a5fa;'>{st.session_state.user_name.upper()}</span></p>", unsafe_allow_html=True)
        menu_list = ["Dashboard Monitor", "📦 Inventory Spareparts"]
        if has_access("Export"): menu_list.append("Export & Reporting")
        if has_access("Security"): menu_list.append("Security Log")
        menu = st.selectbox("📂 NAVIGATION", menu_list)
        if st.button("🔒 LOGOUT", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

# --- 7. MENU LOGIC ---
if not st.session_state.logged_in:
    menu = "Quick Input Mode"

# --- DASHBOARD MONITOR ---
if menu == "Dashboard Monitor" and st.session_state.logged_in:
    st.markdown("## 📊 Monitoring Center")
    db = get_connection()
    try:
        df = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", db)
        query_sp = "SELECT nama_part, kode_part, kategori, SUM(jumlah) as total_stok FROM spareparts WHERE keterangan LIKE '%%[APPROVED]%%' GROUP BY nama_part, kode_part, kategori HAVING total_stok > 0"
        df_stok_ready = pd.read_sql(query_sp, db)
    except:
        df = pd.DataFrame()
        df_stok_ready = pd.DataFrame()
    finally: db.close()

    if not df.empty:
        df['Keterangan'] = df['id'].apply(lambda x: st.session_state.custom_keterangan.get(str(x), "-"))
        df_display = df.rename(columns={'nama_user': 'Nama Teknisi', 'masalah': 'Problem', 'waktu': 'Waktu Laporan'})
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        st.markdown("### ⚡ Action Hub")
        col_input, col_ctrl = st.columns([1.2, 1])
        
        with col_input:
            with st.expander("🆕 Input Tiket Baru", expanded=True):
                if has_access("Input"):
                    with st.form("form_quick_entry", clear_on_submit=True):
                        u_in = st.text_input("Nama Lengkap")
                        c_in = st.selectbox("Lokasi Cabang", st.secrets["master"]["daftar_cabang"])
                        i_in = st.text_area("Deskripsi Kendala")
                        p_in = st.select_slider("Urgensi", ["Low", "Medium", "High"])
                        if st.form_submit_button("KIRIM LAPORAN 🚀", use_container_width=True):
                            if u_in and i_in:
                                db = get_connection(); cur = db.cursor()
                                cur.execute("INSERT INTO tickets (nama_user, cabang, masalah, prioritas, status, waktu) VALUES (%s,%s,%s,%s,'Open',%s)", (u_in, c_in, i_in, p_in, get_wib_now().strftime('%Y-%m-%d %H:%M:%S')))
                                db.close(); add_log("INPUT", u_in); st.rerun()

        with col_ctrl:
            with st.expander("🔄 Update & Sparepart Link", expanded=True):
                if has_access("Edit"):
                    id_up = st.selectbox("Pilih ID Tiket", df['id'].tolist())
                    st_up = st.selectbox("Set Status", ["Open", "In Progress", "Solved", "Closed"])
                    use_sp = st.checkbox("Ganti Hardware?")
                    item_terpilih, qty_out = None, 0
                    if use_sp and not df_stok_ready.empty:
                        df_stok_ready['label'] = df_stok_ready['nama_part'] + " (Sisa: " + df_stok_ready['total_stok'].astype(str) + ")"
                        pilihan = st.selectbox("Stok Gudang", df_stok_ready['label'].tolist())
                        item_terpilih = df_stok_ready[df_stok_ready['label'] == pilihan].iloc[0]
                        qty_out = st.number_input("Jumlah", min_value=1, max_value=int(item_terpilih['total_stok']), value=1)
                    
                    new_ket = st.text_input("Keterangan IT", value=st.session_state.custom_keterangan.get(str(id_up), ""))
                    if st.button("💾 SIMPAN DATA", use_container_width=True):
                        db = get_connection(); cur = db.cursor()
                        try:
                            cur.execute("UPDATE tickets SET status=%s WHERE id=%s", (st_up, id_up))
                            ket_final = new_ket
                            if use_sp and item_terpilih is not None:
                                info_sp = f" [OUT: {item_terpilih['nama_part']} x{qty_out}]"
                                if info_sp not in ket_final: ket_final += info_sp
                                cur.execute("INSERT INTO spareparts (nama_part, kode_part, kategori, jumlah, keterangan, waktu) VALUES (%s,%s,%s,%s,%s,%s)",
                                           (item_terpilih['nama_part'], item_terpilih['kode_part'], item_terpilih['kategori'], -qty_out, f"[APPROVED] [KELUAR] | Ticket #{id_up}", get_wib_now().strftime('%Y-%m-%d %H:%M:%S')))
                            st.session_state.custom_keterangan[str(id_up)] = ket_final
                            save_data('keterangan_it.json', st.session_state.custom_keterangan)
                            db.commit(); add_log("UPDATE", f"Ticket #{id_up}"); st.success("Updated!"); st.rerun()
                        except Exception as e: st.error(e)
                        finally: db.close()

# --- INVENTORY ---
elif menu == "📦 Inventory Spareparts" and st.session_state.logged_in:
    try:
        from spareparts import show_sparepart_menu
        show_sparepart_menu(get_connection, get_wib_now, add_log)
    except Exception as e: st.error(f"Gagal memuat Spareparts: {e}")

# --- EXPORT ---
elif menu == "Export & Reporting":
    st.markdown("## 📂 Export Data Management")
    db = get_connection()
    df_ex = pd.read_sql("SELECT * FROM tickets", db); db.close()
    df_ex['Keterangan_IT'] = df_ex['id'].apply(lambda x: st.session_state.custom_keterangan.get(str(x), "-"))
    
    st.markdown("### Preview Data Tiket")
    st.dataframe(df_ex, use_container_width=True, hide_index=True)
    
    col_dl1, col_dl2 = st.columns(2)
    with col_dl1:
        st.download_button("📥 DOWNLOAD CSV (TIKET)", df_ex.to_csv(index=False).encode('utf-8'), "IT_Tickets_Report.csv", use_container_width=True)
    
    with col_dl2:
        db = get_connection()
        df_sp_ex = pd.read_sql("SELECT * FROM spareparts", db); db.close()
        st.download_button("📥 DOWNLOAD CSV (INVENTORY)", df_sp_ex.to_csv(index=False).encode('utf-8'), "IT_Inventory_Report.csv", use_container_width=True)

# --- SECURITY ---
elif menu == "Security Log":
    st.markdown("## 🛡️ Security & Access Control")
    if has_access("Security"):
        t_user = st.selectbox("Pilih User untuk Ubah Izin:", list(st.secrets["auth"].keys()))
        c_perms = st.session_state.user_permissions.get(t_user.lower(), ["Input"])
        n_perms = st.multiselect("Izin Akses:", ["Input", "Edit", "Hapus", "Export", "Security"], default=c_perms)
        if st.button("Update Izin User"):
            st.session_state.user_permissions[t_user.lower()] = n_perms
            save_data('permissions_it.json', st.session_state.user_permissions)
            st.success(f"Izin {t_user} diperbarui!")
    
    st.divider()
    st.markdown("### 📋 System Audit Log")
    if st.session_state.audit_logs:
        st.dataframe(pd.DataFrame(st.session_state.audit_logs), use_container_width=True, hide_index=True)
    else:
        st.info("Belum ada log aktivitas.")

elif menu == "Quick Input Mode":
    st.info("Silakan Login untuk akses menu lengkap.")
