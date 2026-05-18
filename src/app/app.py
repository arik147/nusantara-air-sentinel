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
    page_title="Weather & Air Quality Realtime Dashboard",
    page_icon="🌤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk gaya visual premium (Glassmorphism & Card style)
st.markdown("""
<style>
    /* Mengubah font utama dan background */
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        color: #f8fafc;
    }
    
    /* Styling Card Glassmorphism */
    div[data-testid="stMetricValue"] {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: #38bdf8 !important;
    }
    
    /* Custom Card container */
    .metric-card {
        background: rgba(30, 41, 59, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 18px;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(8px);
        -webkit-backdrop-filter: blur(8px);
        margin-bottom: 12px;
    }
    
    /* Rekomendasi box styling */
    .rec-box {
        border-radius: 10px;
        padding: 15px;
        margin-top: 10px;
        border-left: 5px solid;
    }
    .rec-good {
        background-color: rgba(34, 197, 94, 0.15);
        border-left-color: #22c55e;
        color: #86efac;
    }
    .rec-moderate {
        background-color: rgba(234, 179, 8, 0.15);
        border-left-color: #eab308;
        color: #fde047;
    }
    .rec-sensitive {
        background-color: rgba(249, 115, 22, 0.15);
        border-left-color: #f97316;
        color: #fdba74;
    }
    .rec-unhealthy {
        background-color: rgba(239, 68, 68, 0.15);
        border-left-color: #ef4444;
        color: #fca5a5;
    }
    .rec-very-unhealthy {
        background-color: rgba(168, 85, 247, 0.15);
        border-left-color: #a855f7;
        color: #d8b4fe;
    }
    .rec-hazardous {
        background-color: rgba(127, 29, 29, 0.3);
        border-left-color: #7f1d1d;
        color: #fda4af;
    }
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
st.sidebar.markdown("<h2 style='text-align: center;'>⚙️ Kontrol & Filter</h2>", unsafe_allow_html=True)

# Load data awal
df_raw = load_all_metrics()

if df_raw.empty:
    st.warning("⚠️ Database masih kosong atau belum terhubung! Silakan jalankan skrip ETL Anda untuk memasukkan data pertama.")
    if st.sidebar.button("🔄 Segarkan Database"):
        refresh_data()
        st.rerun()
    st.stop()

# Filter Kota
all_cities = sorted(df_raw['city'].unique())
selected_city = st.sidebar.selectbox("📍 Pilih Kota Pantauan", all_cities)

# Filter Rentang Waktu
st.sidebar.markdown("---")
st.sidebar.markdown("📅 **Filter Waktu**")
time_options = {
    "1 Hari Terakhir": 1,
    "3 Hari Terakhir": 3,
    "7 Hari Terakhir": 7,
    "30 Hari Terakhir": 30,
    "Tampilkan Semua": 365
}
selected_time_label = st.sidebar.radio("Rentang Analisis", list(time_options.keys()))
days_threshold = time_options[selected_time_label]

# Tombol Sinkronisasi Manual
if st.sidebar.button("🔄 Tarik Data Terbaru", use_container_width=True):
    refresh_data()
    st.toast("Data berhasil disegarkan dari Supabase!", icon="🚀")
    st.rerun()

# Penjelasan Arsitektur untuk Portofolio
st.sidebar.markdown("---")
st.sidebar.markdown("### 🏗️ Arsitektur Proyek")
st.sidebar.info("""
**Supabase Zero Cost Stack**
*   **Data Pipelines**: Python ETL (`pandas`, `requests`) otomatis berjalan di **GitHub Actions** setiap jam.
*   **Penyimpanan**: **Supabase PostgreSQL** dengan index optimasi dan unique constraints.
*   **Visualisasi**: **Streamlit Cloud** & **Plotly** untuk visualisasi tren data cuaca dan AQI realtime.
""")

# ==========================================
# 5. PENGOLAHAN DATA & FILTERING
# ==========================================
# Filter data berdasarkan kota terpilih
df_city = df_raw[df_raw['city'] == selected_city].copy()

# Filter berdasarkan rentang waktu
cutoff_date = datetime.now(pytz.utc) - timedelta(days=days_threshold)
df_filtered = df_city[df_city['recorded_at'] >= cutoff_date].copy()
df_filtered = df_filtered.sort_values(by='recorded_at')  # Urutkan kronologis untuk grafik

# Dapatkan data realtime terkini untuk kota terpilih
latest_data = df_city.iloc[0]

# ==========================================
# 6. HEADER UTAMA
# ==========================================
col_title, col_status = st.columns([4, 1])
with col_title:
    st.markdown(f"<h1 style='margin-bottom:0px;'>🌤️ Dashboard Cuaca & Kualitas Udara Realtime</h1>", unsafe_allow_html=True)
    st.markdown(f"<p style='color: #94a3b8; font-size:1.1rem;'>Stasiun Pemantauan Otomatis: <b>{latest_data['city']}, {latest_data['country']}</b></p>", unsafe_allow_html=True)

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
st.markdown("### 📊 Kondisi Realtime Terkini")
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
    
    img_html = f"<img src='{icon_url}' style='width: 40px; height: 40px; vertical-align: middle; margin-right:5px;' />" if icon_url else "🌤️"
    
    st.markdown(f"""
    <div class="metric-card">
        <span style='font-size: 0.85rem; color: #94a3b8; font-weight:600;'>SUHU & CUACA</span>
        <h2 style='color: #38bdf8; margin: 5px 0 0 0; font-size: 2.3rem;'>{temp_val}°C</h2>
        <span style='font-size: 0.9rem; color: #e2e8f0; display: block; margin-top:5px;'>{img_html} {desc}</span>
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

# ==========================================
# 8. DETAIL POLUTAN & PANDUAN KESEHATAN (ROW 2)
# ==========================================
col_details, col_advice = st.columns([3, 2])

with col_details:
    st.markdown("<h4 style='margin-top:10px;'>🧪 Konsentrasi Polutan Utama</h4>", unsafe_allow_html=True)
    
    # Buat grid untuk polutan individual
    pol1, pol2, pol3 = st.columns(3)
    pol4, pol5, pol6 = st.columns(3)
    
    pollutants = [
        {"name": "PM2.5 (Debu Halus)", "val": latest_data['pm25'], "unit": "µg/m³", "col": pol1},
        {"name": "PM10 (Debu Kasar)", "val": latest_data['pm10'], "unit": "µg/m³", "col": pol2},
        {"name": "O3 (Ozon)", "val": latest_data['o3'], "unit": "µg/m³", "col": pol3},
        {"name": "NO2 (Nitrogen Dioksida)", "val": latest_data['no2'], "unit": "µg/m³", "col": pol4},
        {"name": "SO2 (Sulfur Dioksida)", "val": latest_data['so2'], "unit": "µg/m³", "col": pol5},
        {"name": "CO (Karbon Monoksida)", "val": latest_data['co'], "unit": "µg/m³", "col": pol6}
    ]
    
    for pol in pollutants:
        with pol["col"]:
            val_text = f"{pol['val']:.1f}" if pd.notna(pol['val']) else "N/A"
            st.markdown(f"""
            <div style='background-color:rgba(30, 41, 59, 0.25); border: 1px solid rgba(255, 255, 255, 0.05); border-radius: 8px; padding: 10px; text-align: center; margin-bottom: 10px;'>
                <span style='font-size:0.75rem; color:#94a3b8; font-weight:500; display:block;'>{pol['name']}</span>
                <strong style='font-size:1.3rem; color:#f1f5f9; display:inline-block; margin-top:2px;'>{val_text}</strong>
                <span style='font-size:0.7rem; color:#64748b; display:inline;'> {pol['unit']}</span>
            </div>
            """, unsafe_allow_html=True)

with col_advice:
    st.markdown("<h4 style='margin-top:10px;'>🏥 Panduan Aktivitas & Kesehatan</h4>", unsafe_allow_html=True)
    
    # Konten panduan berdasarkan kategori AQI saat ini
    advices = {
        "Baik": {
            "class": "rec-good",
            "title": "Aman untuk Semua Aktivitas 🧘",
            "desc": "Kualitas udara sangat baik. Silakan berolahraga di luar ruangan, jalan-jalan, dan ventilasikan ruangan Anda secara bebas."
        },
        "Sedang": {
            "class": "rec-moderate",
            "title": "Kondisi Dapat Diterima 👍",
            "desc": "Kualitas udara sedang. Orang yang sangat sensitif terhadap polusi sebaiknya membatasi aktivitas fisik yang berat di luar ruangan."
        },
        "Tidak Sehat bagi Kelompok Sensitif": {
            "class": "rec-sensitive",
            "title": "Kelompok Sensitif Harap Waspada 😷",
            "desc": "Penderita penyakit asma, anak-anak, lansia, dan ibu hamil sebaiknya mengurangi aktivitas fisik yang terlalu lama atau berat di luar ruangan."
        },
        "Tidak Sehat": {
            "class": "rec-unhealthy",
            "title": "Kurangi Aktivitas Luar Ruangan 🚪",
            "desc": "Masyarakat umum disarankan menggunakan masker jika beraktivitas lama di luar ruangan. Penderita penyakit pernapasan harap beraktivitas di dalam ruangan saja."
        },
        "Sangat Tidak Sehat": {
            "class": "rec-very-unhealthy",
            "title": "Tingkat Bahaya Meningkat 🚨",
            "desc": "Hindari aktivitas fisik yang lama di luar ruangan bagi semua kalangan. Gunakan air purifier di dalam rumah dan pastikan jendela tertutup rapat."
        },
        "Berbahaya": {
            "class": "rec-hazardous",
            "title": "DARURAT KESEHATAN ⚠️",
            "desc": "Setiap orang harus menghindari semua aktivitas fisik di luar ruangan. Udara luar ruangan beracun. Tetap di dalam ruangan terlindung."
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
st.markdown(f"### 📈 Grafik Analisis Tren - {selected_city} ({selected_time_label})")

if df_filtered.empty:
    st.warning("⚠️ Tidak ada data historis yang tersedia untuk filter waktu ini.")
else:
    tab1, tab2, tab3 = st.tabs(["📊 Tren Kualitas Udara (AQI & PM2.5)", "🌡️ Tren Parameter Cuaca", "🔄 Korelasi Cuaca vs Polusi"])
    
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
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=40, b=20),
            font=dict(color='#94a3b8'),
            xaxis=dict(
                showgrid=True, 
                gridcolor='rgba(255,255,255,0.05)',
                title="Waktu Pembacaan (WIB)"
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
        
        st.plotly_chart(fig_aqi, use_container_width=True)
        
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
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=20, r=20, t=40, b=20),
            font=dict(color='#94a3b8'),
            xaxis=dict(
                showgrid=True, 
                gridcolor='rgba(255,255,255,0.05)',
                title="Waktu Pembacaan (WIB)"
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
        
        st.plotly_chart(fig_weather, use_container_width=True)
        
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
                font=dict(color='#94a3b8'),
                xaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'),
                yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)')
            )
            
            st.plotly_chart(fig_corr, use_container_width=True)

st.markdown("---")

# ==========================================
# 10. PETA INTERAKTIF SEBARAN STASIUN (ROW 4)
# ==========================================
st.markdown("### 🗺️ Peta Kualitas Udara Seluruh Kota Pantauan")

# Kelompokkan data terbaru untuk setiap kota
df_latest_all = df_raw.groupby('city').first().reset_index()

# Saring stasiun yang memiliki data koordinat
df_map = df_latest_all.dropna(subset=['latitude', 'longitude', 'aqi'])

if df_map.empty:
    st.info("⚠️ Data koordinat stasiun kota tidak lengkap untuk ditampilkan di peta.")
else:
    # Buat Scatter Mapbox yang sangat premium menggunakan Plotly
    fig_map = px.scatter_mapbox(
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
        center={"lat": -2.5, "lon": 118.0},  # Fokus pas di tengah kepulauan Indonesia
        mapbox_style="carto-darkmatter",     # Style dark map gratis yang sangat futuristik
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
    
    st.plotly_chart(fig_map, use_container_width=True)
