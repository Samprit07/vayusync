import numpy as np
import xarray as xr
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split

# 1. Load Datasets
gfs_ds = xr.open_dataset(
    "data/raw/gfs_20260924_12z_f024.grib2", engine="cfgrib"
)
gfs_rain = gfs_ds["tp"]
if gfs_rain.latitude.values[0] < gfs_rain.latitude.values[-1]:
    gfs_rain = gfs_rain.reindex(latitude=gfs_rain.latitude.values[::-1])

aifs_ds = xr.open_dataset(
    "data/raw/aifs_20260924_12z_f024.grib2", engine="cfgrib"
)
aifs_rain = aifs_ds["tp"].sel(
    latitude=slice(38.0, 5.0), longitude=slice(65.0, 100.0)
)

raw_bytes = np.fromfile("data/raw/25092026.grd", dtype=np.float32)
imd_grid = np.where(
    raw_bytes.reshape((281, 241)) == -999.0,
    np.nan,
    raw_bytes.reshape((281, 241)),
)
imd_da = xr.DataArray(
    imd_grid,
    coords=[
        ("latitude", np.linspace(-30.0, 40.0, 281)),
        ("longitude", np.linspace(50.0, 110.0, 241)),
    ],
    name="imd_rf",
)
imd_rain = imd_da.sel(
    latitude=gfs_rain.latitude, longitude=gfs_rain.longitude, method="nearest"
)

# 2. Extract Flattened Feature Vectors
lats, lons = np.meshgrid(
    gfs_rain.latitude.values, gfs_rain.longitude.values, indexing="ij"
)

y_true = imd_rain.values.ravel()
f_gfs = gfs_rain.values.ravel()
f_aifs = aifs_rain.values.ravel()
flat_lats = lats.ravel()
flat_lons = lons.ravel()

valid_mask = ~np.isnan(y_true) & ~np.isnan(f_gfs) & ~np.isnan(f_aifs)

y = y_true[valid_mask]
fg = f_gfs[valid_mask]
fa = f_aifs[valid_mask]
lats_v = flat_lats[valid_mask]
lons_v = flat_lons[valid_mask]

# Feature Matrix: Spatial coordinates + model forecasts + model spread
diff = np.abs(fg - fa)
X = np.column_stack([lats_v, lons_v, fg, fa, diff])

# Train / Test Split on X and y
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.30, random_state=42
)

fg_train = X_train[:, 2]
fa_train = X_train[:, 3]

fg_test = X_test[:, 2]
fa_test = X_test[:, 3]

# 3. Target Weight Formulation
err_gfs = np.abs(fg_train - y_train)
err_aifs = np.abs(fa_train - y_train)
target_w_aifs = (err_gfs / (err_gfs + err_aifs + 1e-6)).clip(0.0, 1.0)

# Train Regressor to predict adaptive AIFS weight
model = GradientBoostingRegressor(
    n_estimators=60, max_depth=4, random_state=42
)
model.fit(X_train, target_w_aifs)

# 4. Predict Adaptive Weights on Unseen Test Set
w_aifs_pred = np.clip(model.predict(X_test), 0.0, 1.0)
w_gfs_pred = 1.0 - w_aifs_pred

# Compute Blends
blend_adaptive = (w_gfs_pred * fg_test) + (w_aifs_pred * fa_test)
blend_equal = 0.5 * fg_test + 0.5 * fa_test


def evaluate(pred, truth):
    mae = np.mean(np.abs(pred - truth))
    rmse = np.sqrt(np.mean((pred - truth) ** 2))
    return mae, rmse


gfs_mae, gfs_rmse = evaluate(fg_test, y_test)
aifs_mae, aifs_rmse = evaluate(fa_test, y_test)
eq_mae, eq_rmse = evaluate(blend_equal, y_test)
ad_mae, ad_rmse = evaluate(blend_adaptive, y_test)

print("--- HOLDOUT TEST EVALUATION (30% Unseen Grid Points) ---")
print(f"GFS Alone       -> MAE: {gfs_mae:.3f} mm | RMSE: {gfs_rmse:.3f} mm")
print(f"AIFS Alone      -> MAE: {aifs_mae:.3f} mm | RMSE: {aifs_rmse:.3f} mm")
print(f"Equal Average   -> MAE: {eq_mae:.3f} mm | RMSE: {eq_rmse:.3f} mm")
print(f"Adaptive Blend  -> MAE: {ad_mae:.3f} mm | RMSE: {ad_rmse:.3f} mm")
print(
    f"\nMean Learned Weights on Test: GFS={np.mean(w_gfs_pred):.2f} | AIFS={np.mean(w_aifs_pred):.2f}"
)

# --- EXTREME WEATHER METRICS (IMD Heavy Rainfall >= 64.5 mm) ---
THRESHOLD = 64.5  # IMD standard definition for Heavy Rain


def calc_event_metrics(pred, truth, thresh=THRESHOLD):
    pred_event = pred >= thresh
    true_event = truth >= thresh

    hits = np.sum(pred_event & true_event)
    misses = np.sum((~pred_event) & true_event)
    false_alarms = np.sum(pred_event & (~true_event))

    pod = hits / (hits + misses) if (hits + misses) > 0 else 0.0
    far = (
        false_alarms / (hits + false_alarms)
        if (hits + false_alarms) > 0
        else 0.0
    )
    csi = (
        hits / (hits + misses + false_alarms)
        if (hits + misses + false_alarms) > 0
        else 0.0
    )

    return pod, far, csi, int(np.sum(true_event)), int(np.sum(pred_event))


print("\n--- EXTREME WEATHER DETECTION (Heavy Rain >= 64.5 mm) ---")
for name, preds in [
    ("GFS Alone", fg_test),
    ("AIFS Alone", fa_test),
    ("Equal Average", blend_equal),
    ("Adaptive Blend", blend_adaptive),
]:
    pod, far, csi, actual_cnt, pred_cnt = calc_event_metrics(preds, y_test)
    print(
        f"{name:<15} -> POD (Recall): {pod:.3f} | FAR: {far:.3f} | CSI: {csi:.3f} | Flags Triggered: {pred_cnt}/{actual_cnt}"
    )