# 🌕 LUNA: Lunar South Pole Landing Site Selection & Environmental Validation System

[![NASA Space Apps Challenge](https://img.shields.io/badge/NASA-Space%20Apps%20Challenge-blue.svg)](https://www.spaceappschallenge.org/)
[![Python](https://img.shields.io/badge/Python-3.9%2B-yellow.svg)](https://www.python.org/)
[![Data Source](https://img.shields.io/badge/NASA%20PDS-LOLA%20%26%20SPICE-red.svg)](https://pds.nasa.gov/)

**LUNA** is an end-to-end geospatial analysis, environmental validation, and interactive visualization platform designed to identify and verify safe landing sites in the **Lunar South Pole** (focusing on Shackleton Crater, Malapert Massif, and Artemis III candidate regions).

By processing real high-resolution elevation data from NASA's **Lunar Orbiter Laser Altimeter (LOLA)** alongside **NAIF SPICE** planetary ephemeris kernels, LUNA evaluates terrain slope safety, horizon elevation profiles, solar illumination availability, and direct-to-Earth (DTE) line-of-sight communication windows.

🔗 **Live Interactive Web Demo:** `[Insert Your GitHub Pages URL Here, e.g., https://username.github.io/luna-project/]`

---

## 🎯 Key Features & Scientific Pipeline

1. **Topographic & Slope Safety Validation (`terrain_analysis.py`, `slope_control.py`):**
   - Processes LOLA Digital Elevation Models (DEM) to compute local surface gradients in degrees.
   - Filters out hazardous terrain exceeding lander stability thresholds (e.g., slopes $> 10^\circ - 15^\circ$) and verifies landing footprint safety.
2. **Horizon & Solar Illumination Analysis (`calculate_horizon.py`):**
   - Performs $360^\circ$ ray-casting across surrounding lunar topography to compute local horizon elevation angles.
   - Identifies Peaks of Eternal Light (PEL) and Permanently Shadowed Regions (PSRs) critical for solar power generation and water-ice proximity.
3. **Ephemeris & Line-of-Sight Modeling (`spice_analysis.py`):**
   - Utilizes NASA NAIF SPICE kernels to track precise Sun and Earth elevation/azimuth angles over mission timelines.
   - Validates continuous solar illumination and Direct-to-Earth (DTE) communication windows.
4. **Interactive Decision-Support Dashboard (`index.html`, `kodi_api.py`):**
   - Visualizes validated landing candidates (`candidates.json`), hillshade topography maps, slope overlays, and real-time environmental telemetry via an intuitive web interface and AI assistant integration.

---

## 📂 Repository Structure

```text
LUNA_FINAL/
├── index.html                  # Main interactive web interface (deployed via GitHub Pages)
├── candidates.json             # Validated landing site coordinates & environmental metrics
├── terrain_analysis.py         # LOLA DEM ingestion and topographic metric extraction
├── slope_control.py            # Surface gradient calculation and landing hazard filtering
├── calculate_horizon.py        # 360-degree horizon elevation profile ray-tracer
├── spice_analysis.py           # NAIF SPICE ephemeris & Sun/Earth visibility calculations
├── control.py                  # Pipeline orchestration and validation checks
├── kodi_api.py                 # Backend API & interactive query handler
├── backend/                    # Server-side endpoints and helper modules
├── output/                     # Generated analysis plots and validation reports
├── output_control.png          # Visual verification of slope and horizon outputs
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation & data setup guide
```

---

## 🛰️ External Dataset Setup (LOLA & SPICE)

Due to GitHub file size limitations, raw high-resolution **NASA LOLA** raster files and **NAIF SPICE** kernels are excluded from this repository. Follow the step-by-step instructions below to download and configure them locally before running the validation scripts.

### Step 1: Create the Local Data Directory
In the root directory of the project, create a `data/` folder with the following subdirectories:
```bash
mkdir -p data/lola
mkdir -p data/spice
```

### Step 2: Download NASA LOLA South Pole DEM Data
1. Navigate to the **NASA PDS Geosciences Node (LOLA Data Archive)** or the **USGS Astrogeology Science Center**:
   - LOLA South Pole Polar Stereographic Products: `https://imbrium.mit.edu/DATA/LOLA_GDR/POLAR/JP2/` or `https://pds-geosciences.wustl.edu/lro/lro-l-lola-3-rdr-v1/lrolol_1xxx/data/lola_gdr/polar/img/`
2. Download the South Pole Digital Elevation Model (LDEM) covering $75^\circ\text{S}$ to $90^\circ\text{S}$ (e.g., `LDEM_80S_20M.IMG` / `.LBL` or `LDEM_75S_30M.TIF`).
   - *Tip:* For faster local testing, you may use the $60\text{ m/pixel}$ or $120\text{ m/pixel}$ resolution products (`LDEM_80S_60M` / `LDEM_80S_120M`).
3. Place the downloaded `.TIF` or `.IMG` + `.LBL` files into the `data/lola/` directory.

### Step 3: Download NASA NAIF SPICE Kernels
1. Visit the **NASA Navigation and Ancillary Information Facility (NAIF)** generic kernels archive:
   - Base URL: `https://naif.jpl.nasa.gov/pub/naif/generic_kernels/`
2. Download the following four essential kernel files:
   - **Leapseconds Kernel (LSK):** `lsk/naif0012.tls`
   - **Planetary Constants Kernel (PCK):** `pck/pck00011.tpc`
   - **Planetary Ephemeris (SPK):** `spk/planets/de440.bsp` (or `de430.bsp`)
   - **Lunar Orientation Frame (FK / Binary PCK):** `pck/moon_pa_de440_200625.bpc` and `fk/satellites/moon_080317.tf`
3. Place all downloaded SPICE files into the `data/spice/` directory.

---

## ⚙️ Installation & Running the Validation Pipeline

### 1. Clone the Repository
```bash
git clone https://github.com/<your-username>/<your-repo-name>.git
cd <your-repo-name>
```

### 2. Set Up Virtual Environment & Install Dependencies
```bash
python -m venv venv

# On Windows:
venv\Scripts\activate

# On macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt
```
*(Core libraries include: `rasterio`, `pyproj`, `numpy`, `scipy`, `spiceypy`, `matplotlib`)*

### 3. Configure Environment Variables (Optional for API)
If running `kodi_api.py` locally, create a `.env` file in the root directory and add your API credentials:
```env
API_KEY=your_api_key_here
```

### 4. Execute Validation Scripts
Run the analysis scripts in order to reproduce `candidates.json` and `output_control.png`:
```bash
python terrain_analysis.py
python slope_control.py
python calculate_horizon.py
python spice_analysis.py
python control.py
```

### 5. Launch the Web Interface
To view the web dashboard locally without CORS restrictions, start a simple HTTP server in the root folder:
```bash
python -m http.server 8000
```
Then open `http://localhost:8000` in your browser.

---

## 👥 Team & Acknowledgments
- **Data Credits:** NASA Lunar Reconnaissance Orbiter (LRO) LOLA Science Team, NASA PDS Geosciences Node, and NASA NAIF.
- Developed for the **NASA International Space Apps Challenge**.