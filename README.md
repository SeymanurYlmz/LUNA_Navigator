# LUNA Navigator — Lunar South Pole Landing Site Selection & Hazard Analysis

[![Live Demo](https://img.shields.io/badge/Live%20Demo-GitHub%20Pages-007ec6?style=for-the-badge&logo=github)](https://seymanurylmz.github.io/LUNA_Navigator/)
[![NASA Space Apps](https://img.shields.io/badge/NASA%20Space%20Apps-Sivas%202026-0B3D91?style=for-the-badge&logo=nasa)](https://www.spaceappschallenge.org/)
[![Data Source](https://img.shields.io/badge/NASA%20LRO-LOLA%20%26%20NAIF%20SPICE-success?style=for-the-badge)](https://pds-geosciences.wustl.edu/missions/lro/lola.htm)

**Live Interactive Web Application:** [https://seymanurylmz.github.io/LUNA_Navigator/](https://seymanurylmz.github.io/LUNA_Navigator/)  
**Source Code Repository:** [https://github.com/SeymanurYlmz/LUNA_Navigator](https://github.com/SeymanurYlmz/LUNA_Navigator)

---

## 1. Executive Summary & Mission Context

Selecting a safe and scientifically valuable landing site at the **Lunar South Pole**—specifically around **Shackleton Crater** and **Malapert Massif**—is one of the primary engineering challenges for Artemis-era lunar exploration. Unlike equatorial regions, the lunar south pole experiences extreme grazing solar incidence angles ($\approx 1.5^\circ$ axial tilt), resulting in adjacent regions of near-continuous sunlight ("Peaks of Eternal Light") and **Permanently Shadowed Regions (PSRs)** that harbor water-ice volatiles.

**LUNA Navigator** is an end-to-end geospatial validation, astrodynamics modeling, and interactive decision-support pipeline. It processes high-resolution Lunar Reconnaissance Orbiter (**LRO**) **LOLA** elevation rasters alongside **NASA NAIF SPICE** planetary ephemerides to quantitatively evaluate, filter, and visualize candidate landing zones across four coupled mission constraints:

1. **Topographic Slope & Lander Stability:** Filtering out steep crater walls and rough terrain exceeding lander tip-over thresholds.
2. **Azimuthal Horizon Masking & Solar Illumination:** Ray-casting across surrounding topography ($360^\circ$) to calculate true solar visibility fractions and power generation potential.
3. **Direct-to-Earth (DTE) Line-of-Sight Communication:** Modeling geocentric Earth elevation angles against local horizon obstructions to guarantee continuous telemetry windows.
4. **Scientific Proximity to PSRs:** Identifying safe, sunlit "oases" within rover traverse range of cold-trapped water-ice reservoirs.

---

## 2. System Architecture & Pipeline Workflow

The system decouples heavy offline planetary raster/ephemeris computation (Python scientific stack) from lightweight, zero-latency client-side visualization (HTML5/JS/JSON).

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                        RAW NASA PLANETARY DATA                          │
│  • LRO LOLA South Pole DEM & Slope Rasters (GeoTIFF / JP2)              │
│  • NAIF SPICE Planetary Ephemerides & Frames (de440.bsp, .bpc, .tls)    │
└───────────────────┬─────────────────────────────────┬───────────────────┘
                    │                                 │
                    ▼                                 ▼
┌───────────────────────────────────┐ ┌───────────────────────────────────┐
│   GEOSPATIAL TERRAIN ENGINE       │ │   ASTRODYNAMIC EPHEMERIS ENGINE   │
│  • terrain_analysis.py            │ │  • spice_analysis.py              │
│  • slope_control.py               │ │  • calculate_horizon.py           │
│  (Elevation, Hillshade, Slope,    │ │  (Sun/Earth Azimuth & Elevation,  │
│   360° Ray-Cast Horizon Profiles) │ │   Illumination & DTE Windows)     │
└───────────────────┬───────────────┘ └─────────────────┬─────────────────┘
                    │                                 │
                    └────────────────┬────────────────┘
                                     ▼
                    ┌─────────────────────────────────┐
                    │   MULTI-CRITERIA VALIDATOR      │
                    │  • control.py & kodi_api.py     │
                    │  (Threshold Filtering, Scoring  │
                    │   & Hazard Cross-Verification)  │
                    └────────────────┬────────────────┘
                                     │
                    ┌────────────────┴────────────────┐
                    ▼                                 ▼
┌───────────────────────────────────┐ ┌───────────────────────────────────┐
│     VALIDATION ARTIFACTS          │ │     INTERACTIVE WEB INTERFACE     │
│  • candidates.json                │ │  • index.html (GitHub Pages)      │
│  • output_control.png & output/   │ │  (Interactive Map, Site Metrics,  │
└───────────────────────────────────┘ └───────────────────────────────────┘
```

---

## 3. Scientific & Mathematical Methodology

### 3.1 Coordinate Reference System (CRS) & Projection
All South Polar raster datasets are processed in the **Moon South Pole Stereographic Projection** (`IAU_MOON` / `MOON_ME` body-fixed frame):
* **Standard Parallel / Latitude of Origin:** $-90^\circ$ (South Pole)
* **Central Meridian:** $0^\circ$
* **Planetary Radius:** $R_{\text{Moon}} = 1,737,400\text{ m}$

### 3.2 Terrain Slope & Surface Roughness (`terrain_analysis.py`, `slope_control.py`)
Using finite-difference elevation gradients ($\frac{\partial z}{\partial x}, \frac{\partial z}{\partial y}$) over local pixel neighborhoods in the LOLA Digital Elevation Model (DEM), the local surface slope angle $\theta_{\text{slope}}$ is derived and cross-checked against official LOLA Slope Data Records (`LDSM`):

$$\theta_{\text{slope}} = \arctan\left(\sqrt{\left(\frac{\partial z}{\partial x}\right)^2 + \left(\frac{\partial z}{\partial y}\right)^2}\right)$$

* **Landing Safety Threshold:** Candidate pixels must satisfy $\theta_{\text{slope}} \le 10^\circ$ (with optimal zones prioritized at $\le 5^\circ$) across a contiguous landing pad footprint to prevent lander tipping during descent.

### 3.3 $360^\circ$ Topographic Horizon Profile (`calculate_horizon.py`)
Because the Sun and Earth remain near the horizon at high lunar latitudes, distant crater rims cast shadows tens of kilometers away. For each candidate coordinate $(x_0, y_0, z_0)$, the algorithm casts radial rays across azimuth angles $\alpha \in [0^\circ, 360^\circ)$ up to a maximum search radius $R_{\max}$ and computes the minimum unobstructed elevation angle $h(\alpha)$:

$$h(\alpha) = \max_{r \in (0, R_{\max}]} \arctan\left(\frac{z(r, \alpha) - z_0}{r} - \frac{r}{2 R_{\text{Moon}}}\right)$$

*(Note: The second term $\frac{r}{2 R_{\text{Moon}}}$ accounts for lunar planetary curvature over long radial baselines).*

### 3.4 Solar Illumination & Earth Visibility (`spice_analysis.py`)
Using **NASA NAIF SPICE** kernels (`de440.bsp`, `earth_latest_high_prec.bpc`, `latest_leapseconds.tls`), the pipeline computes topocentric azimuth and elevation time-series for both the Sun ($\alpha_{\odot}(t), \varepsilon_{\odot}(t)$) and Earth ($\alpha_{\oplus}(t), \varepsilon_{\oplus}(t)$) over a full lunar nodal/seasonal cycle:
* **Illumination Condition:** $\varepsilon_{\odot}(t) + R_{\odot,\text{angular}} > h(\alpha_{\odot}(t))$
* **Direct-to-Earth (DTE) Telemetry Condition:** $\varepsilon_{\oplus}(t) > h(\alpha_{\oplus}(t))$

---

## 4. Repository Structure & Module Breakdown

```text
LUNA_Navigator/
├── index.html                    # Production interactive web dashboard (deployed on GitHub Pages)
├── candidates.json               # Structured output of validated landing sites & safety scores
├── output_control.png            # High-resolution terrain, slope, and candidate overlay map
├── terrain_analysis.py           # Reads LOLA GeoTIFFs via rasterio, generates hillshades & DEM slices
├── slope_control.py              # Computes & cross-validates terrain slope angles against LOLA LDSM
├── calculate_horizon.py          # Performs 360° azimuthal ray-casting with lunar curvature correction
├── spice_analysis.py             # Queries NAIF SPICE ephemerides for Sun/Earth visibility windows
├── control.py                    # Master validation orchestrator; filters hazards & exports JSON
├── kodi_api.py                   # Backend service endpoints for real-time coordinate hazard queries
├── backend/                      # NAIF SPICE kernel directory
│   ├── earth_latest_high_prec.bpc# High-precision Earth orientation binary PCK kernel
│   └── latest_leapseconds.tls    # NAIF leapseconds kernel (LSK)
├── output/                       # Generated analytical plots, horizon profiles, and validation logs
├── requirements.txt              # Python environment dependencies
├── .gitignore                    # Excludes virtual environments, secrets, and >100 MB raw rasters
└── README.md                     # Technical documentation & dataset reproduction guide
```

---

## 5. External NASA Datasets Setup (Step-by-Step)

To keep the repository lightweight and compliant with GitHub's 100 MB file-size limit, raw multi-gigabyte LOLA planetary rasters and the `de440.bsp` ephemeris file are excluded from version control. Follow the steps below to download the exact NASA source files required to re-run the analysis pipeline locally.

### Step 1: Download NASA LRO LOLA South Pole Datasets (PDS)
The terrain and slope scripts require the Lunar Orbiter Laser Altimeter (LOLA) Gridded Data Records (GDR) in South Pole Stereographic projection:

1. Navigate to the **NASA PDS Geosciences Node — LRO LOLA Data Archive**:  
   * **Direct Polar GeoTIFF/JP2 Repository:** [https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/](https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/)  
   * **PDS Geosciences Portal:** [https://pds-geosciences.wustl.edu/missions/lro/lola.htm](https://pds-geosciences.wustl.edu/missions/lro/lola.htm)
2. Download the **South Pole Digital Elevation Model (`LDEM`)** and corresponding **Slope Map (`LDSM`)** at 20 m/pixel or 10 m/pixel resolution:
   * `LDEM_80S_20M.TIF` (or `LDEM_85S_10M.TIF` for ultra-high-resolution Shackleton/Malapert analysis)
   * `LDSM_80S_20M.TIF` (or `LDSM_85S_10M.TIF`)
3. Create a `data/` folder in the repository root and move the downloaded rasters into it:
   ```text
   LUNA_Navigator/
   └── data/
       ├── LDEM_80S_20M.TIF
       └── LDSM_80S_20M.TIF
   ```

### Step 2: Download NASA NAIF SPICE Planetary Ephemeris (`de440.bsp`)
The repository already includes the leapseconds kernel (`latest_leapseconds.tls`) and Earth orientation kernel (`earth_latest_high_prec.bpc`) inside `backend/`. You only need to download the JPL Development Ephemeris (`de440.bsp`, ~114 MB):

1. Download `de440.bsp` directly from the **NASA NAIF Generic Kernels Server**:  
   * **Direct Download Link:** [https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440.bsp](https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/de440.bsp)
2. Place the file inside the existing `backend/` directory:
   ```text
   LUNA_Navigator/
   └── backend/
       ├── de440.bsp                  <-- Place downloaded file here
       ├── earth_latest_high_prec.bpc
       └── latest_leapseconds.tls
   ```

---

## 6. Local Installation & Pipeline Execution

### Prerequisites
* **Python 3.10+**
* GDAL / PROJ system libraries (automatically bundled via `rasterio` and `pyproj` wheels on most platforms)

### Installation Steps
1. **Clone the repository:**
   ```bash
   git clone [https://github.com/SeymanurYlmz/LUNA_Navigator.git](https://github.com/SeymanurYlmz/LUNA_Navigator.git)
   cd LUNA_Navigator
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux / macOS:
   source venv/bin/activate
   ```

3. **Install required Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

### Running the Validation Pipeline
Execute the modules in sequence to process the LOLA rasters, run SPICE visibility simulations, and regenerate `candidates.json`:

```bash
# 1. Extract elevation subsets and generate hillshade base layers
python terrain_analysis.py

# 2. Verify terrain slope gradients against LOLA LDSM thresholds
python slope_control.py

# 3. Compute 360° azimuthal horizon profiles with lunar curvature correction
python calculate_horizon.py

# 4. Run NAIF SPICE solar illumination and Direct-to-Earth visibility models
python spice_analysis.py

# 5. Aggregate constraints, filter hazards, and export validated candidate sites
python control.py
```

To launch the local web interface and verify the updated `candidates.json`:
```bash
python -m http.server 8000
# Open http://localhost:8000 in your browser
```

---

## 7. Technology Stack & Libraries

| Layer | Technologies & Libraries | Purpose |
| :--- | :--- | :--- |
| **Geospatial & Raster Processing** | `Python`, `rasterio`, `pyproj`, `GDAL` | Reading LOLA GeoTIFF DEMs, reprojecting South Pole stereographic coordinates |
| **Numerical & Scientific Computing** | `NumPy`, `SciPy` | Finite-difference slope gradients, vectorized ray-casting horizon profiles |
| **Astrodynamics & Ephemeris** | `SpiceyPy` (NASA NAIF SPICE) | High-precision Sun/Earth topocentric azimuth, elevation, and eclipse modeling |
| **Backend & Validation API** | `Python`, `FastAPI` / `kodi_api.py` | Coordinate-level hazard evaluation and candidate scoring |
| **Frontend Visualization** | `HTML5`, `CSS3`, `JavaScript`, `GitHub Pages` | Interactive lunar south pole map, hazard overlays, and landing site telemetry |

---

## 8. Data Attribution & References

* **NASA LRO LOLA Team:** Smith, D. E., et al. (2010), *The Lunar Orbiter Laser Altimeter Investigation on the Lunar Reconnaissance Orbiter Mission*, Space Science Reviews, 150, 209–241. Data archived at NASA PDS Geosciences Node.
* **NASA NAIF SPICE:** Acton, C. H. (1996), *Ancillary Data Services of NASA's Navigation and Ancillary Information Facility*, Planetary and Space Science, 44(1), 65–70.
