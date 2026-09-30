# VayuSync

### Sub-district meteorological synthesis & real-time monsoonal intelligence engine

<p align="center">
  <img src="https://img.shields.io/badge/SIH-2026-7C3AED?style=for-the-badge" alt="SIH 2026"/>
  <img src="https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python 3.14"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/NumPy-SIMD%20Vectorized-013243?style=for-the-badge&logo=numpy&logoColor=white" alt="NumPy SIMD"/>
  <img src="https://img.shields.io/badge/SQLite-500k%2B%20Centroids-003B57?style=for-the-badge&logo=sqlite&logoColor=white" alt="SQLite"/>
  <img src="https://img.shields.io/badge/HTML5%20Canvas-E34F26?style=for-the-badge&logo=html5&logoColor=white" alt="HTML5 Canvas"/>
  <img src="https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge" alt="License MIT"/>
</p>

**VayuSync** is an operational meteorological synthesis platform that bridges the gap between classical dynamical atmospheric physics (**NOAA GFS v16**) and global data-driven neural weather prediction (**ECMWF AIFS**). 

By evaluating rolling, causality-preserving error residuals against official **India Meteorological Department (IMD)** automated weather station telemetry, VayuSync dynamically allocates trust weights via temperature-scaled Softmax gating. It provides sub-district village downscaling, client-side isobaric rendering, and statutory decision support—operating on commodity CPUs with zero GPU dependency.

---

### 🌐 Live Deployment & Codebase
* 🚀 **Operational Dashboard:** [https://vayusync.onrender.com](https://vayusync.onrender.com)
* 💻 **GitHub Repository:** [https://github.com/Samprit07/vayusync](https://github.com/Samprit07/vayusync)

---

## 📌 Executive Problem Statement & Meteorological Dilemma

During active Southwest Monsoon conditions, duty forecasters and disaster management authorities must reconcile divergent model projections:
* **NOAA GFS v16 (Dynamical Physics):** Strictly enforces mass, momentum, and moisture conservation laws. However, parameterization schemes frequently over-predict precipitation totals across complex coastal orography (e.g., the Western Ghats) and suffer from convective phase displacement.
* **ECMWF AIFS (Graph Neural NWP):** Accurately captures synoptic-scale advection and global circulation patterns with minimal inference cost. However, because it is trained on smooth $L_1$/MSE objective functions, it systematically smooths out sharp convective cloudbursts.

Manual side-by-side deliberation between browser tabs delays disaster warnings by up to **90 minutes**. **VayuSync** replaces manual comparison with an automated, reproducible mathematical synthesis pipeline that executes in **under 45 seconds**.

---

## 🚀 Key Highlights & Capabilities

| Capability | Technical Realization | Operational Impact |
|---|---|---|
| **Dual-Model Gating** | Dynamic Softmax synthesis ($\gamma = 1.8$) on trailing residuals | Balances GFS orographic physical skill with AIFS neural synoptic precision |
| **Zero Future Leakage** | 7-day rolling evaluation window strictly where $\text{Valid Time} \le T_0$ | Prevents temporal data contamination during evaluation cycles |
| **Sub-District Downscale** | Embedded SQLite gazetteer with R-Tree spatial indexing | Instant spatial queries (<12ms) across 500,000+ Indian villages and tehsils |
| **Zero GPU Dependency** | NumPy SIMD vectorized broadcasting across 12,800 grid nodes | Runs entirely on standard 2-core x86 CPU servers (~₹1,200/mo) |
| **Statutory Defensibility** | Deterministic SHA-256 cryptographic audit logs | Provides evidentiary proof for District Magistrate orders under Sec 163 BNSS |
| **Instant Client UI** | Direct HTML5 2D Canvas buffer manipulation | Sub-30ms client-side isobar rendering eliminating server graphics overhead |

---

## 🏗️ System Architecture

```mermaid
flowchart TD
    subgraph INGESTION["1. Ingestion & Preprocessing Layer"]
        A[NOAA GFS v16 GRIB2 0.25° Physics Field]
        B[ECMWF AIFS NetCDF 0.25° Neural NWP Field]
        C[IMD AWS Calibrated Ground Observations]
    end

    subgraph ENGINE["2. Causal Residual & Gating Engine"]
        D["Rolling 7-Day Residual Window (T-7 to T-1)<br/>Strictly Causal: Valid Time ≤ Issue Time"]
        E["Dynamic Softmax Gating Engine (γ = 1.8)<br/>w_m = exp(-γ · MAE_m / R_norm) / Σ exp(...)"]
        F["Convex Combination Synthesis<br/>Blended Field ∈ [min(GFS, AIFS), max(GFS, AIFS)]"]
        G{"Mesoscale Cloudburst<br/>Reflectivity Spike ≥ 45 dBZ?"}
        H[Automated Radar Fallback Flag]
        
        A --> D
        B --> D
        C --> D
        D --> E
        E --> F
        F --> G
        G -->|Yes| H
    end

    subgraph SPATIAL["3. Spatial Downscaling Gazetteer"]
        I["Local SQLite Engine (Spatialite R-Tree)"]
        J["500,000+ Indian Village & Tehsil Centroids"]
        F --> I
        I --> J
    end

    subgraph COCKPIT["4. Operational Forecaster Cockpit"]
        K["HTML5 2D Canvas Isobar Contour Rendering"]
        L["Standardized GeoJSON REST API"]
        M["SHA-256 Legal Audit Trail Generator"]
        
        J --> K
        J --> L
        F --> M
    end

    style INGESTION fill:#0B1329,stroke:#0284C7,stroke-width:2px,color:#38BDF8
    style ENGINE fill:#0F1A36,stroke:#22C55E,stroke-width:2px,color:#FFFFFF
    style SPATIAL fill:#1E293B,stroke:#FBBF24,stroke-width:1.5px,color:#FFFFFF
    style COCKPIT fill:#0B1329,stroke:#0284C7,stroke-width:2px,color:#38BDF8
