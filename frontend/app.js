const API_BASE = "http://127.0.0.1:8000/api";

const leadSelect = document.getElementById("leadTimeSelect");
const varSelect = document.getElementById("variableSelect");
const stationInput = document.getElementById("stationInput");
const searchBtn = document.getElementById("searchBtn");
const searchAlert = document.getElementById("searchAlert");
const suggestionsBox = document.getElementById("suggestionsBox");
const liveUtcClock = document.getElementById("liveUtcClock");
const themeToggleBtn = document.getElementById("themeToggleBtn");
const appLogo = document.getElementById("appLogo");

const btnBlendView = document.getElementById("btnBlendView");
const btnWeightView = document.getElementById("btnWeightView");

let currentLat = 15.49;
let currentLon = 73.83;
let currentCityName = "Panaji";
let activeTab = "blend";
let latestForecastData = null;
let currentTheme = localStorage.getItem("vayusync_theme") || "dark";

function applyTheme(theme) {
    currentTheme = theme;
    localStorage.setItem("vayusync_theme", theme);
    document.documentElement.setAttribute("data-theme", theme);
    themeToggleBtn.innerText = `MODE: ${theme.toUpperCase()}`;
    appLogo.src = (theme === "light") ? "logo-light.svg" : "logo-dark.svg";
    renderMap();
}

themeToggleBtn.addEventListener("click", () => {
    applyTheme(currentTheme === "dark" ? "light" : "dark");
});

function updateClock() {
    const now = new Date();
    liveUtcClock.innerText = `UTC ${now.toISOString().slice(11, 19)}Z`;
}
setInterval(updateClock, 1000);
updateClock();

function getVariableConfig(variable, grid) {
    let flat = grid.flat();
    let min = Math.min(...flat);
    let max = Math.max(...flat);

    if (variable.includes("Rainfall")) {
        return { cscale: "Blues", zmin: 0, zmax: Math.max(35, max), unit: "mm", label: "Precipitation" };
    } else if (variable.includes("Temp")) {
        return { cscale: "YlOrRd", zmin: Math.floor(min), zmax: Math.ceil(max), unit: "°C", label: "Surface Temp" };
    } else if (variable.includes("Wind")) {
        return { cscale: "Viridis", zmin: 0, zmax: Math.max(20, max), unit: "m/s", label: "Wind Speed" };
    } else if (variable.includes("Humidity")) {
        return { cscale: "YlGnBu", zmin: Math.max(20, Math.floor(min)), zmax: 100, unit: "%", label: "Humidity" };
    } else {
        return { cscale: "Portland", zmin: Math.floor(min), zmax: Math.ceil(max), unit: "hPa", label: "Pressure" };
    }
}

function renderMap() {
    if (!latestForecastData) return;
    const data = latestForecastData;
    const variable = varSelect.value;
    const config = getVariableConfig(variable, data.blend_grid);

    let flatLats = [];
    let flatLons = [];
    let flatVals = [];
    let flatWeights = [];

    const step = 2;
    for (let r = 0; r < data.lats.length; r += step) {
        for (let c = 0; c < data.lons.length; c += step) {
            flatLats.push(data.lats[r]);
            flatLons.push(data.lons[c]);
            flatVals.push(data.blend_grid[r][c]);
            flatWeights.push(data.gfs_weight_grid[r][c]);
        }
    }

    const isLight = (currentTheme === "light");
    const esriBase = isLight
        ? "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Light_Gray_Base/MapServer/tile/{z}/{y}/{x}"
        : "https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}";
    
    const fontColor = isLight ? "#334155" : "#94a3b8";
    const paperBg = isLight ? "#ffffff" : "#111622";
    const pinColor = isLight ? "#dc2626" : "#ef4444";
    const pinTextColor = isLight ? "#0f172a" : "#f8fafc";

    const operationalMapboxLayout = {
        style: "white-bg",
        layers: [
            { sourcetype: "raster", source: [esriBase], below: "traces" },
            { sourcetype: "raster", source: ["https://server.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}"] }
        ],
        center: { lat: 22.0, lon: 82.0 },
        zoom: 3.8
    };

    // Clean, professional hover template (Removes ugly 'trace 0')
    const valHoverTemplate = (activeTab === "blend")
        ? `<b>${config.label}</b>: %{z:.1f} ${config.unit}<br>Lat: %{lat:.2f}°N | Lon: %{lon:.2f}°E<extra></extra>`
        : `<b>GFS Weight Allocation</b>: %{z:.2f}<br>Lat: %{lat:.2f}°N | Lon: %{lon:.2f}°E<extra></extra>`;

    const rasterTrace = {
        type: "densitymapbox",
        name: (activeTab === "blend") ? config.label : "Weight Map",
        lat: flatLats,
        lon: flatLons,
        z: (activeTab === "blend") ? flatVals : flatWeights,
        radius: 17,
        opacity: isLight ? 0.72 : 0.82,
        colorscale: (activeTab === "blend") ? config.cscale : "Spectral_r",
        zmin: (activeTab === "blend") ? config.zmin : 0,
        zmax: (activeTab === "blend") ? config.zmax : 1,
        hovertemplate: valHoverTemplate,
        colorbar: {
            title: {
                text: (activeTab === "blend") ? config.unit : "w_GFS",
                font: { family: "JetBrains Mono, monospace", size: 10, color: fontColor }
            },
            tickfont: { family: "JetBrains Mono, monospace", size: 10, color: fontColor },
            thickness: 12,
            len: 0.85
        }
    };

    const targetTrace = {
        type: "scattermapbox",
        name: "Selected Station",
        lat: [currentLat],
        lon: [currentLon],
        mode: "markers+text",
        marker: { size: 10, color: pinColor },
        text: [currentCityName],
        textposition: "top right",
        textfont: { family: "IBM Plex Sans, sans-serif", size: 11, color: pinTextColor },
        hovertemplate: `<b>%{text}</b><br>Lat: %{lat:.2f}°N | Lon: %{lon:.2f}°E<extra></extra>`
    };

    Plotly.react("mapViewport", [rasterTrace, targetTrace], {
        autosize: true,
        margin: { l: 0, r: 0, t: 0, b: 0 },
        paper_bgcolor: paperBg,
        mapbox: operationalMapboxLayout
    }, { responsive: true, displayModeBar: false });
}

