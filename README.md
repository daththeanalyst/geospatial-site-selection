# Camden Synergy Index — Predictive Site Selection for Specialty Coffee

Binary classification on H3 spatial hexagons to identify underserved locations for specialty coffee retail in the London Borough of Camden, using multi-modal geospatial features and supervised machine learning.

**Programme**: MSc Business Analytics (MSIN0097 Predictive Analytics)
**Study Area**: London Borough of Camden (~22 km², ~600 H3 Res-9 hexagons)
**Theoretical Framework**: Burt's Structural Hole Theory (1992) — False Positives as market gaps

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/GeoSpatial-Project.git
cd GeoSpatial-Project

# 2. Create environment and install dependencies
pip install -r requirements.txt

# 3. Run the notebook pipeline in order
#    (Jupyter, VS Code, or any .ipynb-compatible environment)
01_ingest_and_clean.ipynb       # ETL: fetch POIs, load raster metadata, merge census
02_spatial_indexing_and_enrichment.ipynb  # H3 grid, zonal stats, census spatial join
03_analytics_and_vision.ipynb   # Graph centrality, heuristic scoring, 3D Pydeck map
camden_predictive_model.ipynb   # ML pipeline: LR → RF → XGBoost, spatial CV, recommendations

# 4. Launch the interactive dashboard
streamlit run streamlit_app.py
```

---

## Data Access

The pipeline requires three external datasets. OSM data is fetched programmatically; the other two must be downloaded manually.

| Dataset | Source | Access | Expected Location |
|---------|--------|--------|-------------------|
| **LandScan Global Population** | Oak Ridge National Laboratory (ORNL) | [landscan.ornl.gov](https://landscan.ornl.gov/) — free registration required | `landscan-mosaic-unitedkingdom-v1.tif` (project root) |
| **ONS Census 2021** (3 tables) | EDINA Digimap / ONS Nomis | [digimap.edina.ac.uk](https://digimap.edina.ac.uk/) or [nomis.co.uk](https://www.nomisweb.co.uk/) | `ons-age-ew-2021_*/`, `ons-economic-ew-2021_*/`, `ons-qualifications-ew-2021_*/` |
| **OpenStreetMap POIs** | OSMnx (programmatic) | Auto-fetched in Notebook 01 via `ox.features_from_place()` | No manual download needed |

**Census tables required** (Output Area level, England & Wales):
- TS007 — Age by single year (we extract `age_16_to_34_perc`, `age_65_plus_perc`)
- TS066 — Economic activity status (we extract `employed_total_perc`, `retired_perc`, `unemployed_perc`)
- TS067 — Highest qualification (we extract `level4_perc`, `no_qualifications_perc`)

---

## Project Structure

```
GeoSpatial Project/
├── 01_ingest_and_clean.ipynb           # Step 1: Multi-modal ETL pipeline
├── 02_spatial_indexing_and_enrichment.ipynb  # Step 2: H3 grid + spatial enrichment
├── 03_analytics_and_vision.ipynb       # Step 3: Graph analytics + heuristic scoring
├── camden_predictive_model.ipynb       # Step 4: ML pipeline (LR/RF/XGB + spatial CV)
├── streamlit_app.py                    # Interactive 4-tab dashboard
├── requirements.txt                    # Python dependencies
├── agent_collaboration_log.md          # AI-Human collaboration audit (Appendix)
├── report_structure.md                 # Academic report outline
├── claude.md                           # Agent runbook (spatial verification rules)
├── docs/
│   └── index.html                      # GitHub Pages portfolio site
├── data/
│   ├── processed/                      # Intermediate outputs (auto-generated)
│   └── outputs/                        # Final outputs (auto-generated)
├── landscan-mosaic-unitedkingdom-v1.tif  # LandScan raster (manual download)
├── ons-age-ew-2021_*/                  # Census age data (manual download)
├── ons-economic-ew-2021_*/             # Census economic data (manual download)
└── ons-qualifications-ew-2021_*/       # Census qualifications data (manual download)
```

---

## Pipeline Architecture

```
  OSM POIs          LandScan Raster       ONS Census 2021
     │                    │                      │
     ▼                    ▼                      ▼
 ┌─────────┐      ┌────────────┐         ┌────────────┐
 │ Notebook │      │ Notebook   │         │ Notebook   │
 │ 01: ETL  │─────▶│ 02: H3     │◀────────│ 01: Merge  │
 │ (fetch,  │      │ Grid +     │         │ (3 CSVs)   │
 │ classify)│      │ Enrich     │         └────────────┘
 └─────────┘      └─────┬──────┘
                         │
                         ▼
                  ┌────────────┐
                  │ Notebook   │
                  │ 03: Graph  │
                  │ Analytics  │
                  └─────┬──────┘
                         │
                         ▼
                  ┌────────────────────┐
                  │ camden_predictive  │
                  │ _model.ipynb       │
                  │ (LR → RF → XGB)   │
                  │ (Spatial Block CV) │
                  │ (FP Extraction)    │
                  └─────┬──────────────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
         .parquet    .csv/.png   .html
         (grid)    (reports)    (Pydeck)
              │          │          │
              └──────────┼──────────┘
                         ▼
                  ┌────────────┐
                  │ Streamlit  │
                  │ Dashboard  │
                  └────────────┘
```

---

## Key Outputs

| File | Description |
|------|-------------|
| `data/outputs/camden_ml_scored.parquet` | Full H3 grid with predictions, features, and confusion matrix labels |
| `data/outputs/fp_recommendations.csv` | Top 20 recommended sites ranked by model confidence |
| `data/outputs/model_comparison.csv` | LR vs RF vs XGBoost AUC summary |
| `data/outputs/roc_curves.png` | ROC curves (out-of-fold, spatial CV) |
| `data/outputs/confusion_matrix.png` | Confusion matrix (out-of-fold, spatial CV) |
| `data/outputs/feature_importance.png` | XGBoost feature importance (gain) |
| `data/outputs/camden_ml_recommendations.html` | Interactive 3D Pydeck map |

---

## Deployment

**Streamlit Community Cloud** (interactive dashboard):
1. Push repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo, select `streamlit_app.py` as the main file
4. Ensure output files are committed (the `.gitignore` already whitelists them)

**GitHub Pages** (static portfolio):
1. Go to repo Settings > Pages
2. Source: Deploy from branch > Branch: `main`, Folder: `/docs`
3. Site will be available at `https://<username>.github.io/GeoSpatial-Project/`

---

## References

- Burt, R. S. (1992). *Structural Holes: The Social Structure of Competition*. Harvard University Press.
- Boeing, G. (2017). OSMnx: New Methods for Acquiring, Constructing, Analyzing, and Visualizing Complex Street Networks. *Computers, Environment and Urban Systems*, 65, 126-139.
- Moreno, C. et al. (2021). Introducing the "15-Minute City". *Journal of Urban Management*, 10(1), 93-106.
- Tobler, W. R. (1970). A Computer Movie Simulating Urban Growth in the Detroit Region. *Economic Geography*, 46, 234-240.
- Uber Technologies. (2024). H3: Hexagonal Hierarchical Spatial Index. https://h3geo.org/
- Oak Ridge National Laboratory. (2023). LandScan Global Population Database. https://landscan.ornl.gov/

---

*This project was developed with AI assistance (Claude, Anthropic). Full transparency documented in `agent_collaboration_log.md`.*
