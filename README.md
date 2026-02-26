# Camden Synergy Index — Predictive Site Selection for Specialty Coffee

Binary classification on H3 spatial hexagons to identify underserved locations for specialty coffee retail in the London Borough of Camden, using multi-modal geospatial features and supervised machine learning.

**Programme**: MSc Business Analytics (MSIN0097 Predictive Analytics)
**Study Area**: London Borough of Camden (~22 km², ~600 H3 Res-9 hexagons)
**Theoretical Framework**: Burt's Structural Hole Theory (1992) — False Positives as market gaps

---

## Quick Start

```bash
# 1. Clone the repository
git clone https://github.com/daththeanalyst/geospatial-site-selection.git
cd geospatial-site-selection

# 2. Create environment and install dependencies
pip install -r requirements.txt

# 3. Run the unified notebook (Jupyter, VS Code, or any .ipynb-compatible environment)
camden_synergy_index.ipynb   # End-to-end: ETL → H3 grid → graph analytics → ML → recommendations

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
| **OpenStreetMap POIs** | OSMnx (programmatic) | Auto-fetched via `ox.features_from_place()` | No manual download needed |

**Census tables required** (Output Area level, England & Wales):
- TS007 — Age by single year (we extract `age_16_to_34_perc`, `age_65_plus_perc`)
- TS066 — Economic activity status (we extract `employed_total_perc`, `retired_perc`, `unemployed_perc`)
- TS067 — Highest qualification (we extract `level4_perc`, `no_qualifications_perc`)

---

## Project Structure

```
GeoSpatial Project/
├── camden_synergy_index.ipynb          # Unified end-to-end notebook (ETL → H3 → Graph → ML)
├── streamlit_app.py                    # Interactive 4-tab dashboard
├── requirements.txt                    # Python dependencies
├── agent_collaboration_log.md          # AI-Human collaboration audit (Appendix)
├── CLAUDE.md                           # Agent runbook (spatial verification rules)
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
 ┌──────────────────────────────────────────────────────┐
 │           camden_synergy_index.ipynb                 │
 │                                                      │
 │  Section 1: ETL ─── fetch POIs, load raster/census   │
 │       │                                              │
 │       ▼                                              │
 │  Section 1.4: H3 Grid ─── hexagonal indexing         │
 │       │                                              │
 │       ▼                                              │
 │  Section 1.6: Graph Analytics ─── centrality metrics  │
 │       │                                              │
 │       ▼                                              │
 │  Section 2–4: Target + EDA + Spatial CV              │
 │       │                                              │
 │       ▼                                              │
 │  Section 5–8: LR → RF → XGBoost + Evaluation        │
 │       │                                              │
 │       ▼                                              │
 │  Section 9–11: Recommendations + Model Card          │
 └──────────────────────┬───────────────────────────────┘
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
3. Site will be available at `https://daththeanalyst.github.io/geospatial-site-selection/`

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
