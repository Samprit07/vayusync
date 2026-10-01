# VayuSync

**Hybrid AI–NWP Multi-Model Forecast Blending System**  
Smart India Hackathon 2026 · Problem Statement **26SIH082**

[![Live Demo](https://img.shields.io/badge/Live-Demo-00C853?style=for-the-badge)](https://vayusync-balh.onrender.com/)
[![SIH](https://img.shields.io/badge/SIH-26SIH082-7C3AED?style=for-the-badge)](https://github.com/Samprit07/vayusync)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

**VayuSync** dynamically blends classical numerical weather prediction (**NOAA GFS**) with data-driven neural weather prediction (**ECMWF AIFS**) using context-aware Softmax gating. It produces a single optimized forecast for rainfall, temperature, wind, humidity and pressure over the Indian domain, together with spatial model-weight maps and station-level verification against IMD-style ground truth.

Live cockpit → [https://vayusync-balh.onrender.com/](https://vayusync-balh.onrender.com/)

---

## Problem it solves

Different forecast systems excel under different conditions (region, season, lead time, weather regime). A fixed average is suboptimal. VayuSync learns **when to trust which model** and forms a convex combination:

\[
\hat{y} = w_{\text{GFS}}\,F_{\text{GFS}} + w_{\text{AIFS}}\,F_{\text{AIFS}}, \qquad
w_{\text{GFS}} + w_{\text{AIFS}} = 1,\quad w_i \ge 0
\]

Weights are produced by a lightweight adaptive gating network conditioned on location, lead time and inter-model spread.

---

## Key features

| Feature | Description |
|--------|-------------|
| **Dual-model synthesis** | GFS (physics) + AIFS (neural) fused via temperature-scaled Softmax |
| **Spatial weight maps** | Grid of \(w_{\text{GFS}}\) / \(w_{\text{AIFS}}\) showing regional model preference |
| **Station drill-down** | Fast lookup of any Indian village / town / metro via embedded SQLite gazetteer + online fallback |
| **Multi-variable support** | Rainfall, 2 m temperature, 10 m wind, relative humidity, MSLP |
| **Lead-time horizons** | +6 h, +12 h, +24 h, +48 h |
| **Verification metrics** | MAE of GFS, AIFS and blended field vs reference truth; skill improvement % |
| **Operational cockpit** | Dark-mode browser UI (Plotly density maps, real-time station panel) |
| **CPU-only path** | Pure NumPy vectorization — no GPU required |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Forecaster Cockpit (frontend/)                             │
│  HTML · CSS · JS · Plotly  ·  station search · map views    │
└──────────────────────────┬──────────────────────────────────┘
                           │  REST (/api/forecast, /api/station)
┌──────────────────────────▼──────────────────────────────────┐
│  FastAPI Backend (backend/main.py)                          │
│  CORS · static mount · gazetteer · geocoding cache          │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  Adaptive Gating Engine (backend/ml_engine.py)              │
│  Softmax network → w_GFS, w_AIFS → convex blend             │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│  Data Layer (data/)                                         │
│  full_weather_cube.npy · gfs/aifs/imd grids · gazetteer.db  │
└─────────────────────────────────────────────────────────────┘
```

---

## Project structure

```text
vayusync/
├── backend/
│   ├── main.py              # FastAPI app, station lookup, API routes
│   ├── ml_engine.py         # Adaptive Softmax gating + blend
│   └── build_gazetteer.py   # Utility to rebuild village DB
├── frontend/                # Operational cockpit (served as static files)
│   ├── index.html
│   ├── app.js
│   ├── style.css
│   └── logo-*.svg
├── data/
│   ├── full_weather_cube.npy
│   ├── gfs_grid.npy / aifs_grid.npy / imd_grid.npy
│   ├── india_gazetteer.db   # ~50 MB village / place index
│   ├── processed_aifs_india.nc
│   └── resolved_stations.json
├── app.py                   # Optional Streamlit demo portal
├── api/index.py             # Thin entry for some hosts
├── Procfile                 # Render / Heroku: uvicorn backend.main:app
├── requirements.txt
├── LICENSE                  # MIT
└── README.md
```

---

## Quick start (local)

```bash
git clone https://github.com/Samprit07/vayusync.git
cd vayusync

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
# Additional runtime deps used by the live app:
pip install fastapi uvicorn numpy plotly geopy streamlit

# Start the FastAPI + cockpit server
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Open **http://127.0.0.1:8000**

API docs (when running):  
- Swagger → http://127.0.0.1:8000/docs  
- ReDoc → http://127.0.0.1:8000/redoc  

Optional Streamlit demo:

```bash
streamlit run app.py
```

---

## API endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/forecast?lead_time=+24h&variable=Rainfall (mm)` | Full India grid: blended field, GFS weight map, MAE metrics |
| `GET /api/station?query=Panaji&lead_time=+24h&variable=Rainfall (mm)` | Point forecast + model weights + observed reference for a named location |

**Example response (station)**

```json
{
  "status": "success",
  "station_name": "Panaji, Goa",
  "lat": 15.49,
  "lon": 73.83,
  "values": {
    "gfs": 12.4,
    "aifs": 15.1,
    "blend": 14.2,
    "observed": 13.8,
    "w_gfs_pct": 38.0,
    "w_aifs_pct": 62.0
  }
}
```

---

## How the blending works

1. **Ingest** pre-aligned GFS and AIFS fields (and a reference “truth” grid for verification).
2. **Feature vector** at each grid cell: normalized latitude, longitude, lead time, inter-model spread.
3. **AdaptiveGatingNetwork** (small MLP + Softmax) emits \(w_{\text{GFS}}, w_{\text{AIFS}}\).
4. **Convex blend** \(\hat{y} = w_{\text{GFS}} F_{\text{GFS}} + w_{\text{AIFS}} F_{\text{AIFS}}\).
5. **Verification** against the reference field → MAE and relative skill gain.

Rainfall uses the stored multi-source cube; other variables are synthesised with physically plausible spatial structure for demonstration when full multi-variable historical archives are not yet ingested.

---

## Data sources (prototype)

| Source | Role |
|--------|------|
| **NOAA GFS** | Dynamical NWP forecast fields |
| **ECMWF AIFS** | AI / neural weather prediction fields |
| **IMD-style grids** | Reference / verification rainfall (0.25°) |
| **Indian village gazetteer** | Sub-district & place name → lat/lon (SQLite) |

The repository ships with pre-processed NumPy cubes and a ready-to-use gazetteer so the demo runs offline after clone.

---

## Tech stack

- **Backend**: FastAPI, NumPy, SQLite  
- **Frontend**: Vanilla JS, Plotly.js, custom dark operational CSS  
- **Optional UI**: Streamlit  
- **Deployment**: Render (Procfile → `uvicorn backend.main:app`)

---

## Design principles

1. **Physics + learning** — models are gated, never blindly averaged.  
2. **Transparency** — every station query returns individual model values and the assigned weights.  
3. **Locality** — products resolve to village / town scale via the gazetteer.  
4. **Operational simplicity** — single process, static frontend, CPU-only math.  
5. **Reproducibility** — frozen weather cube + deterministic gating seed for demos.

---

## License

MIT License © 2026 Samprit Dhara  
See [LICENSE](LICENSE).

---

**VayuSync** — from global model fields to village-scale monsoonal decisions.
