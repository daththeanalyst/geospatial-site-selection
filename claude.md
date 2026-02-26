# Agent Runbook: Retail Site Selection Mentor Series

This document provides technical instructions for an AI agent to execute and maintain the 3-part modular geospatial pipeline.

## 1. Pipeline Execution Flow
1. **`01_ingest_and_clean.ipynb`**:
    - Load LandScan Raster (`landscan-mosaic-unitedkingdom-v1.tif`).
    - Load Digimap Census CSVs.
    - Fetch Camden Boundary (EPSG:4326) via OSMnx and **immediately reproject to EPSG:27700**.
    - Normalize all vector data to centroids.
    - Save to `data/processed/`.

2. **`02_spatial_indexing_and_enrichment.ipynb`**:
    - Generate H3 (Res 9) hexagons over the Camden BNG boundary.
    - Aggregate Raster Population via `rasterstats.zonal_stats`.
    - Join Census CSV data to hexagons using Areal Interpolation or Spatial Join.
    - Save as `data/outputs/camden_h3_grid.parquet`.

3. **`03_analytics_and_vision.ipynb`**:
    - Construct a NetworkX graph where Hexagons are Nodes.
    - Add Edges based on H3 adjacency (walking paths).
    - Calculate Site Scores: $Score = (\sum Synergy - 10 \times \sum Competitors) \times Pop\_Normalized$.
    - Export interactive HTML maps (Kepler/Pydeck).

## 2. Spatial Verification Rules
- **CRS Check**: Never calculate Euclidean distance in EPSG:4326. Always verify `crs.to_epsg() == 27700`.
- **H3 Resolution**: Use Resolution 9 for walking-scale sites.
- **Null Handling**: Census CSVs often have blank cells; treat as 0 or mean-impute before the spatial join.
- **Raster Projection**: LandScan is typically WGS84; reproject the clipper (H3 geometry) to match the raster CRS for extraction, then convert result back to BNG.
