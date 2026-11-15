import json
import numpy as np
import rasterio
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from rasterio.windows import from_bounds, Window, bounds as pencere_sinirlari
from pyproj import CRS, Transformer

DEM_YOLU = "data/LDEM_80S_80MPP_ADJ.tiff"
HILL_YOLU = "data/LDEM_80S_80MPP_ADJ_HILL.tiff"
YARI_CAP = 15000

with open("candidates.json", encoding="utf-8") as f:
    adaylar = json.load(f)

ay_cografi = CRS.from_proj4("+proj=longlat +a=1737400 +b=1737400 +no_defs")
fig, eksenler = plt.subplots(3, 3, figsize=(13, 13))

with rasterio.open(DEM_YOLU) as dem, rasterio.open(HILL_YOLU) as hill:
    if dem.shape != hill.shape or dem.transform != hill.transform:
        raise ValueError("DEM ve hillshade aynı ızgarada değil")
    donusturucu = Transformer.from_crs(ay_cografi, dem.crs, always_xy=True)
    for ax, a in zip(eksenler.ravel(), adaylar):
        x, y = donusturucu.transform(a["lon"], a["lat"])
        w = from_bounds(x - YARI_CAP, y - YARI_CAP, x + YARI_CAP, y + YARI_CAP, dem.transform)
        w = w.round_offsets().round_lengths().intersection(Window(0, 0, dem.width, dem.height))
        z = dem.read(1, window=w, masked=True)
        g = hill.read(1, window=w, masked=True)
        sol, alt, sag, ust = pencere_sinirlari(w, dem.transform)
        ax.imshow(g, cmap="gray", extent=(sol, sag, alt, ust))
        ax.plot(x, y, "r+", markersize=22, markeredgewidth=2)
        durum = "doğrulandı" if a.get("verified") else "DOĞRULANMADI"
        ax.set_title(f"{a['name']} ({durum})\n{a['lat']}, {a['lon']}\nyükselti {z.min():.0f} … {z.max():.0f} m", fontsize=9)
        ax.set_xticks([])
        ax.set_yticks([])
        print(f"{a['id']:10s} lat {a['lat']:8.3f} lon {a['lon']:8.3f}  yükselti {z.min():7.0f} … {z.max():7.0f} m  {durum}")

plt.tight_layout()
plt.savefig("output_control.png", dpi=110)
print("Kaydedildi: output_control.png")