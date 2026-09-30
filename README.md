# VayuSync

### Sub-district meteorological synthesis & real-time monsoonal intelligence

<p align="center">
  <img src="https://img.shields.io/badge/SIH-2026-7C3AED?style=for-the-badge" alt="SIH 2026"/>
  <img src="https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.14"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/SQLite-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite"/>
  <img src="https://img.shields.io/badge/HTML5%20Canvas-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML5 Canvas"/>
  <img src="https://img.shields.io/badge/Dark%20Console-0E0B16?style=for-the-badge" alt="Dark Console"/>
</p>

**VayuSync** is an operational meteorological synthesis engine that resolves conflicting predictions between dynamical physics (NOAA GFS v16) and neural weather forecasting (ECMWF AIFS).

Built for **operational speed and defensibility**: dynamic Softmax gating against ground truth, sub-12ms village gazetteer downscaling, and instant alert workflows without heavy GPU infrastructure.

---

## Highlights

| Capability | What it delivers |
|---|---|
| **Dual-model synthesis** | Dynamic Softmax weighting balancing GFS physics with AIFS neural skill[cite: 7] |
| **Causal verification** | 7-day trailing residual window strictly free of future-data leakage[cite: 6] |
| **Sub-district drill-down** | 500k+ Indian village centroids resolved in <12ms via embedded SQLite[cite: 8, 11] |
| **Forecaster cockpit** | Client-side 2D Canvas isobar rendering with zero server lag[cite: 8] |
| **Statutory defensibility** | Cryptographic SHA-256 audit logs supporting Sec 163 BNSS disaster orders |
| **Zero GPU footprint** | SIMD NumPy vectorization runs entirely on a commodity 2-core x86 CPU[cite: 11] |

---

## Architecture

```mermaid
flowchart TB
    A["Operational Forecaster Cockpit<br/>HTML5 2D Canvas · Bootstrap 5 · GeoJSON contours"]
    B["FastAPI ASGI Backend<br/>GRIB2 ingest · Dynamic Softmax gating · SQLite spatial lookup · SHA-256 audit"]
    C["Data & Ingestion Engine<br/>NOAA GFS v16 · ECMWF AIFS · IMD AWS ground telemetry · 500k+ gazetteer"]

    A -->|"REST + GeoJSON"| B
    B --> C
