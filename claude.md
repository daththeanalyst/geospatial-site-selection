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

## 1b. Mandatory Change Logging
**After EVERY code change** to the notebook or any project file, the agent MUST:
1. Add a new entry to `agent_collaboration_log.md` documenting: what changed, why, root cause (if a fix), and user vs AI contribution.
2. Use the next available entry number (check the last `### Entry #N` in the log).
3. Do not batch multiple changes into one entry — log each change immediately after making it.

## 2. Spatial Verification Rules
- **CRS Check**: Never calculate Euclidean distance in EPSG:4326. Always verify `crs.to_epsg() == 27700`.
- **H3 Resolution**: Use Resolution 9 for walking-scale sites.
- **Null Handling**: Census CSVs often have blank cells; treat as 0 or mean-impute before the spatial join.
- **Raster Projection**: LandScan is typically WGS84; reproject the clipper (H3 geometry) to match the raster CRS for extraction, then convert result back to BNG.
