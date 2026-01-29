app.py : import streamlit as st
import pymysql
import pandas as pd
import certifi
from datetime import datetime, timedelta
import io
# IMPORT MODUL SPAREPART BARU
from spareparts import show_sparepart_menu

# --- 1. KONFIGURASI & THEME ---
st.set_page_config(page_title="IT Kemasan", page_icon="🎫", layout="wide")

# --- 2. LOGIKA PERSISTENT SESSION ---
@st.cache_resource
def get_auth_state():
    return {"logged_in": False, "user_name": ""}

auth = get_auth_state()
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = auth["logged_in"]
if 'user_name' not in st.session_state:
    st.session_state.user_name = auth["user_name"]

# --- 3. FUNGSI WAKTU WIB ---
def get_wib_now():
    return datetime.utcnow() + timedelta(hours=7)

# --- 4. DATABASE CONNECTION ---
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

# --- 5. CSS CUSTOM (PREMIUM UI) ---
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top right, #0e1117, #1c2533); }
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 20px; border-radius: 15px;
        color: white !important;
    }
    section[data-testid="stSidebar"] {
        background-color: #0e1117 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.1);
    }
    .clock-box {
        background: linear-gradient(135deg, #1d4ed8 0%, #10b981 100%);
        padding: 15px; border-radius: 12px; text-align: center;
        margin-bottom: 25px; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    }
    .digital-clock {
        font-family: 'JetBrains Mono', monospace;
        color: white; font-size: 28px; font-weight: 800;
    }
    .stDataFrame { border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 15px; }
    .action-header {
        background: rgba(255, 255, 255, 0.05);
        padding: 10px 20px; border-radius: 10px;
        border-left: 5px solid #1d4ed8; margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 6. LOGIKA AUDIT LOG ---
if 'audit_logs' not in st.session_state:
    st.session_state.audit_logs = []

def add_log(action, details):
    waktu = get_wib_now().strftime('%H:%M:%S')
    st.session_state.audit_logs.insert(0, {
        "Waktu": waktu,
        "User": st.session_state.user_name.upper() if st.session_state.user_name else "GUEST",
        "Aksi": action, "Detail": details
    })

# --- 7. SIDEBAR MANAGEMENT ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: white;'>🎫 IT-Kemasan Group</h1>", unsafe_allow_html=True)
    wib = get_wib_now()
    st.markdown(f"""
        <div class="clock-box">
            <div class="digital-clock">{wib.strftime('%H:%M:%S')}</div>
            <div style="color: white; font-size: 12px; opacity: 0.9;">{wib.strftime('%A, %d %B %Y')}</div>
        </div>
    """, unsafe_allow_html=True)

    if not st.session_state.logged_in:
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("🔓 SIGN IN", use_container_width=True, type="primary"):
            if u in st.secrets["auth"] and p == st.secrets["auth"][u]:
                st.session_state.logged_in = True
                st.session_state.user_name = u
                auth["logged_in"] = True
                auth["user_name"] = u
                add_log("LOGIN", "Masuk Dashboard")
                st.rerun()
            else:
                st.error("Credential Salah!")
    else:
        st.markdown(f"<p style='text-align: center;'>Operator: <b>{st.session_state.user_name.upper()}</b></p>", unsafe_allow_html=True)
        # TAMBAHKAN MENU SPAREPART DI SINI
        menu = st.selectbox("📂 MAIN MENU", ["Dashboard Monitor", "Sparepart Management", "Export & Reporting", "Security Log"])
        if st.button("🔒 LOGOUT", use_container_width=True):
            st.session_state.logged_in = False
            auth["logged_in"] = False
            auth["user_name"] = ""
            st.rerun()

# --- 8. MENU ROUTING ---
if not st.session_state.logged_in:
    menu = "Quick Input Mode"

if menu == "Dashboard Monitor" and st.session_state.logged_in:
    st.markdown("## 📊 Monitoring Center")
    db = get_connection()
    df = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", db)
    db.close()

    if 'waktu_selesai' in df.columns:
        df['waktu_selesai'] = df.apply(
            lambda r: get_wib_now().strftime('%Y-%m-%d %H:%M:%S') if (r['status'] == 'Solved' and (r['waktu_selesai'] is None or str(r['waktu_selesai']) == 'None')) else r['waktu_selesai'],
            axis=1
        )

    df_display = df.rename(columns={'nama_user': 'Nama Teknisi', 'masalah': 'Problem', 'waktu': 'Waktu Laporan'})
    q = st.text_input("🔍 Search Console", placeholder="Cari...")
    if q: df_display = df_display[df_display.apply(lambda r: r.astype(str).str.contains(q, case=False).any(), axis=1)]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Tickets", len(df_display))
    c2.metric("🔴 Open", len(df_display[df_display['status'] == 'Open']))
    c3.metric("🟡 In Progress", len(df_display[df_display['status'] == 'In Progress']))
    c4.metric("🟢 Solved", len(df_display[df_display['status'] == 'Solved']))

    st.dataframe(df_display, use_container_width=True, hide_index=True)

    st.markdown("<div class='action-header'>⚡ Unified Action & Input Center</div>", unsafe_allow_html=True)
    col_input, col_ctrl = st.columns([1.2, 1])
    
    with col_input:
        with st.expander("🆕 Input Tiket Baru (Quick Entry)", expanded=True):
            with st.form("form_quick_entry", clear_on_submit=True):
                u_in = st.text_input("Nama Lengkap")
                c_in = st.selectbox("Lokasi Cabang", st.secrets["master"]["daftar_cabang"])
                i_in = st.text_area("Deskripsi Kendala")
                p_in = st.select_slider("Urgensi", ["Low", "Medium", "High"])
                if st.form_submit_button("KIRIM LAPORAN 🚀", use_container_width=True):
                    if u_in and i_in:
                        db = get_connection(); cur = db.cursor()
                        now_wib = get_wib_now().strftime('%Y-%m-%d %H:%M:%S')
                        cur.execute("INSERT INTO tickets (nama_user, cabang, masalah, prioritas, status, waktu) VALUES (%s,%s,%s,%s,'Open',%s)", (u_in, c_in, i_in, p_in, now_wib))
                        db.close()
                        add_log("INPUT", f"Tiket Baru oleh {u_in}")
                        st.toast(f"✅ Tiket {u_in} dikirim!", icon='🚀')
                        st.rerun()

    with col_ctrl:
        with st.expander("🔄 Update Status Ticket"):
            if not df.empty:
                id_up = st.selectbox("Pilih ID", df['id'].tolist(), key="up_select")
                st_up = st.selectbox("Set Status", ["Open", "In Progress", "Solved", "Closed"])
                if st.button("SIMPAN PERUBAHAN", type="primary", use_container_width=True):
                    db = get_connection(); cur = db.cursor()
                    if st_up == "Solved":
                        waktu_fix = get_wib_now().strftime('%Y-%m-%d %H:%M:%S')
                        cur.execute("UPDATE tickets SET status=%s, waktu_selesai=%s WHERE id=%s", (st_up, waktu_fix, id_up))
                    else:
                        cur.execute("UPDATE tickets SET status=%s WHERE id=%s", (st_up, id_up))
                    db.close(); add_log("UPDATE", f"ID #{id_up} ke {st_up}"); st.toast("✅ Tersimpan!"); st.rerun()
        
        with st.expander("🗑️ Hapus Tiket"):
            if not df.empty:
                id_del = st.selectbox("Pilih ID", df['id'].tolist(), key="del_select")
                if st.button("KONFIRMASI HAPUS", use_container_width=True):
                    db = get_connection(); cur = db.cursor()
                    cur.execute("DELETE FROM tickets WHERE id=%s", (id_del))
                    db.close(); add_log("DELETE", f"Hapus #{id_del}"); st.toast("🗑️ Terhapus"); st.rerun()

# --- ROUTING MENU SPAREPART ---
elif menu == "Sparepart Management" and st.session_state.logged_in:
    show_sparepart_menu(get_connection, get_wib_now, add_log)

elif menu == "Export & Reporting" and st.session_state.logged_in:
    st.markdown("## 📂 Financial & Operations Report")
    db = get_connection(); df_ex = pd.read_sql("SELECT * FROM tickets", db); db.close()
    st.dataframe(df_ex, use_container_width=True)
    csv = df_ex.to_csv(index=False).encode('utf-8')
    st.download_button("📥 DOWNLOAD CSV", csv, f"Report_{get_wib_now().strftime('%Y%m%d')}.csv", "text/csv", use_container_width=True)

elif menu == "Security Log" and st.session_state.logged_in:
    st.markdown("## 🛡️ Security Audit Log")
    if st.session_state.audit_logs:
        st.dataframe(pd.DataFrame(st.session_state.audit_logs), use_container_width=True, hide_index=True)
    else: st.info("Kosong.")

elif menu == "Quick Input Mode":
    st.markdown("<h1 style='text-align: center;'>📝 Form Laporan IT</h1>", unsafe_allow_html=True)
    _, c2, _ = st.columns([1, 2, 1])
    with c2:
        with st.form("form_guest", clear_on_submit=True):
            user = st.text_input("Nama Lengkap")
            cabang = st.selectbox("Lokasi Cabang", st.secrets["master"]["daftar_cabang"])
            issue = st.text_area("Deskripsi Kendala")
            prio = st.select_slider("Urgensi", ["Low", "Medium", "High"])
            if st.form_submit_button("KIRIM LAPORAN 🚀", use_container_width=True):
                if user and issue:
                    db = get_connection(); cur = db.cursor(); now_wib = get_wib_now().strftime('%Y-%m-%d %H:%M:%S')
                    cur.execute("INSERT INTO tickets (nama_user, cabang, masalah, prioritas, status, waktu) VALUES (%s,%s,%s,%s,'Open',%s)", (user, cabang, issue, prio, now_wib))
                    db.close(); st.success("✅ Laporan diterima.")
