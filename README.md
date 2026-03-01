# London Synergy Index — Predictive Retail Site Selection

Binary classification on H3 spatial hexagons to identify underserved locations for **6 retail business types** across **all 33 London boroughs**, using multi-modal geospatial features and supervised machine learning.

**Programme**: MSc Business Analytics (MSIN0097 Predictive Analytics)
**Study Area**: Greater London (~1,572 km², ~55,000 H3 Res-9 hexagons, 33 boroughs)
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
                             # NOTE: First run takes ~80-130 minutes for all of London (6 business types)

# 4. Launch the interactive dashboard
streamlit run streamlit_app.py
```

---

## Supported Business Types

| Type | OSM Tags | Use Case |
|------|----------|----------|
| Coffee Shop / Cafe | cafe, coffee_shop | Specialty coffee retail |
| Restaurant | restaurant | Full-service dining |
| Pub / Bar | pub, bar | Evening economy venues |
| Fast Food | fast_food | Quick-service restaurants |
| Gym / Fitness | gym, fitness_centre, sports_centre | Health & wellness |
| Bakery | bakery | Artisan bakery retail |

Each type has its own XGBoost model trained with spatial cross-validation. The dashboard lets users switch between types dynamically.

---

## Data Access

The pipeline requires three external datasets. OSM data is fetched programmatically; the other two must be downloaded manually.

| Dataset | Source | Access | Expected Location |
|---------|--------|--------|-------------------|
| **LandScan Global Population** | Oak Ridge National Laboratory (ORNL) | [landscan.ornl.gov](https://landscan.ornl.gov/) — free registration required | `landscan-mosaic-unitedkingdom-v1.tif` (project root) |
| **ONS Census 2021** (3 tables) | EDINA Digimap / ONS Nomis | [digimap.edina.ac.uk](https://digimap.edina.ac.uk/) or [nomis.co.uk](https://www.nomisweb.co.uk/) | `ons-age-ew-2021_*/`, `ons-economic-ew-2021_*/`, `ons-qualifications-ew-2021_*/` |
| **OpenStreetMap POIs** | OSMnx (programmatic) | Auto-fetched borough-by-borough via `ox.features_from_place()` | No manual download needed |

**Census tables required** (Output Area level, Greater London extent):
- TS007 — Age by single year (we extract `age_16_to_34_perc`, `age_65_plus_perc`)
- TS066 — Economic activity status (we extract `employed_total_perc`, `retired_perc`, `unemployed_perc`)
- TS067 — Highest qualification (we extract `level4_perc`, `no_qualifications_perc`)

---

## Project Structure

```
GeoSpatial Project/
├── camden_synergy_index.ipynb          # Unified end-to-end notebook (ETL → H3 → Graph → ML)
├── streamlit_app.py                    # Interactive dashboard with business type + area selection
├── requirements.txt                    # Python dependencies (incl. geopy for postcode search)
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
 │  Section 1: ETL ─── fetch POIs (33 boroughs),       │
 │       │        granular typing (11 POI categories)   │
 │       ▼                                              │
 │  Section 1.1: H3 Grid ─── ~55K hexagons + borough   │
 │       │           + individual POI counts per type    │
 │       │           + competition density (k=1 ring)    │
 │       ▼                                              │
 │  Section 1.6: Graph Analytics ─── 6 centrality       │
 │       │         metrics (betweenness approx. k=500)   │
 │       ▼                                              │
 │  Section 2–4: Multi-type targets + EDA + Spatial CV  │
 │       │                                              │
 │       ▼                                              │
 │  Section 5–7: LR → RF → XGBoost (tuned on cafe)     │
 │       │                                              │
 │       ▼                                              │
 │  Section 7b: Train all 6 types (shared hyperparams)  │
 │       │                                              │
 │       ▼                                              │
 │  Section 8–11: Evaluation + Recommendations + Export │
 └──────────────────────┬───────────────────────────────┘
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
         .parquet    .csv/.png   .html
         (grid)    (reports)    (Pydeck)
              │          │          │
              └──────────┼──────────┘
                         ▼
                  ┌────────────────┐
                  │   Streamlit    │
                  │   Dashboard    │
                  │ (business type │
                  │  + borough +   │
                  │  postcode)     │
                  └────────────────┘
```

---

## Interactive Dashboard Features

The Streamlit dashboard supports **business type selection** and three exploration modes:

**Business Type Selector**: Choose what you want to open (cafe, restaurant, pub, fast food, gym, bakery). All predictions, maps, and recommendations dynamically adapt.

| Mode | Description |
|------|-------------|
| **All of London** | Overview of recommendations across all 33 boroughs, with a "Top Opportunities by Borough" summary table |
| **Select Borough(s)** | Multi-select dropdown to focus on specific boroughs — all KPIs, maps, and recommendations recalculate |
| **Search by Postcode** | Enter a postcode (e.g., WC1E 6BT) and a radius to find nearby recommendations |

**4 Tabs**: Overview (KPIs, model comparison), Interactive Map (3D Pydeck with competition density), Site Recommendations (ranked table with nearby competition, demographic comparison, radar chart), Feature Analysis (dynamic ROC curves, feature importance, co-occurrence heatmap, correlation matrix, distributions)

---

## Key Outputs

| File | Description |
|------|-------------|
| `data/outputs/london_ml_scored.parquet` | Full H3 grid (~55K hexes) with predictions for all 6 types, features, borough, and confusion matrix labels (~67 columns) |
| `data/outputs/feature_importances.csv` | Per-type XGBoost feature importance (~138 rows) |
| `data/outputs/model_comparison.csv` | Per-type model AUC summary |
| `data/outputs/fp_recommendations.csv` | Top 50 cafe recommendations (legacy) |
| `data/outputs/fp_recommendations_{type}.csv` | Top 50 recommendations per business type |
| `data/outputs/roc_curves.png` | ROC curves for all 6 types (spatial CV OOF) |
| `data/outputs/confusion_matrix.png` | Confusion matrices for all 6 types |
| `data/outputs/feature_importance.png` | Feature importance for all 6 types |
| `data/outputs/london_ml_recommendations.html` | Interactive 3D Pydeck map (cafe, default) |

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
