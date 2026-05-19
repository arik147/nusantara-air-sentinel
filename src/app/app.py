# Presentation Layer: Streamlit Dashboard App
# Technology: Python, Streamlit, Plotly, Pandas, Supabase Client

import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
from supabase import create_client, Client

# Muat variabel lingkungan jika berjalan secara lokal
load_dotenv()

# ==========================================
# 1. SETUP PAGE CONFIG & TEMA
# ==========================================
st.set_page_config(
    page_title="Nusantara Air Sentinel",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk gaya visual premium (Glassmorphism & Card style)
st.markdown("""
<style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
    
    /* Font & Background utama */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
        font-family: 'Inter', sans-serif !important;
    }
    .stApp {
        background: linear-gradient(160deg, #0b1120 0%, #162036 50%, #0f1b2d 100%);
        color: #e2e8f0;
    }
    
    /* ===== UNIFIED DARK SIDEBAR ===== */
    section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f172a 0%, #1a2540 100%) !important;
        border-right: 1px solid rgba(255,255,255,0.06);
    }
    section[data-testid="stSidebar"] * {
        color: #cbd5e1 !important;
    }
    
    /* Sidebar Selectbox (dropdown kota) */
    section[data-testid="stSidebar"] [data-baseweb="select"] {
        border: none !important;
        background-color: transparent !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="select"] > div {
        background-color: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid rgba(56, 189, 248, 0.2) !important;
        border-radius: 8px !important;
        color: #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="popover"] {
        background-color: #1e293b !important;
        border: 1px solid rgba(56, 189, 248, 0.15) !important;
    }
    section[data-testid="stSidebar"] [data-baseweb="menu"] {
        background-color: #1e293b !important;
    }
    section[data-testid="stSidebar"] [role="option"] {
        background-color: #1e293b !important;
        color: #cbd5e1 !important;
    }
    section[data-testid="stSidebar"] [role="option"]:hover {
        background-color: rgba(56, 189, 248, 0.15) !important;
    }
    section[data-testid="stSidebar"] [aria-selected="true"] {
        background-color: rgba(56, 189, 248, 0.2) !important;
    }
    
    /* Sidebar Radio Buttons */
    section[data-testid="stSidebar"] .stRadio > div {
        background-color: transparent !important;
    }
    section[data-testid="stSidebar"] .stRadio label {
        color: #94a3b8 !important;
        transition: color 0.15s ease;
    }
    section[data-testid="stSidebar"] .stRadio label:hover {
        color: #e2e8f0 !important;
    }
    section[data-testid="stSidebar"] .stRadio [data-testid="stMarkdownContainer"] {
        color: #cbd5e1 !important;
    }
    
    /* Sidebar Button (Tarik Data Terbaru) */
    section[data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.15) 0%, rgba(14, 165, 233, 0.2) 100%) !important;
        border: 1px solid rgba(56, 189, 248, 0.3) !important;
        color: #38bdf8 !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        padding: 8px 16px !important;
        transition: all 0.2s ease !important;
    }
    section[data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(135deg, rgba(56, 189, 248, 0.25) 0%, rgba(14, 165, 233, 0.35) 100%) !important;
        border-color: rgba(56, 189, 248, 0.5) !important;
        box-shadow: 0 4px 16px rgba(56, 189, 248, 0.15) !important;
        transform: translateY(-1px);
    }
    
    /* Sidebar Divider */
    section[data-testid="stSidebar"] hr {
        border-color: rgba(255,255,255,0.06) !important;
    }
    
    /* Sidebar Info Box (Arsitektur) */
    section[data-testid="stSidebar"] [data-testid="stAlert"] {
        background-color: rgba(56, 189, 248, 0.06) !important;
        border: 1px solid rgba(56, 189, 248, 0.12) !important;
        border-radius: 10px !important;
        color: #94a3b8 !important;
    }
    
    /* Sidebar Labels */
    section[data-testid="stSidebar"] .stSelectbox label,
    section[data-testid="stSidebar"] [data-testid="stSlider"] label,
    section[data-testid="stSidebar"] .stRadio > label {
        color: #94a3b8 !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
    }
    
    /* Jarak antara Label Slider dan Slider-nya */
    section[data-testid="stSidebar"] [data-testid="stSlider"] [data-testid="stWidgetLabel"] {
        margin-bottom: 14px !important;
    }
    
    /* ===== METRIC CARD ===== */
    .metric-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 14px;
        padding: 20px;
        box-shadow: 0 4px 24px rgba(0, 0, 0, 0.25);
        backdrop-filter: blur(12px);
        -webkit-backdrop-filter: blur(12px);
        margin-bottom: 12px;
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
        
        /* Flexbox for equal height and layout alignment */
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        min-height: 165px;
        height: auto;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 32px rgba(56, 189, 248, 0.12);
        border-color: rgba(56, 189, 248, 0.2);
    }
    
    @media (max-width: 768px) {
        .metric-card {
            min-height: 140px;
            padding: 15px;
        }
    }
    
    /* Responsive Pollutants Grid */
    .pollutants-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 10px;
        width: 100%;
        margin-bottom: 12px;
    }
    
    @media (max-width: 1200px) {
        .pollutants-grid {
            grid-template-columns: repeat(2, 1fr);
        }
    }
    
    @media (max-width: 480px) {
        .pollutants-grid {
            grid-template-columns: 1fr;
        }
    }
    
    /* Polutan Card */
    .pollutant-card {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 10px;
        padding: 14px 10px;
        text-align: center;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .pollutant-card:hover {
        transform: translateY(-2px);
        border-color: rgba(56, 189, 248, 0.15);
    }
    
    /* Rekomendasi box styling */
    .rec-box {
        border-radius: 12px;
        padding: 18px;
        margin-top: 10px;
        border-left: 4px solid;
        backdrop-filter: blur(6px);
    }
    .rec-good {
        background-color: rgba(34, 197, 94, 0.1);
        border-left-color: #22c55e;
        color: #86efac;
    }
    .rec-moderate {
        background-color: rgba(234, 179, 8, 0.1);
        border-left-color: #eab308;
        color: #fde047;
    }
    .rec-sensitive {
        background-color: rgba(249, 115, 22, 0.1);
        border-left-color: #f97316;
        color: #fdba74;
    }
    .rec-unhealthy {
        background-color: rgba(239, 68, 68, 0.1);
        border-left-color: #ef4444;
        color: #fca5a5;
    }
    .rec-very-unhealthy {
        background-color: rgba(168, 85, 247, 0.1);
        border-left-color: #a855f7;
        color: #d8b4fe;
    }
    .rec-hazardous {
        background-color: rgba(127, 29, 29, 0.2);
        border-left-color: #7f1d1d;
        color: #fda4af;
    }
    
    /* Section Headers */
    .section-header {
        font-size: 1.25rem;
        font-weight: 700;
        color: #f1f5f9;
        padding-bottom: 8px;
        margin-bottom: 16px;
        border-bottom: 2px solid rgba(56, 189, 248, 0.2);
        letter-spacing: -0.01em;
    }
    
    /* Beautiful Custom Streamlit Tabs */
    [data-testid="stTabs"] {
        border-bottom: 1px solid rgba(255, 255, 255, 0.08) !important;
        gap: 8px !important;
        margin-bottom: 20px !important;
    }
    [data-testid="stTabs"] [role="tab"] {
        background-color: rgba(30, 41, 59, 0.4) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        border-radius: 8px 8px 0 0 !important;
        padding: 8px 20px !important;
        color: #94a3b8 !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
        transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1) !important;
        height: 42px !important;
        box-shadow: none !important;
    }
    [data-testid="stTabs"] [role="tab"]:hover {
        background-color: rgba(56, 189, 248, 0.08) !important;
        color: #38bdf8 !important;
        border-color: rgba(56, 189, 248, 0.2) !important;
    }
    [data-testid="stTabs"] [role="tab"][aria-selected="true"] {
        background-color: rgba(56, 189, 248, 0.15) !important;
        color: #38bdf8 !important;
        font-weight: 700 !important;
        border-color: rgba(56, 189, 248, 0.3) rgba(56, 189, 248, 0.3) transparent rgba(56, 189, 248, 0.3) !important;
        border-bottom: 2px solid #38bdf8 !important;
        box-shadow: 0 -4px 12px rgba(56, 189, 248, 0.05) !important;
    }
    
    /* Footer */
    .app-footer {
        text-align: center;
        padding: 24px 0 12px 0;
        margin-top: 32px;
        border-top: 1px solid rgba(255,255,255,0.06);
        color: #475569;
        font-size: 0.8rem;
    }
    .app-footer a { color: #38bdf8; text-decoration: none; }
    .app-footer a:hover { text-decoration: underline; }
    
    /* Hide Streamlit default elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ==========================================
# 2. KONEKSI KE SUPABASE DATABASE
# ==========================================
@st.cache_resource
def init_supabase() -> Client:
    """Menginisialisasi klien Supabase menggunakan st.secrets atau environment variables."""
    url = None
    key = None
    
    # Coba ambil dari st.secrets (Streamlit Cloud)
    try:
        url = st.secrets.get("SUPABASE_URL")
        key = st.secrets.get("SUPABASE_KEY")
    except Exception:
        # Jika st.secrets kosong/tidak ada file secrets.toml, abaikan dan gunakan env variables secara lokal
        pass
        
    # Jika tidak ada di st.secrets, ambil dari os.getenv (.env lokal)
    if not url:
        url = os.getenv("SUPABASE_URL")
    if not key:
        key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        st.error("[-] Konfigurasi kredensial Supabase tidak ditemukan. Pastikan Anda telah menaruhnya di secrets Streamlit atau file .env!")
        st.stop()
        
    return create_client(url, key)

try:
    supabase = init_supabase()
except Exception as e:
    st.error(f"Gagal menghubungkan ke Supabase: {str(e)}")
    st.stop()

# ==========================================
# 3. KUMPULAN FUNGSI QUERY DATA (DENGAN CACHING)
# ==========================================
# Cache kadaluarsa setelah 10 menit (600 detik) untuk menghemat penggunaan API/DB gratis
@st.cache_data(ttl=600)
def load_all_metrics() -> pd.DataFrame:
    """Menarik semua data historis dari database Supabase."""
    try:
        response = supabase.table("weather_air_metrics").select("*").order("recorded_at", desc=True).execute()
        df = pd.DataFrame(response.data)
        if not df.empty:
            # Ubah string timestamp menjadi tipe datetime dengan timezone Jakarta (WIB)
            df['recorded_at'] = pd.to_datetime(df['recorded_at'])
            df['recorded_local'] = df['recorded_at'].dt.tz_convert('Asia/Jakarta')
        return df
    except Exception as e:
        st.error(f"Error saat memuat data dari database: {str(e)}")
        return pd.DataFrame()

# Trik untuk menyegarkan cache data
def refresh_data():
    st.cache_data.clear()

# ==========================================
# 4. SIDEBAR - FILTER & DOKUMENTASI PORTOFOLIO
# ==========================================
st.sidebar.markdown("<h2 style='text-align: center; font-size: 1.5rem; letter-spacing: -0.02em;'>Kontrol & Filter</h2>", unsafe_allow_html=True)

# Load data awal
df_raw = load_all_metrics()

if df_raw.empty:
    st.warning("⚠️ Database masih kosong atau belum terhubung! Silakan jalankan skrip ETL Anda untuk memasukkan data pertama.")
    if st.sidebar.button("🔄 Segarkan Database"):
        refresh_data()
        st.rerun()
    st.stop()

# Filter Parameter Data
all_cities = sorted(df_raw['city'].unique())
selected_city = st.sidebar.selectbox("Pilih Kota Pantauan", all_cities)

time_options = {
    "1 Hari Terakhir": 1,
    "3 Hari Terakhir": 3,
    "7 Hari Terakhir": 7,
    "30 Hari Terakhir": 30,
    "Tampilkan Semua": 365
}
selected_time_label = st.sidebar.select_slider(
    "Rentang Analisis Waktu",
    options=list(time_options.keys()),
    value="3 Hari Terakhir"
)
days_threshold = time_options[selected_time_label]

# Tombol Sinkronisasi Manual (Tindakan Administratif Sistem)
st.sidebar.markdown("---")
if st.sidebar.button("Tarik Data Terbaru", use_container_width=True):
    refresh_data()
    st.toast("Data berhasil disegarkan dari Supabase!", icon="🚀")
    st.rerun()


# ==========================================
# 5. PENGOLAHAN DATA & FILTERING
# ==========================================
# Filter data berdasarkan kota terpilih
df_city = df_raw[df_raw['city'] == selected_city].copy()

# Filter berdasarkan rentang waktu
cutoff_date = datetime.now(pytz.utc) - timedelta(days=days_threshold)
df_filtered = df_city[df_city['recorded_at'] >= cutoff_date].copy()
df_filtered = df_filtered.sort_values(by='recorded_at')  # Urutkan kronologis untuk grafik

# Tentukan interval (dtick) dan format label (tickformat) sumbu X berdasarkan rentang waktu
if days_threshold <= 1:
    # 1 Hari Terakhir -> Interval per 3 jam
    chart_dtick = 3 * 3600 * 1000  # 3 jam dalam milidetik
    chart_tickformat = "%H:%M\n%d %b"
elif days_threshold <= 3:
    # 3 Hari Terakhir -> Interval per 6 jam
    chart_dtick = 6 * 3600 * 1000  # 6 jam dalam milidetik
    chart_tickformat = "%H:%M\n%d %b"
elif days_threshold <= 7:
    # 7 Hari Terakhir -> Interval per 12 jam
    chart_dtick = 12 * 3600 * 1000  # 12 jam dalam milidetik
    chart_tickformat = "%H:%M\n%d %b"
elif days_threshold <= 30:
    # 30 Hari Terakhir -> Interval per 2 hari
    chart_dtick = 2 * 24 * 3600 * 1000  # 2 hari dalam milidetik
    chart_tickformat = "%d %b"
else:
    # Semua data -> Interval per 7 hari
    chart_dtick = 7 * 24 * 3600 * 1000  # 7 hari dalam milidetik
    chart_tickformat = "%d %b"

# Dapatkan data realtime terkini untuk kota terpilih
latest_data = df_city.iloc[0]

# ==========================================
# 6. HEADER UTAMA
# ==========================================
col_title, col_status = st.columns([4, 1])
with col_title:
    st.markdown(f"<h1 style='margin-bottom:0px; font-size: 2.8rem; font-weight: 800; letter-spacing: -0.03em;'>Nusantara Air Sentinel</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #94a3b8; font-size:1.1rem;'>Platform Pemantauan Cuaca & Kualitas Udara Real-Time 52 Kota: <b>{latest_data['city']}, {latest_data['country']}</b></p>", unsafe_allow_html=True)

with col_status:
    # Waktu Update WIB
    wib_tz = pytz.timezone('Asia/Jakarta')
    local_update = latest_data['recorded_at'].astimezone(wib_tz)
    st.markdown(f"""
    <div style='background-color:rgba(14, 165, 233, 0.15); border: 1px solid #0ea5e9; border-radius: 8px; padding: 10px; text-align: center;'>
        <span style='font-size:0.8rem; color:#38bdf8; display:block;'>UPDATE TERAKHIR (WIB)</span>
        <strong style='font-size:0.95rem; color:#f8fafc;'>{local_update.strftime('%H:%M - %d %b %Y')}</strong>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# 7. RINGKASAN METRIK REALTIME (ROW 1)
# ==========================================
st.markdown("<div class='section-header'>Indikator Cuaca & Kualitas Udara</div>", unsafe_allow_html=True)
col1, col2, col3, col4 = st.columns(4)

# 1. Kualitas Udara (AQI)
with col1:
    aqi_val = int(latest_data['aqi']) if pd.notna(latest_data['aqi']) else "N/A"
    aqi_cat = latest_data['aqi_category']
    
    # Warna pendaran teks berdasarkan status AQI
    aqi_colors = {
        "Baik": "#22c55e",
        "Sedang": "#eab308",
        "Tidak Sehat bagi Kelompok Sensitif": "#f97316",
        "Tidak Sehat": "#ef4444",
        "Sangat Tidak Sehat": "#a855f7",
        "Berbahaya": "#7f1d1d"
    }
    color = aqi_colors.get(aqi_cat, "#94a3b8")
    
    st.markdown(f"""
    <div class="metric-card">
        <span style='font-size: 0.85rem; color: #94a3b8; font-weight:600;'>KUALITAS UDARA (AQI)</span>
        <h2 style='color: {color}; margin: 5px 0 0 0; font-size: 2.3rem;'>{aqi_val}</h2>
        <span style='font-size: 0.95rem; font-weight:700; color: {color}; display: block; margin-top:2px;'>● {aqi_cat}</span>
    </div>
    """, unsafe_allow_html=True)

# 2. Suhu & Kondisi Cuaca
with col2:
    temp_val = latest_data['temperature']
    desc = latest_data['weather_description']
    icon_code = latest_data['weather_icon']
    if pd.isna(icon_code):
        icon_url = None
    elif str(icon_code).startswith("http") or str(icon_code).startswith("//"):
        icon_url = icon_code if str(icon_code).startswith("http") else f"https:{icon_code}"
    else:
        icon_url = f"https://openweathermap.org/img/wn/{icon_code}@2x.png"
    
    img_html = f"<img src='{icon_url}' style='width: 24px; height: 24px; vertical-align: middle; margin-top:-3px; margin-right:2px; margin-left:-2px;' />" if icon_url else "🌤️ "
    
    st.markdown(f"""
    <div class="metric-card">
        <span style='font-size: 0.85rem; color: #94a3b8; font-weight:600;'>SUHU & CUACA</span>
        <h2 style='color: #38bdf8; margin: 5px 0 0 0; font-size: 2.3rem;'>{temp_val}°C</h2>
        <span style='font-size: 0.9rem; color: #94a3b8; display: block; margin-top:5px;'>{img_html}{desc}</span>
    </div>
    """, unsafe_allow_html=True)

# 3. Kelembaban Udara
with col3:
    humidity_val = int(latest_data['humidity']) if pd.notna(latest_data['humidity']) else "N/A"
    st.markdown(f"""
    <div class="metric-card">
        <span style='font-size: 0.85rem; color: #94a3b8; font-weight:600;'>KELEMBABAN UDARA</span>
        <h2 style='color: #06b6d4; margin: 5px 0 0 0; font-size: 2.3rem;'>{humidity_val}%</h2>
        <span style='font-size: 0.9rem; color: #94a3b8; display: block; margin-top:5px;'>💧 Kandungan Uap Air</span>
    </div>
    """, unsafe_allow_html=True)

# 4. Kecepatan Angin
with col4:
    wind_val = latest_data['wind_speed']
    st.markdown(f"""
    <div class="metric-card">
        <span style='font-size: 0.85rem; color: #94a3b8; font-weight:600;'>KECEPATAN ANGIN</span>
        <h2 style='color: #818cf8; margin: 5px 0 0 0; font-size: 2.3rem;'>{wind_val} <span style='font-size: 1.2rem;'>km/j</span></h2>
        <span style='font-size: 0.9rem; color: #94a3b8; display: block; margin-top:5px;'>💨 Aliran Udara</span>
    </div>
    """, unsafe_allow_html=True)

# Berikan jarak vertikal yang cukup antar baris konten
st.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)

# ==========================================
# 8. DETAIL POLUTAN & PANDUAN KESEHATAN (ROW 2)
# ==========================================
col_details, col_advice = st.columns([3, 2], gap="medium")

with col_details:
    st.markdown("<div class='section-header'>Konsentrasi Polutan Utama</div>", unsafe_allow_html=True)
    
    # Data polutan
    pollutants = [
        {"name": "PM2.5 (Debu Halus)", "val": latest_data['pm25'], "unit": "µg/m³"},
        {"name": "PM10 (Debu Kasar)", "val": latest_data['pm10'], "unit": "µg/m³"},
        {"name": "O3 (Ozon)", "val": latest_data['o3'], "unit": "µg/m³"},
        {"name": "NO2 (Nitrogen Dioksida)", "val": latest_data['no2'], "unit": "µg/m³"},
        {"name": "SO2 (Sulfur Dioksida)", "val": latest_data['so2'], "unit": "µg/m³"},
        {"name": "CO (Karbon Monoksida)", "val": latest_data['co'], "unit": "µg/m³"}
    ]
    
    # Render polutan secara responsive menggunakan CSS Grid
    pollutant_items_html = ""
    for pol in pollutants:
        val_text = f"{pol['val']:.1f}" if pd.notna(pol['val']) else "N/A"
        pollutant_items_html += f"<div class='pollutant-card'><span style='font-size:0.75rem; color:#94a3b8; font-weight:500; display:flex; align-items:center; justify-content:center; min-height:32px; line-height:1.2; text-align:center;'>{pol['name']}</span><strong style='font-size:1.3rem; color:#f1f5f9; display:inline-block; margin-top:2px;'>{val_text}</strong><span style='font-size:0.7rem; color:#64748b; display:inline;'> {pol['unit']}</span></div>"
        
    st.markdown(f"<div class='pollutants-grid'>{pollutant_items_html}</div>", unsafe_allow_html=True)

with col_advice:
    st.markdown("<div class='section-header'>Panduan Aktivitas & Kesehatan</div>", unsafe_allow_html=True)
    
    # Konten panduan medis-akademis berdasarkan kategori AQI saat ini
    advices = {
        "Baik": {
            "class": "rec-good",
            "title": "Aktivitas Normal & Ventilasi Maksimal",
            "desc": "Konsentrasi polutan berada pada tingkat minimal. Tidak terdeteksi risiko kesehatan bagi seluruh kelompok populasi. Aktivitas luar ruang dapat dilaksanakan tanpa pembatasan dan pertukaran sirkulasi udara dalam ruangan sangat disarankan."
        },
        "Sedang": {
            "class": "rec-moderate",
            "title": "Kualitas Udara Akseptabel dengan Mitigasi Minimal",
            "desc": "Kadar polutan berada dalam batas ambang aman untuk populasi umum. Namun, individu dengan hipersensitivitas pernapasan ekstrem diimbau memantau respon fisiologis secara mandiri selama melakukan aktivitas fisik jangka panjang di luar ruangan."
        },
        "Tidak Sehat bagi Kelompok Sensitif": {
            "class": "rec-sensitive",
            "title": "Kewaspadaan Protektif bagi Populasi Rentan",
            "desc": "Peningkatan risiko klinis bagi populasi sensitif (anak-anak, lanjut usia, wanita hamil, serta individu dengan riwayat kelainan kardiorespiratori kronis). Disarankan membatasi durasi paparan luar ruang guna meminimalkan akumulasi pajanan polutan."
        },
        "Tidak Sehat": {
            "class": "rec-unhealthy",
            "title": "Imbauan Reduksi Aktivitas Luar Ruang & Proteksi Diri",
            "desc": "Efek kesehatan negatif berpotensi terdeteksi pada populasi umum. Disarankan mereduksi aktivitas fisik intensitas tinggi di ruang terbuka. Penggunaan respirator penyaring partikulat (seperti tipe N95/KN95) sangat disarankan jika berada di luar ruangan."
        },
        "Sangat Tidak Sehat": {
            "class": "rec-very-unhealthy",
            "title": "Restriksi Aktivitas Luar Ruang & Mitigasi Paparan Aktif",
            "desc": "Risiko gangguan kardiorespiratori meningkat signifikan secara epidemiologis bagi seluruh kalangan. Seluruh populasi diimbau menghindari aktivitas fisik di luar ruangan. Disarankan mengoperasikan alat purifikasi udara HEPA di dalam ruangan dan menutup rapat seluruh ventilasi."
        },
        "Berbahaya": {
            "class": "rec-hazardous",
            "title": "Peringatan Darurat Kualitas Lingkungan & Isolasi Fisik",
            "desc": "Keadaan darurat kesehatan lingkungan akut. Paparan udara luar berpotensi memicu efek patologis serius pada organ pernapasan dan pembuluh darah. Diwajibkan menghentikan seluruh aktivitas luar ruang, memblokir sirkulasi udara luar, dan berdiam di ruang tertutup dengan sistem purifikasi udara aktif."
        }
    }
    
    advice = advices.get(aqi_cat, {
        "class": "rec-moderate",
        "title": "Status Tidak Diketahui",
        "desc": "Data kualitas udara saat ini tidak lengkap untuk menentukan status kesehatan."
    })
    
    st.markdown(f"""
    <div class="rec-box {advice['class']}">
        <h5 style='margin:0 0 5px 0; font-weight:700;'>{advice['title']}</h5>
        <p style='margin:0; font-size:0.9rem; line-height:1.45;'>{advice['desc']}</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ==========================================
# 9. GRAFIK TREN INTERAKTIF (ROW 3)
# ==========================================
st.markdown(f"<div class='section-header'>Grafik Analisis Tren - {selected_city} ({selected_time_label})</div>", unsafe_allow_html=True)

if df_filtered.empty:
    st.warning("⚠️ Tidak ada data historis yang tersedia untuk filter waktu ini.")
else:
    tab1, tab2, tab3 = st.tabs(["Tren Kualitas Udara (AQI & PM2.5)", "Tren Parameter Cuaca", "Korelasi Cuaca vs Polusi"])
    
    with tab1:
        # Grafik Line AQI & PM2.5 menggunakan Plotly
        fig_aqi = go.Figure()
        
        # Line AQI
        fig_aqi.add_trace(go.Scatter(
            x=df_filtered['recorded_local'],
            y=df_filtered['aqi'],
            mode='lines+markers',
            name='Skor AQI (US EPA)',
            line=dict(color='#38bdf8', width=3),
            marker=dict(size=6),
            yaxis='y1'
        ))
        
        # Line PM2.5 jika ada data
        if 'pm25' in df_filtered.columns and not df_filtered['pm25'].isna().all():
            fig_aqi.add_trace(go.Scatter(
                x=df_filtered['recorded_local'],
                y=df_filtered['pm25'],
                mode='lines',
                name='PM2.5 (Debu Halus)',
                line=dict(color='#fb923c', width=2, dash='dash'),
                yaxis='y2'
            ))
            
        # Layout dual-axis agar terlihat keren
        fig_aqi.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.05,
                xanchor="center",
                x=0.5,
                font=dict(size=12, color='#f1f5f9'),
                bgcolor='rgba(15, 23, 42, 0.65)',
                bordercolor='rgba(255, 255, 255, 0.08)',
                borderwidth=1
            ),
            margin=dict(l=20, r=20, t=40, b=20),
            font=dict(color='#94a3b8'),
            xaxis=dict(
                showgrid=True, 
                gridcolor='rgba(255,255,255,0.05)',
                title="Waktu Pembacaan (WIB)",
                dtick=chart_dtick,
                tickformat=chart_tickformat
            ),
            yaxis1=dict(
                title="Indeks AQI Utama", 
                showgrid=True, 
                gridcolor='rgba(255,255,255,0.05)',
                color='#38bdf8'
            ),
            yaxis2=dict(
                title="PM2.5 Concentration (µg/m³)",
                overlaying='y',
                side='right',
                showgrid=False,
                color='#fb923c'
            )
        )
        
        st.plotly_chart(fig_aqi, width='stretch', key='chart_aqi')
        
    with tab2:
        # Grafik Line Suhu & Kelembaban
        fig_weather = go.Figure()
        
        # Line Suhu
        fig_weather.add_trace(go.Scatter(
            x=df_filtered['recorded_local'],
            y=df_filtered['temperature'],
            mode='lines+markers',
            name='Suhu (°C)',
            line=dict(color='#ff7171', width=3),
            marker=dict(size=6),
            yaxis='y1'
        ))
        
        # Line Kelembaban
        fig_weather.add_trace(go.Scatter(
            x=df_filtered['recorded_local'],
            y=df_filtered['humidity'],
            mode='lines',
            name='Kelembaban (%)',
            line=dict(color='#06b6d4', width=2, dash='dot'),
            yaxis='y2'
        ))
        
        fig_weather.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            hovermode='x unified',
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.05,
                xanchor="center",
                x=0.5,
                font=dict(size=12, color='#f1f5f9'),
                bgcolor='rgba(15, 23, 42, 0.65)',
                bordercolor='rgba(255, 255, 255, 0.08)',
                borderwidth=1
            ),
            margin=dict(l=20, r=20, t=40, b=20),
            font=dict(color='#94a3b8'),
            xaxis=dict(
                showgrid=True, 
                gridcolor='rgba(255,255,255,0.05)',
                title="Waktu Pembacaan (WIB)",
                dtick=chart_dtick,
                tickformat=chart_tickformat
            ),
            yaxis1=dict(
                title="Temperatur (°C)", 
                showgrid=True, 
                gridcolor='rgba(255,255,255,0.05)',
                color='#ff7171'
            ),
            yaxis2=dict(
                title="Kelembaban (%)",
                overlaying='y',
                side='right',
                showgrid=False,
                color='#06b6d4'
            )
        )
        
        st.plotly_chart(fig_weather, width='stretch', key='chart_weather')
        
    with tab3:
        # Korelasi Cuaca vs Polusi (Scatter Plot dengan Trendline)
        st.markdown("<p style='text-align: center; color: #94a3b8;'>Hubungan antara <b>Suhu Udara</b> vs <b>Konsentrasi Debu PM2.5</b></p>", unsafe_allow_html=True)
        
        # Hapus baris kosong agar scatter berjalan lancar
        df_corr = df_filtered.dropna(subset=['temperature', 'pm25'])
        
        if df_corr.empty:
            st.info("⚠️ Data polutan PM2.5 atau Suhu tidak lengkap untuk membuat korelasi.")
        else:
            fig_corr = px.scatter(
                df_corr, 
                x="temperature", 
                y="pm25",
                color="aqi_category",
                color_discrete_map=aqi_colors,
                labels={
                    "temperature": "Suhu Udara (°C)",
                    "pm25": "Debu Halus PM2.5 (µg/m³)",
                    "aqi_category": "Kategori AQI"
                },
                hover_data=["recorded_local"]
            )
            
            fig_corr.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=20, b=20),
                font=dict(color='#f1f5f9'),
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                legend=dict(
                    font=dict(size=11, color='#f1f5f9'),
                    bgcolor='rgba(15, 23, 42, 0.65)',
                    bordercolor='rgba(255, 255, 255, 0.08)',
                    borderwidth=1
                )
            )
            
            st.plotly_chart(fig_corr, width='stretch', key='chart_corr')

st.markdown("---")

# ==========================================
# 10. PETA INTERAKTIF SEBARAN STASIUN (ROW 4)
# ==========================================
st.markdown("<div class='section-header'>Peta Kualitas Udara Seluruh Kota Pantauan</div>", unsafe_allow_html=True)

# Kelompokkan data terbaru untuk setiap kota
df_latest_all = df_raw.groupby('city').first().reset_index()

# Saring stasiun yang memiliki data koordinat
df_map = df_latest_all.dropna(subset=['latitude', 'longitude', 'aqi'])

if df_map.empty:
    st.info("⚠️ Data koordinat stasiun kota tidak lengkap untuk ditampilkan di peta.")
else:
    # Buat Scatter Mapbox yang sangat premium menggunakan Plotly
    fig_map = px.scatter_map(
        df_map,
        lat="latitude",
        lon="longitude",
        hover_name="city",
        hover_data={
            "aqi": True, 
            "aqi_category": True, 
            "temperature": True,
            "latitude": False,
            "longitude": False
        },
        color="aqi_category",
        color_discrete_map=aqi_colors,
        size="aqi",
        size_max=22,
        zoom=4.5,
        center={"lat": -2.5, "lon": 118.0},
        map_style="carto-darkmatter",
        height=450
    )
    
    fig_map.update_layout(
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(l=0, r=0, t=0, b=0),
        legend=dict(
            title="Tingkat AQI",
            yanchor="top",
            y=0.98,
            xanchor="left",
            x=0.02,
            bgcolor="rgba(15, 23, 42, 0.8)",
            font=dict(color="#f8fafc")
        )
    )
    
    st.plotly_chart(fig_map, width='stretch', key='chart_map')

st.markdown("""
<div class='app-footer'>
    <p>&copy; 2026 Arik Rizki Akbar. All Rights Reserved.</p>
    <p>Nusantara Air Sentinel &mdash; Real-Time Weather & Air Quality Monitoring Platform</p>
    <p>Built with Python &bull; Supabase &bull; Streamlit &bull; Plotly &bull; GitHub Actions &bull; <a href='https://github.com/arik147/nusantara-air-sentinel' target='_blank'>GitHub Repository</a></p>
</div>
""", unsafe_allow_html=True)
