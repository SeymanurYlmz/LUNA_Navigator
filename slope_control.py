import json
import numpy as np
import rasterio
from rasterio.windows import from_bounds, Window
from pyproj import CRS, Transformer

DEM_YOLU = "data/LDEM_80S_80MPP_ADJ.tiff"
SLOPE_YOLU = "data/LDSM_80S_80MPP_ADJ.tiff"
YARI_CAP = 7500

with open("candidates.json", encoding="utf-8") as f:
    adaylar = json.load(f)

ay_cografi = CRS.from_proj4("+proj=longlat +a=1737400 +b=1737400 +no_defs")

with rasterio.open(DEM_YOLU) as dem, rasterio.open(SLOPE_YOLU) as egim:
    donusturucu = Transformer.from_crs(ay_cografi, dem.crs, always_xy=True)
    print(f"{'id':10s} {'LDSM ort':>9s} {'kendi ort':>10s} {'fark':>6s} {'merkez yük. (m)':>16s} {'merkez eğim':>12s}")
    for a in adaylar:
        x, y = donusturucu.transform(a["lon"], a["lat"])
        w = from_bounds(x - YARI_CAP, y - YARI_CAP, x + YARI_CAP, y + YARI_CAP, dem.transform)
        w = w.round_offsets().round_lengths().intersection(Window(0, 0, dem.width, dem.height))
        z = dem.read(1, window=w, masked=True).astype("float64").filled(np.nan)
        s = egim.read(1, window=w, masked=True).astype("float64").filled(np.nan)
        dy, dx = np.gradient(z, dem.res[1], dem.res[0])
        kendi = np.degrees(np.arctan(np.hypot(dx, dy)))
        ldsm_ort = float(np.nanmean(s))
        kendi_ort = float(np.nanmean(kendi))
        merkez_z = float(next(dem.sample([(x, y)]))[0])
        merkez_s = float(next(egim.sample([(x, y)]))[0])
        print(f"{a['id']:10s} {ldsm_ort:9.1f} {kendi_ort:10.1f} {abs(ldsm_ort - kendi_ort):6.1f} {merkez_z:16.0f} {merkez_s:12.1f}")