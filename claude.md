# Agent Runbook: London Retail Site Selection

This document provides technical instructions for an AI agent to execute and maintain the unified geospatial pipeline.

## 1. Pipeline Execution Flow

**Single notebook:** `camden_synergy_index.ipynb` (end-to-end: ETL → H3 grid → graph analytics → ML → recommendations)

Key stages:
1. Load LandScan Raster, Digimap Census CSVs, crime data, transport data
2. Fetch all 33 London borough boundaries via OSMnx, reproject to **EPSG:27700**
3. Generate H3 (Res 9) hexagons, aggregate raster population via `rasterstats.zonal_stats`
4. Join Census, crime, and transport data to hexagons
5. Build NetworkX graph (H3 adjacency), compute centrality + community + Node2Vec embeddings
6. Define binary targets for 6 business types (cafe, restaurant, pub, fast_food, gym, bakery)
7. Spatial block CV (H3 Res-7 parents), train LR → RF → XGBoost
8. Evaluation suite: ROC, confusion matrix, SHAP, calibration, ablation, fairness audit
9. Export recommendations, interactive 3D Pydeck maps, portfolio assets

## 1b. Mandatory Change Logging
**After EVERY code change** to the notebook or any project file, the agent MUST:
1. Add a new entry to `agent_collaboration_log.md` documenting: what changed, why, root cause (if a fix), and user vs AI contribution.
2. Use the next available entry number (check the last `### Entry #N` in the log).
3. Do not batch multiple changes into one entry — log each change immediately after making it.

## 2. Spatial Verification Rules
- **CRS Check**: Never calculate Euclidean distance in EPSG:4326. Always verify `crs.to_epsg() == 27700`.
- **H3 Resolution**: Use Resolution 9 for walking-scale sites (~174m edge, ~0.1 km²).
- **H3 Assignment**: Convert geometries to EPSG:4326 for `h3.latlng_to_cell()`, then back to BNG for spatial ops.
- **Null Handling**: Census CSVs often have blank cells; treat as 0 or mean-impute before the spatial join.
- **Raster Projection**: LandScan is typically WGS84; reproject the clipper (H3 geometry) to match the raster CRS for extraction, then convert result back to BNG.
- **Leakage Guard**: When building features for business type X, exclude `n_X` from the feature set (e.g., cafe model must not use `n_cafe`).
