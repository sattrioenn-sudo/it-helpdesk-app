import streamlit as st
import pymysql
import pandas as pd
import certifi
from datetime import datetime, timedelta
import io

# --- 1. CONFIG & THEME ---
st.set_page_config(page_title="IT Kemasan Pro", page_icon="🎫", layout="wide")

def get_wib_now():
    return datetime.now() + timedelta(hours=7)

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

# --- 2. CSS UI GLASSMORPHISM (WAJIB ADA BIAR GANTENG) ---
st.markdown("""
    <style>
    .stApp { background: radial-gradient(circle at top right, #0e1117, #1c2533); color: white; }
    div[data-testid="metric-container"] {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
        padding: 20px; border-radius: 15px;
    }
    .clock-box {
        background: linear-gradient(135deg, #1d4ed8 0%, #10b981 100%);
        padding: 15px; border-radius: 12px; text-align: center; margin-bottom: 20px;
    }
    .digital-clock { font-family: 'JetBrains Mono', monospace; color: white; font-size: 26px; font-weight: 800; }
    .action-header {
        background: rgba(255, 255, 255, 0.05); padding: 10px; border-radius: 10px;
        border-left: 5px solid #1d4ed8; margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. SESSION STATE & LOGGING ---
if 'audit_logs' not in st.session_state: st.session_state.audit_logs = []
def add_log(action, details):
    st.session_state.audit_logs.insert(0, {"Waktu": get_wib_now().strftime('%H:%M'), "User": st.session_state.get('user_name', 'GUEST'), "Aksi": action, "Detail": details})

# --- 4. SIDEBAR ---
with st.sidebar:
    st.markdown("<h2 style='text-align: center;'>🎫 IT-KEMASAN</h2>", unsafe_allow_html=True)
    st.markdown(f'<div class="clock-box"><div class="digital-clock">{get_wib_now().strftime("%H:%M:%S")}</div></div>', unsafe_allow_html=True)
    
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False

    if st.session_state.logged_in:
        st.write(f"Logged in as: **{st.session_state.user_name.upper()}**")
        menu = st.selectbox("📂 MENU", ["Dashboard Monitor", "Analytics", "Export Data", "Log System", "Buat Tiket"])
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.rerun()
    else:
        menu = "Buat Tiket"
        u = st.text_input("Username")
        p = st.text_input("Password", type="password")
        if st.button("Login", type="primary", use_container_width=True):
            if u in st.secrets["auth"] and p == st.secrets["auth"][u]:
                st.session_state.logged_in = True
                st.session_state.user_name = u
                st.rerun()

# --- 5. LOGIC MENU ---
db = get_connection()

if menu == "Dashboard Monitor" and st.session_state.logged_in:
    st.header("📊 Monitoring Center")
    df = pd.read_sql("SELECT * FROM tickets ORDER BY id DESC", db)
    
    # Perbaikan None
    if 'waktu_selesai' in df.columns:
        df['waktu_selesai'] = df.apply(lambda r: get_wib_now().strftime('%Y-%m-%d %H:%M') if (r['status'] == 'Solved' and (r['waktu_selesai'] is None or str(r['waktu_selesai']) == 'None')) else r['waktu_selesai'], axis=1)

    # Rename untuk Tampilan
    df_view = df.rename(columns={'nama_user': 'Nama Teknisi'})
    
    # Filter Pencarian
    search = st.text_input("🔍 Cari data...")
    if search:
        df_view = df_view[df_view.apply(lambda r: r.astype(str).str.contains(search, case=False).any(), axis=1)]

    st.dataframe(df_view, use_container_width=True, hide_index=True)

    # Action Center (Update & Hapus)
    st.markdown("<div class='action-header'>⚡ Quick Action</div>", unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        with st.expander("🔄 Update Status"):
            id_up = st.selectbox("Pilih ID", df['id'].tolist())
            st_up = st.selectbox("Status", ["Open", "In Progress", "Solved", "Closed"])
            if st.button("Update"):
                cur = db.cursor()
                if st_up == "Solved":
                    cur.execute("UPDATE tickets SET status=%s, waktu_selesai=%s WHERE id=%s", (st_up, get_wib_now().strftime('%Y-%m-%d %H:%M:%S'), id_up))
                else:
                    cur.execute("UPDATE tickets SET status=%s WHERE id=%s", (st_up, id_up))
                st.toast("Updated!")
                st.rerun()
    with c2:
        with st.expander("🗑️ Hapus Tiket"):
            id_del = st.selectbox("Pilih ID Hapus", df['id'].tolist())
            if st.button("Hapus Data", type="secondary"):
                cur = db.cursor()
                cur.execute("DELETE FROM tickets WHERE id=%s", (id_del))
                st.toast("Deleted!")
                st.rerun()

elif menu == "Analytics" and st.session_state.logged_in:
    st.header("📈 Statistik")
    df = pd.read_sql("SELECT * FROM tickets", db)
    if not df.empty:
        st.subheader("Beban Kerja Teknisi")
        st.bar_chart(df['nama_user'].value_counts())
        st.subheader("Masalah per Cabang")
        st.line_chart(df['cabang'].value_counts())

elif menu == "Buat Tiket":
    st.header("📝 Lapor Kendala IT")
    with st.form("tiket_baru"):
        nama = st.text_input("Nama Anda")
        cbng = st.selectbox("Cabang", st.secrets["master"]["daftar_cabang"])
        mslh = st.text_area("Detail Kendala")
        prio = st.select_slider("Prioritas", ["Low", "Medium", "High"])
        if st.form_submit_button("Kirim Laporan"):
            cur = db.cursor()
            cur.execute("INSERT INTO tickets (nama_user, cabang, masalah, prioritas, status) VALUES (%s,%s,%s,%s,'Open')", (nama, cbng, mslh, prio))
            st.success("Terkirim!")
            st.balloons()

db.close()
