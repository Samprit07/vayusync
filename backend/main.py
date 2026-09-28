import os
import sys
import json
import sqlite3
import urllib.request
import urllib.parse

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

for path in [CURRENT_DIR, PROJECT_ROOT]:
    if path not in sys.path:
        sys.path.insert(0, path)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import numpy as np
import difflib
from ml_engine import compute_ml_blend

app = FastAPI(title="VayuSync API", version="2.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

data_cube_path = os.path.join(PROJECT_ROOT, "data", "full_weather_cube.npy")
data_cube = np.load(data_cube_path, allow_pickle=True).item()

DB_PATH = os.path.join(PROJECT_ROOT, "data", "india_gazetteer.db")
CACHE_PATH = os.path.join(PROJECT_ROOT, "data", "resolved_stations.json")

def load_disk_cache():
    if os.path.exists(CACHE_PATH):
        try:
            with open(CACHE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_disk_cache(cache):
    try:
        with open(CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

STATION_CACHE = load_disk_cache()

# ==============================================================================
# AUTHORITATIVE METROPOLITAN & DISTRICT REGISTRY (Instant 0ms Resolution)
# ==============================================================================
MASTER_METRO_REGISTRY = {
    "bandra": (19.06, 72.84, "Bandra, Mumbai (Maharashtra)"),
    "bandra west": (19.06, 72.83, "Bandra West, Mumbai (MH)"),
    "bandra east": (19.06, 72.85, "Bandra East, Mumbai (MH)"),
    "andheri": (19.11, 72.84, "Andheri, Mumbai (MH)"),
    "juhu": (19.10, 72.83, "Juhu, Mumbai (MH)"),
    "dadar": (19.02, 72.84, "Dadar, Mumbai (MH)"),
    "borivali": (19.23, 72.86, "Borivali, Mumbai (MH)"),
    "colaba": (18.91, 72.81, "Colaba, Mumbai (MH)"),
    "powai": (19.12, 72.91, "Powai, Mumbai (MH)"),
    "kurla": (19.07, 72.88, "Kurla, Mumbai (MH)"),
    "chembur": (19.05, 72.90, "Chembur, Mumbai (MH)"),
    "mumbai": (19.08, 72.88, "Mumbai, Maharashtra"),
    "pune": (18.52, 73.86, "Pune, Maharashtra"),
    "nagpur": (21.15, 79.08, "Nagpur, Maharashtra"),
    "delhi": (28.61, 77.20, "New Delhi, NCT"),
    "new delhi": (28.61, 77.20, "New Delhi, NCT"),
    "connaught place": (28.63, 77.22, "Connaught Place, Delhi"),
    "noida": (28.54, 77.39, "Noida, Uttar Pradesh"),
    "gurgaon": (28.46, 77.03, "Gurugram (Gurgaon), Haryana"),
    "gurugram": (28.46, 77.03, "Gurugram, Haryana"),
    "chandigarh": (30.73, 76.78, "Chandigarh UT"),
    "kashmir": (34.08, 74.80, "Srinagar (Kashmir Valley)"),
    "srinagar": (34.08, 74.80, "Srinagar, J&K"),
    "bengaluru": (12.97, 77.59, "Bengaluru, Karnataka"),
    "bangalore": (12.97, 77.59, "Bengaluru, Karnataka"),
    "chennai": (13.08, 80.27, "Chennai, Tamil Nadu"),
    "hyderabad": (17.38, 78.48, "Hyderabad, Telangana"),
    "goa": (15.49, 73.83, "Goa (HQ: Panaji)"),
    "panaji": (15.49, 73.83, "Panaji, Goa"),
    "panjim": (15.49, 73.83, "Panaji (Panjim), Goa"),
    "margao": (15.28, 73.99, "Margao, Goa"),
    "vasco": (15.40, 73.81, "Vasco da Gama, Goa"),
    "veroda": (15.19, 73.99, "Veroda, Goa"),
    "cuncolim": (15.18, 73.99, "Cuncolim, Goa"),
    "kolkata": (22.57, 88.36, "Kolkata, West Bengal"),
    "jalpaiguri": (26.52, 88.73, "Jalpaiguri, West Bengal"),
    "siliguri": (26.72, 88.43, "Siliguri, West Bengal"),
    "patna": (25.59, 85.14, "Patna, Bihar"),
    "ahmedabad": (23.02, 72.57, "Ahmedabad, Gujarat")
}

def query_online_geocoder(query_str):
    try:
        encoded = urllib.parse.quote(f"{query_str}, India")
        url = f"https://photon.komoot.io/api/?q={encoded}&limit=1"
        req = urllib.request.Request(url, headers={"User-Agent": "VayuSync-SIH2026/2.0"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data and data.get("features"):
                feat = data["features"][0]
                coords = feat["geometry"]["coordinates"]
                props = feat.get("properties", {})
                country = props.get("country", "")
                if country.lower() == "india" or not country:
                    lon, lat = coords[0], coords[1]
                    name = props.get("name", query_str.title())
                    state = props.get("state", "")
                    full_name = f"{name} ({state})" if state else name
                    return lat, lon, full_name
    except Exception:
        pass
    return None, None, None

def query_gazetteer(query_str):
    q_norm = query_str.strip().lower()

    if q_norm in MASTER_METRO_REGISTRY:
        lat, lon, name = MASTER_METRO_REGISTRY[q_norm]
        return lat, lon, name

    if q_norm in STATION_CACHE:
        c = STATION_CACHE[q_norm]
        return c["lat"], c["lon"], c["name"]

    if "," in q_norm:
        p_name = q_norm.split(",")[0].strip()
        if p_name in MASTER_METRO_REGISTRY:
            lat, lon, name = MASTER_METRO_REGISTRY[p_name]
            return lat, lon, name

    lat, lon, resolved_name = query_online_geocoder(query_str)
    if lat and lon and (5.0 <= lat <= 38.0 and 65.0 <= lon <= 100.0):
        STATION_CACHE[q_norm] = {"lat": lat, "lon": lon, "name": resolved_name}
        save_disk_cache(STATION_CACHE)
        return lat, lon, resolved_name

    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("""
            SELECT name, lat, lon FROM places 
            WHERE name_lower = ? 
            ORDER BY weight DESC LIMIT 1
        """, (q_norm,))
        row = cur.fetchone()
        if row:
            conn.close()
            return row[1], row[2], row[0]

        cur.execute("""
            SELECT name, lat, lon FROM places 
            WHERE name_lower LIKE ? 
            ORDER BY weight DESC LIMIT 1
        """, (f"{q_norm}%",))
        row = cur.fetchone()
        if row:
            conn.close()
            return row[1], row[2], row[0]

        cur.execute("SELECT DISTINCT name FROM places WHERE name_lower LIKE ? LIMIT 20", (f"{q_norm[:3]}%",))
        candidates = [r[0] for r in cur.fetchall()]
        conn.close()
        suggestions = difflib.get_close_matches(query_str.strip().title(), candidates, n=3, cutoff=0.5)
        return None, None, suggestions

    return None, None, []

@app.get("/api/forecast")
def get_forecast(lead_time: str = "+24h", variable: str = "Rainfall (mm)"):
    fg, fa, blend, truth, w_gfs, w_aifs, lats, lons = compute_ml_blend(data_cube, lead_time, variable)
    
    mae_gfs = float(np.mean(np.abs(fg - truth)))
    mae_aifs = float(np.mean(np.abs(fa - truth)))
    mae_blend = float(np.mean(np.abs(blend - truth)))

    best_individual = min(mae_gfs, mae_aifs)
    improvement = ((best_individual - mae_blend) / best_individual) * 100.0

    return {
        "lead_time": lead_time,
        "variable": variable,
        "metrics": {
            "mae_gfs": round(mae_gfs, 2),
            "mae_aifs": round(mae_aifs, 2),
            "mae_blend": round(mae_blend, 2),
            "improvement_pct": round(improvement, 1)
        },
        "lats": lats.tolist(),
        "lons": lons.tolist(),
        "blend_grid": blend.tolist(),
        "gfs_weight_grid": w_gfs.tolist()
    }

@app.get("/api/station")
def get_station(query: str = "Panaji", lead_time: str = "+24h", variable: str = "Rainfall (mm)"):
    lat, lon, res_name = query_gazetteer(query)

    if lat is None or lon is None:
        suggestions = res_name if isinstance(res_name, list) else []
        return {
            "status": "error",
            "message": "Location not recognized in Indian Administrative Registry.",
            "suggestions": suggestions
        }

    fg, fa, blend, truth, w_gfs, w_aifs, lats, lons = compute_ml_blend(data_cube, lead_time, variable)
    
    r = int(np.clip(np.argmin(np.abs(lats - lat)), 0, 132))
    c = int(np.clip(np.argmin(np.abs(lons - lon)), 0, 140))

    return {
        "status": "success",
        "station_name": res_name,
        "lat": round(lat, 2),
        "lon": round(lon, 2),
        "lead_time": lead_time,
        "variable": variable,
        "values": {
            "gfs": round(float(fg[r, c]), 1),
            "aifs": round(float(fa[r, c]), 1),
            "blend": round(float(blend[r, c]), 1),
            "observed": round(float(truth[r, c]), 1),
            "w_gfs_pct": round(float(w_gfs[r, c]) * 100, 1),
            "w_aifs_pct": round(float(w_aifs[r, c]) * 100, 1)
        }
    }

# Mount static frontend
STATIC_DIR = os.path.join(PROJECT_ROOT, "frontend")
if not os.path.exists(STATIC_DIR):
    STATIC_DIR = os.path.join(PROJECT_ROOT, "public")

if os.path.exists(STATIC_DIR):
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
