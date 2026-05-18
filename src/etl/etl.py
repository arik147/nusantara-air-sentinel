# Data Pipeline: ETL Script for Weather & Air Quality Monitoring Dashboard
# Technology: Python, Requests, Pandas, Supabase Client (WeatherAPI.com Edition)
# Version 2.0: Parallel Fetching, Batch Upsert, Retry, Data Validation

import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import pandas as pd
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from supabase import create_client, Client

# Muat variabel lingkungan dari file .env (jika ada, untuk pengembangan lokal)
load_dotenv()

# ============================================================
# KONFIGURASI
# ============================================================
WEATHERAPI_KEY = os.getenv("WEATHERAPI_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
# Gunakan service_role key untuk bypass RLS (write access)
# Fallback ke SUPABASE_KEY untuk backward compatibility
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

# Parameter Pipeline
MAX_WORKERS = 10       # Jumlah thread paralel untuk API calls
MAX_RETRIES = 3        # Percobaan ulang jika API gagal
RETRY_BACKOFF = 1      # Detik awal exponential backoff (1s, 2s, 4s)
REQUEST_TIMEOUT = 15   # Timeout per request (detik)

# ============================================================
# DAFTAR 52 KOTA TARGET PANTAUAN NUSANTARA
# ============================================================
CITIES = [
    # Sumatera (12)
    {"name": "Banda Aceh", "country_code": "ID"},
    {"name": "Medan", "country_code": "ID"},
    {"name": "Pekanbaru", "country_code": "ID"},
    {"name": "Batam", "country_code": "ID"},
    {"name": "Padang", "country_code": "ID"},
    {"name": "Jambi", "country_code": "ID"},
    {"name": "Bengkulu", "country_code": "ID"},
    {"name": "Palembang", "country_code": "ID"},
    {"name": "Bandar Lampung", "country_code": "ID"},
    {"name": "Pangkalpinang", "country_code": "ID"},
    {"name": "Tanjungpinang", "country_code": "ID"},
    {"name": "Metro", "country_code": "ID"},
    
    # Jawa (19)
    {"name": "Jakarta", "country_code": "ID"},
    {"name": "Tangerang", "country_code": "ID"},
    {"name": "Tangerang Selatan", "country_code": "ID"},
    {"name": "Bekasi", "country_code": "ID"},
    {"name": "Depok", "country_code": "ID"},
    {"name": "Bogor", "country_code": "ID"},
    {"name": "Bandung", "country_code": "ID"},
    {"name": "Cimahi", "country_code": "ID"},
    {"name": "Majalengka", "country_code": "ID"},
    {"name": "Purwakarta", "country_code": "ID"},
    {"name": "Cirebon", "country_code": "ID"},
    {"name": "Tasikmalaya", "country_code": "ID"},
    {"name": "Semarang", "country_code": "ID"},
    {"name": "Surakarta", "country_code": "ID"},
    {"name": "Tegal", "country_code": "ID"},
    {"name": "Yogyakarta", "country_code": "ID"},
    {"name": "Surabaya", "country_code": "ID"},
    {"name": "Malang", "country_code": "ID"},
    {"name": "Kediri", "country_code": "ID"},
    
    # Bali & Nusa Tenggara (3)
    {"name": "Denpasar", "country_code": "ID"},
    {"name": "Mataram", "country_code": "ID"},
    {"name": "Kupang", "country_code": "ID"},
    
    # Kalimantan (7)
    {"name": "Pontianak", "country_code": "ID"},
    {"name": "Palangkaraya", "country_code": "ID"},
    {"name": "Banjarmasin", "country_code": "ID"},
    {"name": "Balikpapan", "country_code": "ID"},
    {"name": "Samarinda", "country_code": "ID"},
    {"name": "Bontang", "country_code": "ID"},
    {"name": "Tarakan", "country_code": "ID"},
    
    # Sulawesi (6)
    {"name": "Makassar", "country_code": "ID"},
    {"name": "Palu", "country_code": "ID"},
    {"name": "Kendari", "country_code": "ID"},
    {"name": "Manado", "country_code": "ID"},
    {"name": "Gorontalo", "country_code": "ID"},
    {"name": "Bitung", "country_code": "ID"},
    
    # Maluku & Papua (5)
    {"name": "Ternate", "country_code": "ID"},
    {"name": "Ambon", "country_code": "ID"},
    {"name": "Sorong", "country_code": "ID"},
    {"name": "Jayapura", "country_code": "ID"},
    {"name": "Merauke", "country_code": "ID"}
]

# ============================================================
# FUNGSI KALKULASI AQI (US-EPA STANDARD)
# ============================================================
def calculate_pm25_aqi(pm25: float) -> int:
    """Menghitung nilai AQI berdasarkan konsentrasi PM2.5 menggunakan standar US-EPA."""
    if pm25 is None or pm25 < 0:
        return 0
    
    # Breakpoints US-EPA untuk PM2.5 (µg/m³)
    breakpoints = [
        (0.0,   12.0,   0,   50),
        (12.1,  35.4,   51,  100),
        (35.5,  55.4,   101, 150),
        (55.5,  150.4,  151, 200),
        (150.5, 250.4,  201, 300),
        (250.5, 350.4,  301, 400),
        (350.5, 500.4,  401, 500),
    ]
    
    for bp_lo, bp_hi, aqi_lo, aqi_hi in breakpoints:
        if pm25 <= bp_hi:
            return round(((aqi_hi - aqi_lo) / (bp_hi - bp_lo)) * (pm25 - bp_lo) + aqi_lo)
    
    return 500  # Di atas skala


def get_aqi_category(aqi: int) -> str:
    """Mengonversi nilai AQI ke kategori kualitas udara bahasa Indonesia."""
    if aqi is None:
        return "Tidak Diketahui"
    
    aqi = int(aqi)
    if aqi <= 50:
        return "Baik"
    elif aqi <= 100:
        return "Sedang"
    elif aqi <= 150:
        return "Tidak Sehat bagi Kelompok Sensitif"
    elif aqi <= 200:
        return "Tidak Sehat"
    elif aqi <= 300:
        return "Sangat Tidak Sehat"
    else:
        return "Berbahaya"

# ============================================================
# VALIDASI DATA
# ============================================================
def validate_record(record: dict) -> tuple:
    """Validasi range nilai data cuaca dan polusi. Returns (is_valid, warnings)."""
    warnings = []
    
    # Validasi suhu (-50°C sampai 60°C)
    if record.get("temperature") is not None:
        if not (-50 <= record["temperature"] <= 60):
            warnings.append(f"Suhu di luar range: {record['temperature']}°C")
    
    # Validasi kelembaban (0-100%)
    if record.get("humidity") is not None:
        if not (0 <= record["humidity"] <= 100):
            warnings.append(f"Kelembaban di luar range: {record['humidity']}%")
    
    # Validasi AQI (0-500)
    if record.get("aqi") is not None:
        if not (0 <= record["aqi"] <= 500):
            warnings.append(f"AQI di luar range: {record['aqi']}")
    
    # Validasi konsentrasi polutan (tidak boleh negatif)
    for pol in ["pm25", "pm10", "no2", "so2", "o3", "co"]:
        if record.get(pol) is not None and record[pol] < 0:
            warnings.append(f"{pol} negatif: {record[pol]}")
    
    # Validasi kecepatan angin (tidak boleh negatif)
    if record.get("wind_speed") is not None and record["wind_speed"] < 0:
        warnings.append(f"Kecepatan angin negatif: {record['wind_speed']}")
    
    return (len(warnings) == 0, warnings)

# ============================================================
# HTTP SESSION DENGAN RETRY OTOMATIS
# ============================================================
def create_resilient_session() -> requests.Session:
    """Membuat HTTP session dengan retry strategy dan connection pooling."""
    session = requests.Session()
    retry_strategy = Retry(
        total=MAX_RETRIES,
        backoff_factor=RETRY_BACKOFF,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )
    adapter = HTTPAdapter(
        max_retries=retry_strategy,
        pool_connections=MAX_WORKERS,
        pool_maxsize=MAX_WORKERS
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session

# ============================================================
# FUNGSI FETCH PER KOTA (THREAD-SAFE)
# ============================================================
def fetch_and_transform(session: requests.Session, city_name: str, country_code: str) -> dict:
    """Menarik dan mentransformasi data untuk satu kota. Thread-safe."""
    url = "https://api.weatherapi.com/v1/current.json"
    params = {
        "key": WEATHERAPI_KEY,
        "q": f"{city_name},{country_code}",
        "aqi": "yes"
    }
    
    try:
        response = session.get(url, params=params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        api_data = response.json()
    except requests.exceptions.RequestException as e:
        return {"city": city_name, "status": "error", "message": str(e)}
    
    try:
        # 1. Ekstrak Waktu & Lokasi
        location = api_data["location"]
        current = api_data["current"]
        
        lat = location["lat"]
        lon = location["lon"]
        recorded_epoch = current["last_updated_epoch"]
        recorded_at = datetime.fromtimestamp(recorded_epoch, tz=timezone.utc).isoformat()
        
        # 2. Ekstrak Data Cuaca
        temp = current["temp_c"]
        humidity = current["humidity"]
        wind_speed = current["wind_kph"]
        weather_desc = current["condition"]["text"].title()
        weather_icon = current["condition"]["icon"]
        
        # Pastikan ikon berformat URL lengkap dengan https:
        if weather_icon and weather_icon.startswith("//"):
            weather_icon = f"https:{weather_icon}"
        
        # 3. Ekstrak Data Kualitas Udara
        air_quality = current.get("air_quality", {})
        pm25 = air_quality.get("pm2_5")
        pm10 = air_quality.get("pm10")
        no2 = air_quality.get("no2")
        so2 = air_quality.get("so2")
        o3 = air_quality.get("o3")
        co = air_quality.get("co")
        
        # 4. Hitung AQI secara sains dari PM2.5
        aqi_val = calculate_pm25_aqi(pm25) if pm25 is not None else None
        aqi_category = get_aqi_category(aqi_val)
        
        # 5. Susun record
        record = {
            "city": city_name,
            "country": country_code,
            "latitude": lat,
            "longitude": lon,
            "recorded_at": recorded_at,
            "temperature": float(temp),
            "humidity": float(humidity),
            "wind_speed": float(wind_speed),
            "weather_description": weather_desc,
            "weather_icon": weather_icon,
            "aqi": int(aqi_val) if aqi_val is not None else None,
            "aqi_category": aqi_category,
            "pm25": float(pm25) if pm25 is not None else None,
            "pm10": float(pm10) if pm10 is not None else None,
            "no2": float(no2) if no2 is not None else None,
            "so2": float(so2) if so2 is not None else None,
            "o3": float(o3) if o3 is not None else None,
            "co": float(co) if co is not None else None,
            "status": "ok"
        }
        
        # 6. Validasi data
        is_valid, warnings = validate_record(record)
        if not is_valid:
            record["status"] = "warning"
            record["warnings"] = warnings
        
        return record
        
    except Exception as e:
        return {"city": city_name, "status": "error", "message": f"Transform error: {str(e)}"}

# ============================================================
# FUNGSI UTAMA PIPELINE
# ============================================================
def main():
    start_time = datetime.now(timezone.utc)
    print(f"{'='*65}")
    print(f"  NUSANTARA AIR SENTINEL — ETL Pipeline v2.0")
    print(f"  Waktu mulai : {start_time.isoformat()}")
    print(f"  Target kota : {len(CITIES)} kota")
    print(f"  Parallelism : {MAX_WORKERS} worker threads")
    print(f"  Retry       : {MAX_RETRIES}x dengan backoff {RETRY_BACKOFF}s")
    print(f"{'='*65}\n")
    
    # Validasi Kredensial
    if not all([WEATHERAPI_KEY, SUPABASE_URL, SUPABASE_SERVICE_KEY]):
        print("[FATAL] Konfigurasi credentials tidak lengkap!")
        print("  Pastikan WEATHERAPI_KEY, SUPABASE_URL, dan SUPABASE_SERVICE_KEY tersedia.")
        return
    
    # ---- PHASE 1: EXTRACT + TRANSFORM (Parallel) ----
    print("[PHASE 1/2] Extract & Transform - Fetching data secara paralel...\n")
    
    session = create_resilient_session()
    records = []
    errors = []
    warnings_list = []
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit semua task secara paralel
        future_to_city = {
            executor.submit(fetch_and_transform, session, city["name"], city["country_code"]): city["name"]
            for city in CITIES
        }
        
        # Kumpulkan hasil saat selesai
        for future in as_completed(future_to_city):
            city_name = future_to_city[future]
            try:
                result = future.result()
                
                if result["status"] == "error":
                    errors.append(f"{city_name}: {result.get('message', 'Unknown error')}")
                    print(f"  [FAIL] {city_name} - GAGAL: {result.get('message', '')[:80]}")
                else:
                    if result["status"] == "warning":
                        for w in result.get("warnings", []):
                            warnings_list.append(f"{city_name}: {w}")
                        print(f"  [WARN] {city_name} - OK (dengan warning validasi)")
                    else:
                        print(f"  [OK] {city_name} - Suhu: {result['temperature']}C | AQI: {result['aqi']} ({result['aqi_category']})")
                    
                    # Hapus field internal sebelum simpan ke DB
                    clean_record = {k: v for k, v in result.items() if k not in ("status", "warnings")}
                    records.append(clean_record)
                    
            except Exception as e:
                errors.append(f"{city_name}: Unexpected error - {str(e)}")
                print(f"  [FAIL] {city_name} - EXCEPTION: {str(e)[:80]}")
    
    session.close()
    
    # ---- PHASE 2: LOAD (Batch Upsert) ----
    print(f"\n[PHASE 2/2] Load - Batch upsert ke Supabase...\n")
    
    if not records:
        print("[ABORT] Tidak ada data yang berhasil diproses. Pipeline dihentikan.")
        return
    
    # Inisialisasi Supabase Client dengan service_role key
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    
    try:
        # Batch upsert: kirim SEMUA records dalam 1 query
        result = supabase.table("weather_air_metrics").upsert(
            records,
            on_conflict="city,recorded_at"
        ).execute()
        
        saved_count = len(result.data) if result.data else len(records)
        print(f"  [OK] Batch upsert berhasil: {saved_count} record tersimpan.\n")
        
    except Exception as e:
        print(f"  [FAIL] Batch upsert GAGAL: {str(e)}")
        print(f"  Mencoba fallback: upsert satu per satu...\n")
        
        # Fallback: upsert per record jika batch gagal
        saved_count = 0
        for record in records:
            try:
                supabase.table("weather_air_metrics").upsert(
                    record,
                    on_conflict="city,recorded_at"
                ).execute()
                saved_count += 1
            except Exception as e2:
                print(f"  [FAIL] Gagal simpan {record['city']}: {str(e2)[:60]}")
        
        print(f"  Fallback selesai: {saved_count}/{len(records)} record tersimpan.\n")
    
    # ---- SUMMARY ----
    elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()
    print(f"{'='*65}")
    print(f"  PIPELINE SUMMARY")
    print(f"{'='*65}")
    print(f"  Total kota target  : {len(CITIES)}")
    print(f"  Berhasil diproses  : {len(records)}")
    print(f"  Gagal fetch/parse  : {len(errors)}")
    print(f"  Warning validasi   : {len(warnings_list)}")
    print(f"  Tersimpan ke DB    : {saved_count}")
    print(f"  Waktu eksekusi     : {elapsed:.1f} detik")
    print(f"{'='*65}")
    
    if errors:
        print(f"\n[ERRORS]")
        for err in errors:
            print(f"  - {err}")
    
    if warnings_list:
        print(f"\n[WARNINGS]")
        for w in warnings_list:
            print(f"  - {w}")
    
    print(f"\n[DONE] Pipeline ETL v2.0 selesai pada {datetime.now(timezone.utc).isoformat()}")


if __name__ == "__main__":
    main()
