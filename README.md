# LUNA Navigator — Lunar South Pole Landing Site Selection & Hazard Analysis

**Live Interactive Demo:** [https://seymanurylmz.github.io/LUNA_Navigator/](https://seymanurylmz.github.io/LUNA_Navigator/)  
**Repository:** [https://github.com/SeymanurYlmz/LUNA_Navigator](https://github.com/SeymanurYlmz/LUNA_Navigator)

---

## Overview

**LUNA Navigator** is a scientific decision-support and terrain validation system designed for lunar south pole landing site selection (focusing on **Shackleton Crater** and **Malapert Massif**). By combining high-resolution altimetry from NASA's **Lunar Orbiter Laser Altimeter (LOLA)** with orbital ephemeris calculations from **NASA NAIF SPICE**, the pipeline evaluates candidate landing zones across three critical mission constraints:

1. **Terrain Slope & Surface Roughness:** Identifies flat, hazard-free zones safe for lander touchdown.
2. **Horizon Elevation & Solar Illumination:** Computes local topographic horizons to estimate solar power availability and locate Permanently Shadowed Regions (PSRs).
3. **Earth Visibility & Communication Windows:** Models line-of-sight geometry for continuous direct-to-Earth telemetry.

---

## Repository Architecture

```text
LUNA_Navigator/
├── index.html                    # Interactive web interface (GitHub Pages)
├── candidates.json               # Validated candidate landing site coordinates & metrics
├── output_control.png            # Terrain & slope validation visual output
├── calculate_horizon.py          # Topographic horizon profile & illumination modeling
├── control.py                    # Core validation & site filtering pipeline
├── kodi_api.py                   # Backend API integration for terrain queries
├── slope_control.py              # LOLA DEM slope angle verification script
├── spice_analysis.py             # Solar/Earth ephemeris & geometry calculations (SPICE)
├── terrain_analysis.py           # Elevation, hillshade, and hazard map processing
├── backend/                      # SPICE leapseconds & Earth orientation kernels
├── output/                       # Processed analytical charts and validation outputs
├── requirements.txt              # Python package dependencies
└── README.md                     # Project documentation & dataset setup guide
