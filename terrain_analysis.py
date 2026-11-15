import os
import glob
import json
import numpy as np
import rasterio
from rasterio.windows import from_bounds, Window
from pyproj import CRS, Transformer
from scipy import ndimage
from PIL import Image

DEM_PATH = "data/LDEM_80S_80MPP_ADJ.tiff"
SLOPE_PATH = "data/LDSM_80S_80MPP_ADJ.tiff"
HILLSHADE_PATH = "data/LDEM_80S_80MPP_ADJ_HILL.tiff"
OUTPUT_DIR = "output"

RADIUS_M = 7500
FLAT_THRESHOLD_DEG = 5.0

with open("candidates.json", encoding="utf-8") as f:
    candidates = json.load(f)

os.makedirs(OUTPUT_DIR, exist_ok=True)
for old_file in ("sites.json", "sites_detailed_report.json", "hillshade_bounds.json", "south_pole_hillshade.png"):
    path = os.path.join(OUTPUT_DIR, old_file)
    if os.path.exists(path):
        os.remove(path)
for old_dem in glob.glob(os.path.join(OUTPUT_DIR, "*_dem.tif")):
    os.remove(old_dem)

moon_geo_crs = CRS.from_proj4("+proj=longlat +a=1737400 +b=1737400 +no_defs")

with rasterio.open(DEM_PATH) as d, rasterio.open(SLOPE_PATH) as s, rasterio.open(HILLSHADE_PATH) as h:
    if d.crs is None:
        raise ValueError("DEM file does not contain CRS metadata")
    if d.crs != s.crs or d.crs != h.crs:
        raise ValueError("DEM, slope, and hillshade CRS values do not match")
    if d.transform != s.transform or d.shape != s.shape:
        raise ValueError("DEM and slope files are not on the same grid")
    transformer = Transformer.from_crs(moon_geo_crs, d.crs, always_xy=True)
    print("CRS and grid verified:", d.crs.to_proj4())


def clean_masked(masked_arr):
    vals = masked_arr.compressed()
    return vals[np.isfinite(vals)]


sites_ui = []
sites_detailed = []

with rasterio.open(DEM_PATH) as dem_src, rasterio.open(SLOPE_PATH) as slope_src:
    for site in candidates:
        if not site.get("verified"):
            print(f"WARNING: Coordinates for {site['name']} are not verified yet")

        x_m, y_m = transformer.transform(site["lon"], site["lat"])
        window = from_bounds(x_m - RADIUS_M, y_m - RADIUS_M, x_m + RADIUS_M, y_m + RADIUS_M, dem_src.transform)
        window = window.round_offsets().round_lengths()
        window = window.intersection(Window(0, 0, dem_src.width, dem_src.height))
        if window.width <= 0 or window.height <= 0:
            raise ValueError(f"{site['name']} is outside map boundaries")

        expected_px = (2 * RADIUS_M / dem_src.res[0]) * (2 * RADIUS_M / dem_src.res[1])
        coverage_pct = round(min(100.0, window.width * window.height / expected_px * 100), 1)
        if coverage_pct < 99.0:
            print(f"WARNING: Window coverage for {site['name']} is approximately {coverage_pct}%")

        dem_m = dem_src.read(1, window=window, masked=True)
        slope_m = slope_src.read(1, window=window, masked=True)
        dem_v = clean_masked(dem_m)
        slope_v = clean_masked(slope_m)
        if dem_v.size == 0 or slope_v.size == 0:
            raise ValueError(f"No valid data for {site['name']}")

        profile = dem_src.profile.copy()
        profile.update(
            height=dem_m.shape[0],
            width=dem_m.shape[1],
            transform=rasterio.windows.transform(window, dem_src.transform)
        )
        nodata = dem_src.nodata if dem_src.nodata is not None else -32768
        with rasterio.open(os.path.join(OUTPUT_DIR, f"{site['id']}_dem.tif"), "w", **profile) as dst:
            dst.write(dem_m.filled(nodata), 1)

        flat_mask = slope_m.filled(999.0) < FLAT_THRESHOLD_DEG
        labeled_grid, num_features = ndimage.label(flat_mask)
        largest_flat_km2 = 0.0
        if num_features > 0:
            sizes = ndimage.sum(flat_mask, labeled_grid, range(1, num_features + 1))
            largest_flat_km2 = round(float(sizes.max()) * slope_src.res[0] * slope_src.res[1] / 1e6, 2)

        mean_slope = round(float(np.mean(slope_v)), 1)
        pct_under_5 = round(float(np.mean(slope_v < 5.0) * 100), 1)
        pct_under_10 = round(float(np.mean(slope_v < 10.0) * 100), 1)

        sites_ui.append({
            "id": site["id"],
            "name": site["name"],
            "lat": site["lat"],
            "lon": site["lon"],
            "horizon": site["horizon"],
            "tag": site["tag"],
            "ph": site["ph"],
            "slope": mean_slope
        })

        sites_detailed.append({
            "id": site["id"],
            "name": site["name"],
            "x_m": round(x_m, 2),
            "y_m": round(y_m, 2),
            "verified": bool(site.get("verified")),
            "approx_coverage_pct": coverage_pct,
            "valid_pixels": int(slope_v.size),
            "mean_slope": mean_slope,
            "pct_under_5": pct_under_5,
            "pct_under_10": pct_under_10,
            "largest_flat_area_km2": largest_flat_km2,
            "elevation_min": round(float(dem_v.min()), 1),
            "elevation_max": round(float(dem_v.max()), 1)
        })

        print(f"[{site['id']}] {site['name']} -> mean slope: {mean_slope}°, <5° area: {pct_under_5}%, largest flat patch: {largest_flat_km2} km²")

with open(os.path.join(OUTPUT_DIR, "sites.json"), "w", encoding="utf-8") as f:
    json.dump(sites_ui, f, ensure_ascii=False, indent=2)

with open(os.path.join(OUTPUT_DIR, "sites_detailed_report.json"), "w", encoding="utf-8") as f:
    json.dump(sites_detailed, f, ensure_ascii=False, indent=2)

with rasterio.open(HILLSHADE_PATH) as hill_src:
    hill_m = hill_src.read(1, out_shape=(1000, 1000), masked=True)
    hill_v = clean_masked(hill_m)
    if hill_v.size == 0:
        raise ValueError("Hillshade data is empty")
    h_min, h_max = float(hill_v.min()), float(hill_v.max())
    hill_norm = np.zeros(hill_m.shape, dtype=np.uint8)
    valid = (~np.ma.getmaskarray(hill_m)) & np.isfinite(hill_m.data)
    if h_max > h_min:
        hill_norm[valid] = ((hill_m.data[valid] - h_min) / (h_max - h_min) * 255).astype(np.uint8)
    bounds = {
        "min_x": hill_src.bounds.left,
        "max_x": hill_src.bounds.right,
        "min_y": hill_src.bounds.bottom,
        "max_y": hill_src.bounds.top
    }
    Image.fromarray(hill_norm).save(os.path.join(OUTPUT_DIR, "south_pole_hillshade.png"))

with open(os.path.join(OUTPUT_DIR, "hillshade_bounds.json"), "w", encoding="utf-8") as f:
    json.dump(bounds, f, indent=2)

print("Completed: sites.json, sites_detailed_report.json, hillshade, and *_dem.tif files generated")