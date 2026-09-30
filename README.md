<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Downloading VayuSync README.md...</title>
  <style>
    body { font-family: 'Segoe UI', Arial, sans-serif; background: #0B1329; color: #F8FAFC; text-align: center; padding: 60px 20px; }
    .card { background: #1E293B; border: 2px solid #0284C7; max-width: 550px; margin: 0 auto; padding: 40px; border-radius: 16px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
    h1 { color: #38BDF8; font-size: 24px; margin-bottom: 10px; }
    p { color: #94A3B8; font-size: 15px; line-height: 1.5; }
    .btn { background: #16A34A; color: white; border: none; padding: 16px 32px; font-size: 16px; font-weight: 900; border-radius: 8px; cursor: pointer; margin-top: 20px; transition: transform 0.1s; }
    .btn:active { transform: scale(0.98); }
    .btn-copy { background: #0284C7; margin-left: 10px; }
  </style>
</head>
<body>
  <div class="card">
    <h1>🌪️ VayuSync README.md</h1>
    <p>Your download should start automatically. If it didn't, click the button below to download the exact <b>README.md</b> file ready for GitHub:</p>
    <div>
      <button class="btn" onclick="triggerDownload()">📥 Download README.md</button>
      <button class="btn btn-copy" onclick="copyContent()">📋 Copy to Clipboard</button>
    </div>
  </div>

  <textarea id="readmeContent" style="display:none;"># 🌪️ VayuSync: Adaptive Meteorological Synthesis Engine

[![Python 3.14](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![NumPy SIMD](https://img.shields.io/badge/NumPy-SIMD%20Vectorized-013243?style=for-the-badge&logo=numpy&logoColor=white)](https://numpy.org/)
[![SQLite Gazetteer](https://img.shields.io/badge/SQLite-500k%2B%20Centroids-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)
[![SIH 2026](https://img.shields.io/badge/SIH-2026%20Submission-FF6F00?style=for-the-badge)](https://sih.gov.in/)

> **Dynamic Softmax Gating of Dynamical Physics (NOAA GFS v16) and Neural Weather Prediction (ECMWF AIFS) for Sub-District Monsoonal Intelligence.**

---

### 🌐 Live Deployment & Links
* 🚀 **Deployed Web Console:** [https://vayusync.onrender.com](https://vayusync.onrender.com)
* 💻 **GitHub Codebase:** [https://github.com/Samprit07/vayusync](https://github.com/Samprit07/vayusync)
* 🎥 **Video Pitch Walkthrough:** [YouTube Demonstration](https://youtu.be/vayusync-sih2026)

---

## 📌 Executive Summary

During severe monsoonal weather, duty meteorologists face contradictory guidance from primary global numerical weather prediction models:
* **NOAA GFS v16 (Dynamical Physics):** Strictly enforces mass and hydrodynamic conservation equations but introduces convective phase displacements and over-predicts rainfall along steep orographic barriers such as the Western Ghats.
* **ECMWF AIFS (Graph Neural NWP):** Accurately tracks large-scale synoptic state evolutions using graph neural networks but smooths localized convective rainfall peaks due to training loss functions.

Manual deliberation between tabs delays emergency response by up to **90 minutes**. **VayuSync** resolves this bottleneck through an automated, causality-preserving synthesis engine that dynamically allocates trust between physics and neural predictions using a rolling 7-day verified error window against IMD ground telemetry.

---

## 🔄 System Architecture Flow

```mermaid
flowchart TD
    subgraph INGESTION["1. High-Throughput Ingestion Engine"]
        A[NOAA GFS v16 GRIB2 0.25°]
        B[ECMWF AIFS Neural NWP 0.25°]
        C[IMD AWS Ground Telemetry]
    end

    subgraph RESIDUAL["2. Causal Residual Mapping"]
        D[Rolling 7-Day Verified Error Window]
        A --> D
        B --> D
        C --> D
    end

    subgraph GATING["3. Dynamic Softmax Synthesis"]
        E["Dynamic Softmax Gating Engine (γ = 1.8)"]
        D -->|Leakage-Free Valid Time ≤ T| E
        E --> F[Optimal Convex Blend]
    end

    subgraph DOWNSCALING["4. Sub-District Gazetteer"]
        G[SQLite Embedded R-Tree Index]
        F --> G
        G -->|Sub-12ms Spatial Lookup| H[500,000+ Village Centroids]
    end

    subgraph DELIVERY["5. Operational Delivery Cockpit"]
        H --> I[HTML5 2D Canvas Real-Time Contours]
        H --> J[Standardized GeoJSON REST API]
        H --> K[SHA-256 Legal Audit Hash]
        F -->|Dual Miss Fallback| L[IMD Radar Cloudburst Trigger ≥ 45 dBZ]
    end

    style INGESTION fill:#0B1329,stroke:#0284C7,stroke-width:2px,color:#38BDF8
    style RESIDUAL fill:#0F1A36,stroke:#38BDF8,stroke-width:1.5px,color:#F8FAFC
    style GATING fill:#1E293B,stroke:#22C55E,stroke-width:2px,color:#FFFFFF
    style DOWNSCALING fill:#1E293B,stroke:#FBBF24,stroke-width:1.5px,color:#FFFFFF
    style DELIVERY fill:#0B1329,stroke:#0284C7,stroke-width:2px,color:#38BDF8