async function loadForecastData() {
    const lead = leadSelect.value;
    const variable = varSelect.value;

    const res = await fetch(`${API_BASE}/forecast?lead_time=${encodeURIComponent(lead)}&variable=${encodeURIComponent(variable)}`);
    const data = await res.json();
    latestForecastData = data;

    const unit = variable.split(" ")[1]?.replace(/[()]/g, "") || "";
    document.getElementById("maeGFS").innerText = `${data.metrics.mae_gfs} ${unit}`;
    document.getElementById("maeAIFS").innerText = `${data.metrics.mae_aifs} ${unit}`;
    document.getElementById("maeBlend").innerText = `${data.metrics.mae_blend} ${unit}`;

    const gain = data.metrics.improvement_pct;
    const skillElem = document.getElementById("skillGain");
    if (gain >= 0) {
        skillElem.innerText = `+${gain}%`;
        skillElem.className = "metric-cell-val text-success";
    } else {
        skillElem.innerText = `${gain}%`;
        skillElem.className = "metric-cell-val text-danger";
    }

    renderMap();
}

async function loadStation(cityName) {
    const lead = leadSelect.value;
    const variable = varSelect.value;

    searchAlert.innerHTML = "";
    suggestionsBox.innerHTML = "";

    const res = await fetch(`${API_BASE}/station?query=${encodeURIComponent(cityName)}&lead_time=${encodeURIComponent(lead)}&variable=${encodeURIComponent(variable)}`);
    const data = await res.json();

    if (data.status === "error") {
        searchAlert.innerHTML = `<div class="sys-msg sys-msg-error">${data.message}</div>`;
        if (data.suggestions && data.suggestions.length > 0) {
            let pillsHtml = `<div class="suggestion-wrap">`;
            data.suggestions.forEach(s => {
                pillsHtml += `<span class="sugg-chip" onclick="quickSelect('${s}')">${s}</span>`;
            });
            pillsHtml += `</div>`;
            suggestionsBox.innerHTML = pillsHtml;
        }
        return;
    }

    currentLat = data.lat;
    currentLon = data.lon;
    currentCityName = data.station_name;

    const unit = variable.split(" ")[1]?.replace(/[()]/g, "") || "";
    document.getElementById("stnName").innerText = `Station: ${data.station_name}`;
    document.getElementById("stnCoords").innerText = `${data.lat.toFixed(2)}°N, ${data.lon.toFixed(2)}°E`;
    
    document.getElementById("stnGFS").innerText = `${data.values.gfs} ${unit}`;
    document.getElementById("stnAIFS").innerText = `${data.values.aifs} ${unit}`;
    document.getElementById("stnBlend").innerText = `${data.values.blend} ${unit}`;
    document.getElementById("stnTruth").innerText = `${data.values.observed} ${unit}`;
    
    document.getElementById("stnWGFS").innerText = `${data.values.w_gfs_pct}%`;
    document.getElementById("stnWAIFS").innerText = `${data.values.w_aifs_pct}%`;

    loadForecastData();
}

window.quickSelect = function(name) {
    stationInput.value = name;
    loadStation(name);
};

searchBtn.addEventListener("click", () => {
    const q = stationInput.value.trim();
    if (q) loadStation(q);
});

stationInput.addEventListener("keypress", (e) => {
    if (e.key === "Enter") {
        const q = stationInput.value.trim();
        if (q) loadStation(q);
    }
});

btnBlendView.addEventListener("click", () => {
    activeTab = "blend";
    btnBlendView.classList.add("active");
    btnWeightView.classList.remove("active");
    renderMap();
});

btnWeightView.addEventListener("click", () => {
    activeTab = "weight";
    btnWeightView.classList.add("active");
    btnBlendView.classList.remove("active");
    renderMap();
});

leadSelect.addEventListener("change", () => loadStation(currentCityName));
varSelect.addEventListener("change", () => loadStation(currentCityName));

applyTheme(currentTheme);
loadStation("Panaji");
