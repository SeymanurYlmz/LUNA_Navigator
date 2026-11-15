import os
import json
import spiceypy as spice
import numpy as np

kernel_path = "backend/kernels"
if os.path.exists(kernel_path):
    spice.furnsh(os.path.join(kernel_path, "latest_leapseconds.tls"))
    spice.furnsh(os.path.join(kernel_path, "earth_latest_high_prec.bpc"))
    spice.furnsh(os.path.join(kernel_path, "de440.bsp"))
    spice.furnsh(os.path.join(kernel_path, "pck00010.tpc"))
    print("SPICE Kernels successfully loaded.\n" + "="*50)
else:
    print(f"ERROR: '{kernel_path}' directory not found. Please check kernel paths.")
    exit()

json_path = "cikti/sites.json"
with open(json_path, "r", encoding="utf-8") as f:
    sites = json.load(f)

start_utc = "2027-01-01 00:00:00 UTC"
end_utc = "2027-01-02 00:00:00 UTC"

et_start = spice.utc2et(start_utc)
et_end = spice.utc2et(end_utc)

print(f"Simulation Range: {start_utc} -> {end_utc}\n" + "="*50)

for site in sites:
    site_id = site["id"]
    name = site["name"]
    lat = site["lat"]
    lon = site["lon"]
    horizon = site["horizon"]
    slope = site["slope"]
    
    print(f"Analyzing -> Site: {name} [{site_id}]")
    print(f"  Lat/Lon : {lat}°, {lon}° | Horizon Angle: {horizon}° | Slope: {slope}°")
    
    radius = 1737.4  
    lat_rad = np.radians(lat)
    lon_rad = np.radians(lon)
    
    pos_srf = spice.latrec(radius, lon_rad, lat_rad)
    
    target_et = et_start
    
    sun_pos, _ = spice.spkpos("SUN", target_et, "IAU_MOON", "LT+S", "MOON")
    
    relative_sun = [s - p for s, p in zip(sun_pos, pos_srf)]
    dist_sun = np.linalg.norm(relative_sun)
    
    print(f"  -> Sun Vector Distance at {start_utc}: {dist_sun:.2f} km")
    print("-" * 50)

spice.kclear()
print("\nAll SPICE analysis loops completed successfully.")