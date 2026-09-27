import os
import sys
import zipfile
import sqlite3
import math

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
DB_PATH = os.path.join(DATA_DIR, "india_gazetteer.db")
ZIP_PATH = os.path.join(DATA_DIR, "IN.zip")
TXT_PATH = os.path.join(DATA_DIR, "IN.txt")

if not os.path.exists(ZIP_PATH):
    print("Error: data/IN.zip not found.")
    sys.exit(1)

print("1. Extracting IN.txt from archive...")
with zipfile.ZipFile(ZIP_PATH, 'r') as zf:
    zf.extract("IN.txt", DATA_DIR)

print("2. Re-compiling SQLite Database with Population & Administrative Weights...")
conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("DROP TABLE IF EXISTS places")
cur.execute("""
    CREATE TABLE places (
        id INTEGER PRIMARY KEY,
        name TEXT,
        name_lower TEXT,
        lat REAL,
        lon REAL,
        fcode TEXT,
        admin1 TEXT,
        population INTEGER,
        weight REAL
    )
""")

# Administrative Rank Multipliers
FCODE_WEIGHTS = {
    "PPLC": 50.0,   # National Capital (New Delhi)
    "PPLA": 35.0,   # State Capital (Mumbai, Kolkata, Panaji, Jaipur, etc.)
    "PPLA2": 25.0,  # District Headquarters / Major Metros
    "PPLA3": 15.0,  # Sub-district / Tehsil HQ
    "PPL": 5.0,     # Populated Place / Suburb / Village
    "ADM1": 40.0,   # First-order administrative division (States)
    "ADM2": 25.0    # Second-order administrative division (Districts)
}

records = []
batch_size = 25000
count = 0

with open(TXT_PATH, "r", encoding="utf-8") as f:
    for line in f:
        parts = line.strip().split("\t")
        if len(parts) >= 15:
            fclass = parts[6]
            fcode = parts[7]
            
            if fclass in ("P", "A"):
                primary_name = parts[1]
                alt_names_raw = parts[3].split(",") if parts[3] else []
                lat = float(parts[4])
                lon = float(parts[5])
                admin1 = parts[10]
                
                try:
                    population = int(parts[14])
                except (ValueError, IndexError):
                    population = 0

                # Ensure coordinates lie within the Indian forecast grid
                if 5.0 <= lat <= 38.0 and 65.0 <= lon <= 100.0:
                    admin_bonus = FCODE_WEIGHTS.get(fcode, 2.0)
                    pop_score = math.log10(population + 1) * 6.0
                    total_weight = round(admin_bonus + pop_score, 2)

                    # Index primary name
                    records.append((primary_name, primary_name.strip().lower(), lat, lon, fcode, admin1, population, total_weight))
                    count += 1

                    # Index alternate names (e.g., historical spellings like Bombay, Panjim, etc.)
                    for alt in alt_names_raw:
                        alt_clean = alt.strip().lower()
                        if len(alt_clean) >= 3 and alt_clean != primary_name.lower():
                            records.append((primary_name, alt_clean, lat, lon, fcode, admin1, population, total_weight))
                            count += 1

                if len(records) >= batch_size:
                    cur.executemany("INSERT INTO places (name, name_lower, lat, lon, fcode, admin1, population, weight) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", records)
                    records = []

if records:
    cur.executemany("INSERT INTO places (name, name_lower, lat, lon, fcode, admin1, population, weight) VALUES (?, ?, ?, ?, ?, ?, ?, ?)", records)

print("3. Building composite index (name_lower + weight DESC)...")
cur.execute("CREATE INDEX idx_name_weight ON places (name_lower, weight DESC)")
conn.commit()
conn.close()

if os.path.exists(TXT_PATH):
    os.remove(TXT_PATH)

print(f"Success! Indexed {count:,} weighted entries into {DB_PATH}")
