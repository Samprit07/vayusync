import numpy as np

class AdaptiveGatingNetwork:
    def __init__(self, in_features=4, hidden_units=8):
        np.random.seed(42)
        self.W1 = np.random.randn(in_features, hidden_units) * 0.15
        self.b1 = np.zeros(hidden_units)
        self.W2 = np.random.randn(hidden_units, 2) * 0.15
        self.b2 = np.array([0.0, 0.2])

    def softmax(self, z):
        exp_z = np.exp(z - np.max(z, axis=-1, keepdims=True))
        return exp_z / np.sum(exp_z, axis=-1, keepdims=True)

    def predict_weights(self, lat_grid, lon_grid, lead_hours, fg, fa):
        lat_norm = (lat_grid - 5.0) / 33.0
        lon_norm = (lon_grid - 65.0) / 35.0
        lead_norm = np.full_like(lat_norm, lead_hours / 48.0)
        
        spread = np.abs(fg - fa)
        spread_norm = spread / (np.max(spread) + 1e-5)

        X = np.stack([lat_norm.ravel(), lon_norm.ravel(), lead_norm.ravel(), spread_norm.ravel()], axis=1)
        h = np.maximum(0, np.dot(X, self.W1) + self.b1)
        logits = np.dot(h, self.W2) + self.b2
        weights = self.softmax(logits)

        w_gfs = np.clip(weights[:, 0].reshape(lat_grid.shape), 0.05, 0.95)
        w_aifs = 1.0 - w_gfs
        return w_gfs, w_aifs

ml_gater = AdaptiveGatingNetwork()

def smooth_field(grid, passes=4):
    g = grid.copy()
    for _ in range(passes):
        p = np.pad(g, 1, mode="edge")
        g = (p[:-2, :-2] + p[:-2, 1:-1] + p[:-2, 2:] +
             p[1:-1, :-2] + p[1:-1, 1:-1] + p[1:-1, 2:] +
             p[2:, :-2] + p[2:, 1:-1] + p[2:, 2:]) / 9.0
    return g

def compute_ml_blend(data_cube, lead_str, var_name):
    lead_hours_map = {"+6h": 6, "+12h": 12, "+24h": 24, "+48h": 48}
    hours = lead_hours_map.get(lead_str, 24)

    lats = np.linspace(38.0, 5.0, 133)
    lons = np.linspace(65.0, 100.0, 141)
    lon_grid, lat_grid = np.meshgrid(lons, lats)
    shape = lat_grid.shape

    if "Rainfall" in var_name:
        entry = data_cube.get((lead_str, "Rainfall (mm)"), list(data_cube.values())[0])
        fg, fa, truth = entry["gfs"], entry["aifs"], entry["truth"]

    elif "Temperature" in var_name:
        # Realistic North-South thermal gradient + continental heating
        truth = 36.0 - 0.55 * (lat_grid - 8.0) + 0.1 * (lon_grid - 75.0)
        truth = smooth_field(truth + np.random.normal(0, 1.2, shape), passes=3)
        fg = truth + smooth_field(np.random.normal(0.4, 0.8, shape), passes=2)
        fa = truth + smooth_field(np.random.normal(-0.2, 0.6, shape), passes=2)

    elif "Wind Speed" in var_name:
        # Synoptic Monsoon Jet Stream flowing southwest to northeast
        monsoon_corridor = np.exp(-((lat_grid - 15.0)**2 / 60.0)) * np.exp(-((lon_grid - 72.0)**2 / 90.0))
        truth = 6.0 + 16.0 * monsoon_corridor + 4.0 * np.sin(lat_grid / 4.0)
        truth = np.clip(smooth_field(truth, passes=5), 0.5, 30.0)
        fg = np.clip(truth + smooth_field(np.random.normal(0.5, 1.2, shape), passes=3), 0, None)
        fa = np.clip(truth + smooth_field(np.random.normal(-0.3, 0.9, shape), passes=3), 0, None)

    elif "Humidity" in var_name:
        # Coastal high humidity vs dry continental interior
        coastal_dist = np.minimum(np.abs(lon_grid - 70.0), np.abs(lon_grid - 88.0))
        truth = 88.0 - 1.2 * coastal_dist + 5.0 * np.cos(lat_grid / 5.0)
        truth = np.clip(smooth_field(truth, passes=4), 25.0, 98.0)
        fg = np.clip(truth + smooth_field(np.random.normal(0, 3.0, shape), passes=2), 20.0, 100.0)
        fa = np.clip(truth + smooth_field(np.random.normal(0, 2.0, shape), passes=2), 20.0, 100.0)

    else: # Pressure (hPa)
        # Broad synoptic low pressure trough over North India, higher pressure in South
        truth = 1012.0 - 0.35 * (lat_grid - 8.0) + 0.08 * (lon_grid - 75.0)
        truth = smooth_field(truth, passes=6)
        fg = truth + smooth_field(np.random.normal(0.2, 0.5, shape), passes=2)
        fa = truth + smooth_field(np.random.normal(-0.1, 0.4, shape), passes=2)

    w_gfs, w_aifs = ml_gater.predict_weights(lat_grid, lon_grid, hours, fg, fa)
    blend = (w_gfs * fg) + (w_aifs * fa)

    return fg, fa, blend, truth, w_gfs, w_aifs, lats, lons
