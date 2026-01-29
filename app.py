import streamlit as st
import pymysql
import pandas as pd
import certifi
import json
import os
from datetime import datetime, timedelta

# --- 1. KONFIGURASI & THEME ---
st.set_page_config(page_title="IT Kemasan", page_icon="🎫", layout="wide")

# --- 2. STORAGE VIRTUAL (AGAR DATA TIDAK HILANG) ---
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

# --- 4. CSS CUSTOM (RARE UI ENHANCEMENT) ---
st.markdown("""
    <style>
    /* Background Deep Ocean */
    .stApp { background: radial-gradient(circle at 50% 50%, #0f172a 0%, #020617 100%); }
    
    /* Glassmorphism Effect */
    div[data-testid="metric-container"], .stDataFrame, .stExpander, .stForm {
        background: rgba(255, 255, 255, 0.02) !important;
        backdrop-filter: blur(15px);
        border: 1px solid rgba(59, 130, 246, 0.2) !important;
        border-radius: 20px !important;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.8);
    }

    /* Rare Clock Styling */
    .clock-inner {
        background: rgba(15, 23, 42, 0.8); border-radius: 18px; padding: 15px; text-align: center;
        border: 1px solid #3b82f6; box-shadow: 0 0 15px rgba(59, 130, 246, 0.4);
    }
    .digital-clock {
        font-family: 'JetBrains Mono', monospace; color: #60a5fa;
        font-size: 32px; font-weight: 800; text-shadow: 0 0 10px rgba(96, 165, 250, 0.8);
    }

    /* Cyber Header Accent */
    .action-header {
        background: linear-gradient(90deg, rgba(59, 130, 246, 0.2) 0%, transparent 100%);
        padding: 15px; border-radius: 12px; border-left: 6px solid #3b82f6;
        color: #f8fafc; text-transform: uppercase; letter-spacing: 2px; margin: 25px 0;
    }

    /* Premium Buttons */
    .stButton>button {
        background: linear-gradient(135deg, #1d4ed8 0%, #1e40af 100%) !important;
        border: none !important; border-radius: 10px !important; color: white !important;
        font-weight: bold !important; transition: 0.3s all !important;
        box-shadow: 0 4px 15px rgba(29, 78, 216, 0.4) !important;
    }
    .stButton>button:hover {
        box-shadow: 0 0 20px rgba(59, 130, 246, 0.6) !important; transform: translateY(-2px);
    }

    /* Sidebar Image Rare Container */
    .sidebar-img-container {
        border-radius: 15px; overflow: hidden; border: 1px solid rgba(59, 130, 246, 0.3);
        margin-top: 20px; position: relative; background: #000;
    }
    .sidebar-img-tag {
        padding: 6px; background: rgba(59, 130, 246, 0.15); 
        text-align: center; font-size: 10px; color: #60a5fa; font-weight: bold;
        letter-spacing: 1px; border-top: 1px solid rgba(59, 130, 246, 0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. LOGIKA AUDIT LOG ---
if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = []

def add_log(action, details):
    waktu = get_wib_now().strftime('%H:%M:%S')
    st.session_state.audit_logs.insert(0, {
        "Waktu": waktu, "User": st.session_state.user_name.upper(),
        "Aksi": action, "Detail": details
    })

# --- 6. SIDEBAR MANAGEMENT ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False

with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: #60a5fa;'>🎫 IT-KEMASAN</h2>", unsafe_allow_html=True)
    
    wib = get_wib_now()
    st.markdown(f'''
        <div class="clock-inner">
            <div class="digital-clock">{wib.strftime("%H:%M:%S")}</div>
            <div style="color: #94a3b8; font-size: 13px;">{wib.strftime("%A, %d %b %Y")}</div>
        </div>
    ''', unsafe_allow_html=True)

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

        # --- TAMPILAN GAMBAR UI-MATCHING RARE ---
        st.markdown(f'''
            <div class="sidebar-img-container">
                <img src="https://images.unsplash.com/photo-1551288049-bbbda536339a?q=80&w=500&auto=format&fit=crop" 
                     style="width: 100%; display: block; filter: hue-rotate(180deg) brightness(0.7) contrast(1.2); opacity: 0.85;">
                <div class="sidebar-img-tag">📊 DATA ANALYTICS HUB</div>
            </div>
        ''', unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔒 LOGOUT", use_container_width=True):
            st.session_state.logged_in = False
            st.rerun()

# --- 7. MENU LOGIC ---
if not st.session_state.logged_in:
    menu = "Quick Input Mode"

if menu == "Dashboard Monitor" and st.session_state.logged_in:
    st.markdown("## 📊 Monitoring Center")
    db = get_connection()
    df = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", db)
    db.close()

    df['Keterangan'] = df['id'].apply(lambda x: st.session_state.custom_keterangan.get(str(x), "-"))
    df_display = df.rename(columns={'nama_user': 'Nama Teknisi', 'masalah': 'Problem', 'waktu': 'Waktu Laporan'})
    
    cols = list(df_display.columns)
    if 'Problem' in cols and 'Keterangan' in cols:
        p_idx = cols.index('Problem')
        cols.insert(p_idx + 1, cols.pop(cols.index('Keterangan')))
    df_display = df_display[cols]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Tickets", len(df_display))
    c2.metric("🔴 Open", len(df_display[df_display['status'] == 'Open']))
    c3.metric("🟡 In Progress", len(df_display[df_display['status'] == 'In Progress']))
    c4.metric("🟢 Solved", len(df_display[df_display['status'] == 'Solved']))

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    st.markdown("<div class='action-header'>⚡ Unified Action Center</div>", unsafe_allow_html=True)
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
            else: st.warning("Akses Input Dibatasi.")

    with col_ctrl:
        with st.expander("🔄 Update Status & Keterangan", expanded=True):
            if has_access("Edit") and not df.empty:
                id_up = st.selectbox("Pilih ID Tiket", df['id'].tolist())
                current_ket = st.session_state.custom_keterangan.get(str(id_up), "")
                new_ket = st.text_input("Keterangan IT (SSD/RAM/dll)", value=current_ket)
                st_up = st.selectbox("Set Status Database", ["Open", "In Progress", "Solved", "Closed"])
                
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    if st.button("💾 SIMPAN SEMUA", use_container_width=True):
                        st.session_state.custom_keterangan[str(id_up)] = new_ket
                        save_data('keterangan_it.json', st.session_state.custom_keterangan)
                        db = get_connection(); cur = db.cursor()
                        cur.execute("UPDATE tickets SET status=%s WHERE id=%s", (st_up, id_up))
                        db.close(); add_log("UPDATE", f"ID #{id_up}"); st.rerun()
                with c_btn2:
                    if st.button("🗑️ HAPUS TIKET", use_container_width=True):
                        if has_access("Hapus"):
                            db = get_connection(); cur = db.cursor()
                            cur.execute("DELETE FROM tickets WHERE id=%s", (id_up,))
                            if str(id_up) in st.session_state.custom_keterangan: del st.session_state.custom_keterangan[str(id_up)]
                            save_data('keterangan_it.json', st.session_state.custom_keterangan)
                            db.close(); add_log("DELETE", f"ID #{id_up}"); st.rerun()
                        else: st.error("Akses Hapus Dibatasi")

elif menu == "📦 Inventory Spareparts" and st.session_state.logged_in:
    try:
        from spareparts import show_sparepart_menu
        show_sparepart_menu(get_connection, get_wib_now, add_log)
    except Exception as e: st.error(f"Gagal memuat Spareparts: {e}")

elif menu == "Export & Reporting":
    st.markdown("## 📂 Export Data")
    db = get_connection()
    df_ex = pd.read_sql("SELECT * FROM tickets", db); db.close()
    df_ex['Keterangan_IT'] = df_ex['id'].apply(lambda x: st.session_state.custom_keterangan.get(str(x), "-"))
    st.dataframe(df_ex, use_container_width=True)
    st.download_button("📥 DOWNLOAD CSV", df_ex.to_csv(index=False).encode('utf-8'), "IT_Report.csv")

elif menu == "Security Log":
    st.markdown("## 🛡️ User Access Control")
    target_user = st.selectbox("Pilih User:", list(st.secrets["auth"].keys()))
    current_perms = st.session_state.user_permissions.get(target_user.lower(), ["Input"])
    new_perms = st.multiselect("Izin Akses:", ["Input", "Edit", "Hapus", "Export", "Security"], default=current_perms)
    if st.button("Update Hak Akses"):
        st.session_state.user_permissions[target_user.lower()] = new_perms
        save_data('permissions_it.json', st.session_state.user_permissions)
        st.success(f"Akses {target_user} diperbarui!")
    st.divider()
    st.markdown("### 📋 Audit Log")
    st.dataframe(pd.DataFrame(st.session_state.audit_logs), use_container_width=True)

elif menu == "Quick Input Mode":
    st.info("Silakan Login untuk akses menu lengkap.")
