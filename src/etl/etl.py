# Data Pipeline: ETL Script for Weather & Air Quality Monitoring Dashboard
# Technology: Python, Requests, Pandas, Supabase Client (WeatherAPI.com Edition)

import os
import requests
import pandas as pd
from datetime import datetime, timezone
from dotenv import load_dotenv
from supabase import create_client, Client

# Muat variabel lingkungan dari file .env (jika ada, untuk pengembangan lokal)
load_dotenv()

# Konfigurasi API Keys dan Database Credentials
WEATHERAPI_KEY = os.getenv("WEATHERAPI_KEY")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Daftar 50 kota target untuk dipantau secara otomatis (Representasi Nusantara Selengkapnya)
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

def calculate_pm25_aqi(pm25: float) -> int:
    """Menghitung nilai AQI berdasarkan konsentrasi PM2.5 menggunakan standar US-EPA."""
    if pm25 is None or pm25 < 0:
        return 0
    
    if pm25 <= 12.0:
        return round(((50 - 0) / (12.0 - 0.0)) * (pm25 - 0.0) + 0)
    elif pm25 <= 35.4:
        return round(((100 - 51) / (35.4 - 12.1)) * (pm25 - 12.1) + 51)
    elif pm25 <= 55.4:
        return round(((150 - 101) / (55.4 - 35.5)) * (pm25 - 35.5) + 101)
    elif pm25 <= 150.4:
        return round(((200 - 151) / (150.4 - 55.5)) * (pm25 - 55.5) + 151)
    elif pm25 <= 250.4:
        return round(((300 - 201) / (250.4 - 150.5)) * (pm25 - 150.5) + 201)
    elif pm25 <= 350.4:
        return round(((400 - 301) / (350.4 - 250.5)) * (pm25 - 250.5) + 301)
    elif pm25 <= 500.4:
        return round(((500 - 401) / (500.4 - 350.5)) * (pm25 - 350.5) + 401)
    else:
        return 500

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

def fetch_weather_aqi_data(city_name: str, country_code: str):
    """Menarik data cuaca dan kualitas udara sekaligus dari WeatherAPI.com."""
    url = "https://api.weatherapi.com/v1/current.json"
    params = {
        "key": WEATHERAPI_KEY,
        "q": f"{city_name},{country_code}",
        "aqi": "yes"
    }
    
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(f"[-] Gagal mengambil data untuk {city_name}: {response.text}")
        return None
    
    return response.json()

def main():
    print(f"=== Memulai Pipeline ETL WeatherAPI.com pada {datetime.now(timezone.utc).isoformat()} ===")
    
    # Validasi Kredensial
    if not all([WEATHERAPI_KEY, SUPABASE_URL, SUPABASE_KEY]):
        print("[-] ERROR: Konfigurasi WEATHERAPI_KEY atau Supabase credentials tidak lengkap di Environment Variables!")
        return
    
    # Inisialisasi Supabase Client
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    records = []
    
    for city in CITIES:
        city_name = city["name"]
        country_code = city["country_code"]
        print(f"\n[+] Memproses kota: {city_name}...")
        
        # Ambil data cuaca dan AQI secara simultan
        api_data = fetch_weather_aqi_data(city_name, country_code)
        if not api_data:
            continue
            
        try:
            # 1. Ekstrak Waktu & Lokasi
            location = api_data["location"]
            current = api_data["current"]
            
            lat = location["lat"]
            lon = location["lon"]
            
            # Waktu update terakhir dalam format epoch
            recorded_epoch = current["last_updated_epoch"]
            recorded_at = datetime.fromtimestamp(recorded_epoch, tz=timezone.utc).isoformat()
            
            # 2. Ekstrak Data Cuaca
            temp = current["temp_c"]
            humidity = current["humidity"]
            wind_speed = current["wind_kph"]  # Sudah dalam km/jam dari API
            weather_desc = current["condition"]["text"].title()
            weather_icon = current["condition"]["icon"]  # Mengembalikan link ikon full
            
            # Pastikan ikon berformat URL lengkap dengan https:
            if weather_icon and weather_icon.startswith("//"):
                weather_icon = f"https:{weather_icon}"
            
            # 3. Ekstrak Data Kualitas Udara (AQI & Polutan)
            air_quality = current.get("air_quality", {})
            pm25 = air_quality.get("pm2_5")
            pm10 = air_quality.get("pm10")
            no2 = air_quality.get("no2")
            so2 = air_quality.get("so2")
            o3 = air_quality.get("o3")
            co = air_quality.get("co")
            
            # Hitung AQI secara standar sains data dari PM2.5
            aqi_val = calculate_pm25_aqi(pm25) if pm25 is not None else None
            aqi_category = get_aqi_category(aqi_val)
            
            # Susun record baru
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
                "co": float(co) if co is not None else None
            }
            
            records.append(record)
            print(f"[OK] Berhasil memproses data {city_name}. Suhu: {temp}°C | AQI: {aqi_val} ({aqi_category})")
            
        except Exception as e:
            print(f"[-] Gagal memproses data ETL untuk {city_name} karena error: {str(e)}")
            continue

    if not records:
        print("\n[-] Tidak ada data baru yang berhasil diproses.")
        return
        
    # Memasukkan data ke Supabase
    df = pd.DataFrame(records)
    print(f"\n[+] Total data yang akan di-upsert ke Supabase: {len(df)} baris.")
    
    success_count = 0
    for record in records:
        try:
            result = supabase.table("weather_air_metrics").upsert(
                record, 
                on_conflict="city,recorded_at"
            ).execute()
            success_count += 1
        except Exception as e:
            print(f"[-] Gagal menyimpan ke database untuk {record['city']}: {str(e)}")
            
    print(f"\n[SUCCESS] Pipeline ETL Selesai dengan sukses! {success_count}/{len(records)} data tersimpan ke Supabase.")

if __name__ == "__main__":
    main()
