-- Database Schema: Weather & Air Quality Monitoring Dashboard
-- Target: Supabase PostgreSQL Database

-- Hapus tabel jika sudah ada (untuk memudahkan setup pertama kali)
DROP TABLE IF EXISTS weather_air_metrics;

-- Buat tabel utama untuk menampung data gabungan cuaca dan kualitas udara
CREATE TABLE weather_air_metrics (
    id SERIAL PRIMARY KEY,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(10) DEFAULT 'ID',
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Parameter Cuaca
    temperature REAL,                   -- dalam derajat Celsius
    humidity REAL,                      -- dalam persen (%)
    wind_speed REAL,                    -- dalam km/jam
    weather_description VARCHAR(100),   -- deskripsi kondisi (misal: "hujan ringan", "cerah")
    weather_icon VARCHAR(255),          -- URL ikon cuaca (kompatibel OWM & WeatherAPI)
    
    -- Parameter Kualitas Udara (Polutan & AQI)
    aqi INTEGER,                        -- Indeks Kualitas Udara (US EPA AQI Standard)
    aqi_category VARCHAR(50),           -- Kategori (Good, Moderate, Unhealthy, dll)
    pm25 REAL,                          -- PM2.5 (ug/m3)
    pm10 REAL,                          -- PM10 (ug/m3)
    no2 REAL,                           -- Nitrogen Dioksida (ug/m3)
    so2 REAL,                           -- Sulfur Dioksida (ug/m3)
    o3 REAL,                            -- Ozon (ug/m3)
    co REAL,                            -- Karbon Monoksida (ug/m3)
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Kontrol Integritas: Hindari duplikasi data untuk kota dan waktu pencatatan yang sama
    CONSTRAINT unique_city_recorded_at UNIQUE (city, recorded_at)
);

-- Indeks untuk mempercepat pencarian data berdasarkan kota dan rentang waktu (sangat penting untuk grafik tren)
CREATE INDEX idx_metrics_city_recorded_at ON weather_air_metrics(city, recorded_at DESC);
