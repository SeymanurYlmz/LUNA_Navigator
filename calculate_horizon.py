import os
os.environ["PROJ_LIB"] = ""

import json
import numpy as np
import rasterio
from pyproj import CRS, Transformer

def calculate_max_horizon(dem_path, center_lat, center_lon, num_azimuths=36, max_distance_m=50000):
    with rasterio.open(dem_path) as src:
        dem = src.read(1)
        transform = src.transform
        res_x = transform[0]
        
        src_crs = CRS.from_dict({'proj': 'longlat', 'R': 1737400, 'no_defs': True})
        dst_crs = src.crs
        
        transformer = Transformer.from_crs(src_crs, dst_crs, always_xy=True)
        x_m, y_m = transformer.transform(center_lon, center_lat)
        
        try:
            row, col = src.index(x_m, y_m)
        except Exception as e:
            print(f"Coordinate outside pixel boundaries: {e}")
            return 0.0
        
        if row < 0 or row >= dem.shape[0] or col < 0 or col >= dem.shape[1]:
            print(f"Warning: Coordinate not within DEM matrix bounds! (row:{row}, col:{col})")
            return 0.0
            
        z0 = dem[row, col]
        if np.isnan(z0) or z0 <= -30000:
            z0 = 0.0
            
        max_horizon_deg = 0.0
        
        azimuths = np.linspace(0, 360, num_azimuths, endpoint=False)
        
        for az in azimuths:
            rad = np.radians(az)
            dx = np.sin(rad)
            dy = -np.cos(rad)
            
            current_dist = res_x
            while current_dist < max_distance_m:
                step_counts = int(current_dist / res_x)
                r = int(row + step_counts * dy)
                c = int(col + step_counts * dx)
                
                if r < 0 or r >= dem.shape[0] or c < 0 or c >= dem.shape[1]:
                    break
                
                z = dem[r, c]
                if np.isnan(z) or z <= -30000:
                    current_dist += res_x * 5
                    continue
                
                delta_z = z - z0
                if delta_z > 0:
                    angle = np.degrees(np.arctan2(delta_z, current_dist))
                    if angle > max_horizon_deg:
                        max_horizon_deg = angle
                
                current_dist += res_x * 5
                
        return round(float(max_horizon_deg), 2)

json_path = "cikti/sites.json"
with open(json_path, "r", encoding="utf-8") as f:
    sites = json.load(f)

print("Calculating horizon angles from DEM data...\n" + "="*50)

for site in sites:
    site_id = site["id"]
    name = site["name"]
    lat = site["lat"]
    lon = site["lon"]
    
    dem_file = os.path.join("cikti", f"{site_id}_dem.tif")
    
    if os.path.exists(dem_file):
        calculated_horizon = calculate_max_horizon(dem_file, lat, lon)
        print(f"Site: {name} [{site_id}]")
        print(f"  -> Old Horizon Value : {site['horizon']}°")
        print(f"  -> Calculated from DEM : {calculated_horizon}°")
        
        site["horizon"] = calculated_horizon
    else:
        print(f"WARNING: {dem_file} not found, original value preserved.")
        
    print("-" * 50)

with open(json_path, "w", encoding="utf-8") as f:
    json.dump(sites, f, ensure_ascii=False, indent=2)

print("\nCalculation completed! Updated horizon values saved to 'cikti/sites.json'.")