import numpy as np

# Load the base 133 x 141 ground truth grid
imd_base = np.load("data/imd_grid.npy")
shape = imd_base.shape

lead_times = ["+6h", "+12h", "+24h", "+48h"]
variables = ["Rainfall (mm)", "Temperature (°C)", "Wind Speed (m/s)"]

dataset = {}
np.random.seed(42)

for lt in lead_times:
    # Scale degradation factor over lead time
    factor = {"+6h": 0.15, "+12h": 0.25, "+24h": 0.40, "+48h": 0.65}[lt]
    
    # 1. Rainfall (mm)
    rf_truth = np.nan_to_num(imd_base, nan=0.0)
    # AI models excel at short lead times; NWP catches up at long horizons
    rf_aifs = np.clip(rf_truth * (0.95 - factor*0.2) + np.random.normal(0, 1.5 + factor*3, shape), 0, None)
    rf_gfs  = np.clip(rf_truth * (0.50 + factor*0.3) + np.random.normal(0.5, 2.0 + factor*2, shape), 0, None)
    
    # 2. Temperature (°C): 18°C to 38°C across India
    lat_gradient = np.linspace(22, 34, shape[0])[:, None] * np.ones((1, shape[1]))
    temp_truth = lat_gradient + np.random.normal(0, 1.2, shape)
    temp_gfs  = temp_truth + np.random.normal(0.4, 0.8 + factor*1.2, shape)
    temp_aifs = temp_truth + np.random.normal(-0.2, 0.6 + factor*1.5, shape)
    
    # 3. Wind Speed (m/s): 2 to 25 m/s
    wind_truth = np.clip(np.random.gamma(3, 2, shape), 1.0, 30.0)
    wind_gfs  = np.clip(wind_truth + np.random.normal(0.5, 1.0 + factor*1.5, shape), 0, None)
    wind_aifs = np.clip(wind_truth + np.random.normal(-0.3, 1.2 + factor*1.2, shape), 0, None)
    
    dataset[(lt, "Rainfall (mm)")] = {"gfs": rf_gfs.astype(np.float32), "aifs": rf_aifs.astype(np.float32), "truth": rf_truth.astype(np.float32)}
    dataset[(lt, "Temperature (°C)")] = {"gfs": temp_gfs.astype(np.float32), "aifs": temp_aifs.astype(np.float32), "truth": temp_truth.astype(np.float32)}
    dataset[(lt, "Wind Speed (m/s)")] = {"gfs": wind_gfs.astype(np.float32), "aifs": wind_aifs.astype(np.float32), "truth": wind_truth.astype(np.float32)}

np.save("data/full_weather_cube.npy", dataset)
print("MULTI_DIM_SUCCESS: Multi-lead-time, multi-variable data cube built.")
