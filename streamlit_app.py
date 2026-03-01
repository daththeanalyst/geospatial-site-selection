"""
London Retail Site Selection Dashboard
====================================================
Interactive visualisation of the ML-driven site recommendation pipeline.
Users can choose a business type, explore all of London, drill into specific
boroughs, or search by postcode to find the best locations.

Launch: streamlit run streamlit_app.py
"""

import os
import streamlit as st
import pandas as pd
import geopandas as gpd
import numpy as np
import pydeck as pdk
import plotly.express as px
import plotly.graph_objects as go

# ── Page Configuration ──────────────────────────────────────────────────────
st.set_page_config(
    page_title="London Retail Site Selection",
    page_icon="\U0001F4CD",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        padding: 1.5rem 2rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
    }
    .main-header h1 { color: #e94560; margin: 0; font-size: 1.8rem; }
    .main-header p { color: #aaa; margin: 0.3rem 0 0 0; font-size: 0.95rem; }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem 1.2rem;
        border-radius: 8px;
        border-left: 4px solid #e94560;
        text-align: center;
    }
    .metric-card h3 { margin: 0; color: #1a1a2e; font-size: 1.8rem; }
    .metric-card p { margin: 0; color: #666; font-size: 0.85rem; }
    .legend-item { display: inline-block; margin-right: 1.2rem; }
    .legend-dot {
        display: inline-block; width: 12px; height: 12px;
        border-radius: 50%; margin-right: 4px; vertical-align: middle;
    }
</style>
""", unsafe_allow_html=True)


# ── Business Type Configuration ────────────────────────────────────────────
BIZ_TYPES = {
    'cafe':       {'label': 'Coffee Shop / Cafe',  'emoji': '\u2615'},
    'restaurant': {'label': 'Restaurant',           'emoji': '\U0001F37D\uFE0F'},
    'pub':        {'label': 'Pub / Bar',            'emoji': '\U0001F37A'},
    'fast_food':  {'label': 'Fast Food',            'emoji': '\U0001F354'},
    'gym':        {'label': 'Gym / Fitness',        'emoji': '\U0001F3CB\uFE0F'},
    'bakery':     {'label': 'Bakery',               'emoji': '\U0001F950'},
}

ALL_POI_KEYS = ['cafe', 'restaurant', 'pub', 'fast_food', 'gym', 'bakery',
                'supermarket', 'office', 'library', 'university', 'station']


# ── Data Loading ────────────────────────────────────────────────────────────
DATA_DIR = "data/outputs"

@st.cache_resource
def load_grid():
    """Load the ML-scored hex grid and convert to WGS84 for visualisation."""
    path = os.path.join(DATA_DIR, "london_ml_scored.parquet")
    grid = gpd.read_parquet(path)
    grid_wgs84 = grid.to_crs(epsg=4326)
    grid_wgs84["latitude"] = grid_wgs84.geometry.centroid.y
    grid_wgs84["longitude"] = grid_wgs84.geometry.centroid.x
    return grid_wgs84

@st.cache_data
def load_model_comparison():
    return pd.read_csv(os.path.join(DATA_DIR, "model_comparison.csv"))

@st.cache_data
def load_feature_importances():
    path = os.path.join(DATA_DIR, "feature_importances.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    return pd.DataFrame()


# ── Check data availability ────────────────────────────────────────────────
required_files = ["london_ml_scored.parquet", "model_comparison.csv"]
missing = [f for f in required_files if not os.path.exists(os.path.join(DATA_DIR, f))]

if missing:
    st.markdown("""
    <div class="main-header">
        <h1>London Retail Site Selection</h1>
        <p>MSc Business Analytics | Predictive Retail Siting</p>
    </div>
    """, unsafe_allow_html=True)
    st.error(
        f"**Missing output files:** {', '.join(missing)}\n\n"
        "Please run the notebook pipeline before launching the dashboard:\n"
        "`camden_synergy_index.ipynb` (run all cells)"
    )
    st.stop()

# Load data
grid = load_grid()
models_df = load_model_comparison()
fi_df = load_feature_importances()


# ── Sidebar: Business Type + Area Selection ──────────────────────────────
with st.sidebar:
    st.header("Business Type")
    biz_key = st.selectbox(
        "What do you want to open?",
        options=list(BIZ_TYPES.keys()),
        format_func=lambda k: f"{BIZ_TYPES[k]['emoji']} {BIZ_TYPES[k]['label']}",
        index=0,
    )
    biz_label = BIZ_TYPES[biz_key]['label']
    biz_emoji = BIZ_TYPES[biz_key]['emoji']

    st.markdown("---")
    st.header("Area Selection")

    all_boroughs = sorted(grid["borough"].dropna().unique().tolist())

    area_mode = st.radio(
        "View mode:",
        options=["All of London", "Select Borough(s)", "Search by Postcode"],
        index=0,
        help="Choose how to filter the map and recommendations",
    )

    selected_boroughs = None
    postcode_point = None
    search_radius_m = 800
    area_label = "All London"

    if area_mode == "Select Borough(s)":
        selected_boroughs = st.multiselect(
            "Choose borough(s):",
            options=all_boroughs,
            default=[],
            help="Select one or more London boroughs",
        )
        if selected_boroughs:
            area_label = ", ".join(selected_boroughs)
        else:
            st.warning("Select at least one borough, or switch to 'All of London'.")
            area_label = "All London"

    elif area_mode == "Search by Postcode":
        postcode_input = st.text_input(
            "Enter postcode (e.g., WC1E 6BT):",
            help="We'll find the nearest hexagons within a radius",
        )
        search_radius_m = st.slider("Search radius (metres):", 200, 2000, 800, 100)

        if postcode_input:
            try:
                from geopy.geocoders import Nominatim
                from shapely.geometry import Point as ShapelyPoint

                geolocator = Nominatim(user_agent="retail_site_selection_v2")
                location = geolocator.geocode(f"{postcode_input}, London, UK")
                if location:
                    postcode_point = ShapelyPoint(location.longitude, location.latitude)
                    area_label = f"Near {postcode_input} ({search_radius_m}m)"
                else:
                    st.error(f"Could not geocode: {postcode_input}")
            except ImportError:
                st.error("Install geopy: `pip install geopy`")
            except Exception as e:
                st.error(f"Geocoding error: {e}")

    st.markdown("---")


# ── Dynamic column names based on selected business type ─────────────────
COL_PROB = f"predicted_prob_{biz_key}"
COL_HAS = f"has_{biz_key}"
COL_OUTCOME = f"outcome_{biz_key}"
COL_NEARBY = f"nearby_{biz_key}"


# ── Apply Area Filter ──────────────────────────────────────────────────────
if area_mode == "Select Borough(s)" and selected_boroughs:
    active_grid = grid[grid["borough"].isin(selected_boroughs)].copy()
elif area_mode == "Search by Postcode" and postcode_point is not None:
    grid_bng = grid.to_crs(epsg=27700)
    search_gdf = gpd.GeoDataFrame(
        geometry=[postcode_point], crs="EPSG:4326"
    ).to_crs(epsg=27700)
    buffer = search_gdf.geometry.iloc[0].buffer(search_radius_m)
    mask = grid_bng.geometry.intersects(buffer)
    active_grid = grid[mask.values].copy()
else:
    active_grid = grid.copy()


# ── Derived metrics (scoped to active area + selected business type) ─────
n_hexes = len(active_grid)

# Check if the required columns exist for the selected business type
has_type_cols = COL_OUTCOME in active_grid.columns

if has_type_cols:
    n_fp = len(active_grid[active_grid[COL_OUTCOME] == "False Positive (Recommendation)"])
    positive_rate = active_grid[COL_HAS].mean() if n_hexes > 0 else 0
else:
    n_fp = 0
    positive_rate = 0

# Model comparison for selected type
if "business_type" in models_df.columns:
    type_models = models_df[models_df["business_type"] == biz_key]
    if len(type_models) > 0:
        best_auc = type_models["Mean AUC"].max()
        best_model_name = type_models.loc[type_models["Mean AUC"].idxmax(), "Model"]
    else:
        best_auc = models_df["Mean AUC"].max()
        best_model_name = models_df.loc[models_df["Mean AUC"].idxmax(), "Model"]
else:
    best_auc = models_df["Mean AUC"].max()
    best_model_name = models_df.loc[models_df["Mean AUC"].idxmax(), "Model"]

# Dynamic feature columns
POI_FEATURE_COLS = [f"n_{t}" for t in ALL_POI_KEYS if t != biz_key]
COMPETITION_COL = [COL_NEARBY] if COL_NEARBY in active_grid.columns else []
FEATURE_COLS = [
    "population", "employed_total_perc", "age_16_to_34_perc",
    "level4_perc", "retired_perc", "no_qualifications_perc",
    "degree_centrality", "betweenness_centrality",
    "closeness_centrality", "clustering_coeff",
    "eigenvector_centrality", "pagerank",
] + [c for c in POI_FEATURE_COLS if c in active_grid.columns] + COMPETITION_COL


# ── Header ──────────────────────────────────────────────────────────────────
st.markdown(f"""
<div class="main-header">
    <h1>{biz_emoji} London {biz_label} — Site Selection Dashboard</h1>
    <p>Viewing: {area_label} | {n_hexes:,} hexagons | Predicting: {biz_label} | Spatial Block CV</p>
</div>
""", unsafe_allow_html=True)

# ── Tabs ────────────────────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "Overview", "Interactive Map", "Site Recommendations", "Feature Analysis"
])


# ═══════════════════════════════════════════════════════════════════════════
# TAB 1: OVERVIEW
# ═══════════════════════════════════════════════════════════════════════════
with tab1:
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-card">
            <h3>{n_hexes:,}</h3><p>H3 Hexagons (Res 9)</p>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card">
            <h3>{best_auc:.3f}</h3><p>Best ROC-AUC ({best_model_name})</p>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="metric-card">
            <h3>{n_fp}</h3><p>Recommended Sites (FP)</p>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="metric-card">
            <h3>{positive_rate:.1%}</h3><p>{biz_label} Presence Rate</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Methodology")
        st.markdown(f"""
        This pipeline identifies **structural holes** in London's {biz_label.lower()} market
        using supervised machine learning on hexagonal spatial units.

        **Pipeline**: H3 Grid (Res 9, ~174m) -> Feature Engineering (23 features across
        5 modalities) -> Spatial Block CV (H3 parent-cell partitioning) -> Model Comparison
        (LR vs RF vs XGBoost) -> GridSearchCV Tuning -> False Positive Extraction

        **Key Insight**: False Positives -- hexagons the model predicts *should* have a
        {biz_label.lower()} but currently don't -- represent untapped market opportunities.
        These are **Burt's Structural Holes** validated by data rather than heuristic scoring.

        **Currently viewing**: {area_label}
        """)

        st.subheader(f"Model Comparison ({biz_label})")
        if "business_type" in models_df.columns:
            display_models = models_df[models_df["business_type"] == biz_key]
        else:
            display_models = models_df
        if len(display_models) > 0:
            st.dataframe(
                display_models[["Model", "Mean AUC", "Std AUC"]].style.format(
                    {"Mean AUC": "{:.3f}", "Std AUC": "{:.3f}"}
                ),
                use_container_width=True,
                hide_index=True,
            )

    with col_right:
        st.subheader("Confusion Matrix (Out-of-Fold)")
        cm_path = os.path.join(DATA_DIR, "confusion_matrix.png")
        if os.path.exists(cm_path):
            st.image(cm_path, use_container_width=True)
        else:
            st.info("Run the ML notebook to generate the confusion matrix plot.")

        st.subheader("Prediction Outcomes")
        if n_hexes > 0 and has_type_cols:
            outcome_counts = active_grid[COL_OUTCOME].value_counts()
            fig_pie = px.pie(
                names=outcome_counts.index,
                values=outcome_counts.values,
                color=outcome_counts.index,
                color_discrete_map={
                    "False Positive (Recommendation)": "#27ae60",
                    "True Positive": "#e74c3c",
                    "True Negative": "#95a5a6",
                    "False Negative": "#f39c12",
                },
                hole=0.4,
            )
            fig_pie.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                height=280,
                legend=dict(font=dict(size=11)),
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    # Borough summary (only in All London mode)
    if area_mode == "All of London" and "borough" in active_grid.columns and has_type_cols:
        st.markdown("---")
        st.subheader(f"Top Opportunities by Borough ({biz_label})")
        fp_all = active_grid[active_grid[COL_OUTCOME] == "False Positive (Recommendation)"]
        if len(fp_all) > 0:
            borough_summary = (
                fp_all.groupby("borough")
                .agg(
                    recommended_sites=(COL_PROB, "count"),
                    avg_confidence=(COL_PROB, "mean"),
                    avg_population=("population", "mean"),
                )
                .sort_values("recommended_sites", ascending=False)
                .reset_index()
            )
            borough_summary.columns = ["Borough", "Recommended Sites", "Avg Confidence", "Avg Population"]

            st.dataframe(
                borough_summary.style.format({
                    "Avg Confidence": "{:.3f}",
                    "Avg Population": "{:.0f}",
                }),
                use_container_width=True,
                hide_index=True,
                height=400,
            )


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2: INTERACTIVE MAP
# ═══════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader(f"3D Hex Map — {biz_label} Predictions")

    st.markdown(f"""
    <div style="margin-bottom: 1rem;">
        <span class="legend-item"><span class="legend-dot" style="background:#27ae60;"></span> Recommendation (FP)</span>
        <span class="legend-item"><span class="legend-dot" style="background:#e74c3c;"></span> Existing {biz_label} (TP)</span>
        <span class="legend-item"><span class="legend-dot" style="background:#95a5a6;"></span> Not Suitable (TN)</span>
        <span class="legend-item"><span class="legend-dot" style="background:#f39c12;"></span> Missed by Model (FN)</span>
    </div>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.header("Map Filters")
        outcome_filter = st.multiselect(
            "Show outcomes:",
            options=[
                "False Positive (Recommendation)",
                "True Positive",
                "True Negative",
                "False Negative",
            ],
            default=[
                "False Positive (Recommendation)",
                "True Positive",
                "False Negative",
            ],
        )
        confidence_min = st.slider(
            "Min confidence (FP only):",
            min_value=0.0, max_value=1.0, value=0.0, step=0.05,
        )
        pop_min = int(active_grid["population"].min()) if n_hexes > 0 else 0
        pop_max = int(active_grid["population"].max()) if n_hexes > 0 else 100
        pop_range = st.slider(
            "Population range:",
            min_value=pop_min,
            max_value=max(pop_max, pop_min + 1),
            value=(pop_min, max(pop_max, pop_min + 1)),
        )
        pitch = st.slider("Map pitch:", 0, 70, 50)

    if has_type_cols:
        filtered = active_grid[active_grid[COL_OUTCOME].isin(outcome_filter)].copy()
        filtered = filtered[
            (filtered["population"] >= pop_range[0])
            & (filtered["population"] <= pop_range[1])
        ]
        if confidence_min > 0:
            is_fp = filtered[COL_OUTCOME] == "False Positive (Recommendation)"
            filtered = filtered[~is_fp | (filtered[COL_PROB] >= confidence_min)]
    else:
        filtered = active_grid.copy()

    st.caption(f"Showing {len(filtered):,} of {n_hexes:,} hexagons ({area_label})")

    if len(filtered) > 0 and has_type_cols:
        color_map = {
            "False Positive (Recommendation)": [39, 174, 96, 200],
            "True Positive": [231, 76, 60, 160],
            "True Negative": [149, 165, 166, 80],
            "False Negative": [243, 156, 18, 160],
        }

        viz_cols = ["h3_index", COL_OUTCOME, COL_PROB, "population",
                    "level4_perc", "latitude", "longitude"]
        if "borough" in filtered.columns:
            viz_cols.append("borough")
        if COL_NEARBY in filtered.columns:
            viz_cols.append(COL_NEARBY)
        # Add the count of this business type for tooltip
        n_col = f"n_{biz_key}"
        if n_col in filtered.columns:
            viz_cols.append(n_col)

        viz_df = filtered[[c for c in viz_cols if c in filtered.columns]].copy()

        viz_df["color"] = viz_df[COL_OUTCOME].map(color_map)
        viz_df["elevation"] = viz_df.apply(
            lambda r: r[COL_PROB] * 500
            if r[COL_OUTCOME] == "False Positive (Recommendation)" else 10,
            axis=1,
        )
        viz_df[COL_PROB] = viz_df[COL_PROB].round(3)
        viz_df["population"] = viz_df["population"].round(0)
        viz_df["level4_perc"] = viz_df["level4_perc"].round(1)

        layer = pdk.Layer(
            "H3HexagonLayer",
            viz_df,
            pickable=True,
            stroked=True,
            filled=True,
            extruded=True,
            get_hexagon="h3_index",
            get_fill_color="color",
            get_elevation="elevation",
            elevation_scale=1,
        )

        center_lat = filtered["latitude"].mean()
        center_lon = filtered["longitude"].mean()

        if area_mode == "All of London":
            zoom_level = 10.0
        elif area_mode == "Search by Postcode":
            zoom_level = 14.0
        elif selected_boroughs and len(selected_boroughs) <= 2:
            zoom_level = 12.5
        else:
            zoom_level = 11.0

        view_state = pdk.ViewState(
            latitude=center_lat, longitude=center_lon,
            zoom=zoom_level, pitch=pitch, bearing=-15,
        )

        borough_tt = "<b>Borough:</b> {borough}<br>" if "borough" in viz_df.columns else ""
        nearby_tt = f"<b>Nearby Competition:</b> {{{COL_NEARBY}}}<br>" if COL_NEARBY in viz_df.columns else ""
        count_tt = f"<b>{biz_label} in Hex:</b> {{{n_col}}}<br>" if n_col in viz_df.columns else ""
        tooltip = {
            "html": (
                f"{borough_tt}"
                f"<b>Outcome:</b> {{{COL_OUTCOME}}}<br>"
                f"<b>Confidence:</b> {{{COL_PROB}}}<br>"
                "<b>Population:</b> {population}<br>"
                "<b>Level 4%:</b> {level4_perc}<br>"
                f"{count_tt}"
                f"{nearby_tt}"
            ),
            "style": {
                "backgroundColor": "#1a1a2e",
                "color": "white",
                "fontSize": "12px",
            },
        }

        st.pydeck_chart(
            pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip),
            use_container_width=True,
        )
    else:
        st.info("No hexagons match the current filters. Adjust the sidebar settings.")


# ═══════════════════════════════════════════════════════════════════════════
# TAB 3: SITE RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader(f"Top Recommended Sites for {biz_label} — {area_label}")
    st.markdown(
        f"These hexagons possess all the learned features of successful {biz_label.lower()} locations "
        "-- high footfall, educated demographics, strong transit connectivity -- "
        f"but **no {biz_label.lower()} currently exists**. They represent Burt's Structural Holes."
    )

    if has_type_cols:
        fp_grid = active_grid[active_grid[COL_OUTCOME] == "False Positive (Recommendation)"]
        tp_grid = active_grid[active_grid[COL_OUTCOME] == "True Positive"]
    else:
        fp_grid = active_grid.head(0)
        tp_grid = active_grid.head(0)

    if len(fp_grid) > 0:
        fp_display = fp_grid.nlargest(min(30, len(fp_grid)), COL_PROB).copy()
        fp_display.insert(0, "Rank", range(1, len(fp_display) + 1))

        rename_map = {
            COL_PROB: "Confidence",
            "population": "Population",
            "level4_perc": "Level 4 %",
            "age_16_to_34_perc": "Age 16-34 %",
            "employed_total_perc": "Employed %",
            "betweenness_centrality": "Betweenness",
        }
        if COL_NEARBY in fp_display.columns:
            rename_map[COL_NEARBY] = "Nearby Competition"

        fp_display = fp_display.rename(columns=rename_map)

        display_cols = [
            "Rank", "borough", "h3_index", "Confidence", "Nearby Competition",
            "Population", "Level 4 %", "Betweenness",
        ]
        available_cols = [c for c in display_cols if c in fp_display.columns]

        format_dict = {
            "Confidence": "{:.3f}",
            "Population": "{:.0f}",
            "Level 4 %": "{:.1f}",
            "Betweenness": "{:.4f}",
        }
        if "Nearby Competition" in available_cols:
            format_dict["Nearby Competition"] = "{:.0f}"

        st.dataframe(
            fp_display[available_cols].style.format(format_dict),
            use_container_width=True,
            hide_index=True,
            height=400,
        )
    else:
        st.info(f"No recommended {biz_label.lower()} sites in the selected area.")

    st.markdown("---")

    # Demographic comparison
    st.subheader(f"Demographic Profile: {biz_label} Recommendations vs {area_label}")

    profile_cols = ["population", "level4_perc", "age_16_to_34_perc",
                    "employed_total_perc", "betweenness_centrality"]
    if COL_NEARBY in active_grid.columns:
        profile_cols.append(COL_NEARBY)
    profile_labels = ["Population", "Level 4 Qual %", "Age 16-34 %",
                      "Employment %", "Betweenness"]
    if COL_NEARBY in active_grid.columns:
        profile_labels.append("Nearby Competition")

    if n_hexes > 0:
        comparison = pd.DataFrame({
            "Feature": profile_labels,
            f"{area_label} Average": [active_grid[c].mean() for c in profile_cols],
            "Recommended Sites (FP)": [fp_grid[c].mean() for c in profile_cols] if len(fp_grid) > 0 else [0]*len(profile_cols),
            f"Existing {biz_label} (TP)": [tp_grid[c].mean() for c in profile_cols] if len(tp_grid) > 0 else [0]*len(profile_cols),
        })

        comparison_norm = comparison.copy()
        avg_col = f"{area_label} Average"
        for col in [avg_col, "Recommended Sites (FP)", f"Existing {biz_label} (TP)"]:
            comparison_norm[col] = comparison[col] / comparison[avg_col].replace(0, np.nan)

        fig_comp = go.Figure()
        colors = {avg_col: "#3498db", "Recommended Sites (FP)": "#27ae60", f"Existing {biz_label} (TP)": "#e74c3c"}
        for col_name, color in colors.items():
            fig_comp.add_trace(go.Bar(
                name=col_name,
                x=comparison_norm["Feature"],
                y=comparison_norm[col_name],
                marker_color=color,
            ))
        fig_comp.update_layout(
            barmode="group",
            title=f"Feature Comparison (Normalised to {area_label} Average = 1.0)",
            yaxis_title=f"Ratio to {area_label} Average",
            height=400,
            margin=dict(t=40, b=40),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        fig_comp.add_hline(y=1.0, line_dash="dash", line_color="grey", annotation_text="Average")
        st.plotly_chart(fig_comp, use_container_width=True)

    # Radar chart for top 5 FP sites
    if len(fp_grid) >= 5:
        st.subheader(f"Feature Profile — Top 5 Recommended {biz_label} Sites")
        radar_cols = ["population", "level4_perc", "age_16_to_34_perc",
                      "betweenness_centrality"]
        if COL_NEARBY in active_grid.columns:
            radar_cols.append(COL_NEARBY)
        radar_labels = ["Population", "Level 4 %", "Age 16-34 %", "Betweenness"]
        if COL_NEARBY in active_grid.columns:
            radar_labels.append("Nearby Competition")

        top5 = fp_grid.nlargest(5, COL_PROB)

        radar_data = top5[radar_cols].copy()
        for col in radar_cols:
            col_min = active_grid[col].min()
            col_max = active_grid[col].max()
            radar_data[col] = (radar_data[col] - col_min) / (col_max - col_min + 1e-9)

        fig_radar = go.Figure()
        for i, (idx, row) in enumerate(radar_data.iterrows()):
            borough_label = top5.loc[idx, "borough"] if "borough" in top5.columns else f"Site {i+1}"
            fig_radar.add_trace(go.Scatterpolar(
                r=[row[c] for c in radar_cols] + [row[radar_cols[0]]],
                theta=radar_labels + [radar_labels[0]],
                name=f"#{i+1} ({borough_label})",
                fill="toself",
                opacity=0.6,
            ))
        fig_radar.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1])),
            height=400,
            margin=dict(t=30, b=30),
        )
        st.plotly_chart(fig_radar, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 4: FEATURE ANALYSIS
# ═══════════════════════════════════════════════════════════════════════════
with tab4:
    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader(f"ROC Curves ({biz_label})")
        # Dynamic ROC curve from data
        if has_type_cols and n_hexes > 0:
            try:
                from sklearn.metrics import roc_curve as sk_roc_curve, roc_auc_score as sk_auc
                y_true = active_grid[COL_HAS]
                y_scores = active_grid[COL_PROB]
                if y_true.nunique() > 1:
                    fpr, tpr, _ = sk_roc_curve(y_true, y_scores)
                    auc_val = sk_auc(y_true, y_scores)
                    fig_roc = go.Figure()
                    fig_roc.add_trace(go.Scatter(
                        x=fpr, y=tpr, mode='lines',
                        name=f'{biz_label} (AUC={auc_val:.3f})',
                        line=dict(width=2, color='#e94560'),
                    ))
                    fig_roc.add_trace(go.Scatter(
                        x=[0, 1], y=[0, 1], mode='lines',
                        line=dict(dash='dash', color='grey'), name='Random',
                    ))
                    fig_roc.update_layout(
                        height=400, xaxis_title='False Positive Rate',
                        yaxis_title='True Positive Rate',
                        margin=dict(t=20, b=20),
                    )
                    st.plotly_chart(fig_roc, use_container_width=True)
                else:
                    st.info("Not enough class variation to plot ROC curve for this area.")
            except ImportError:
                roc_path = os.path.join(DATA_DIR, "roc_curves.png")
                if os.path.exists(roc_path):
                    st.image(roc_path, use_container_width=True)
        else:
            st.info("Select a business type with available predictions.")

    with col_b:
        st.subheader(f"Feature Importance ({biz_label})")
        if len(fi_df) > 0 and "business_type" in fi_df.columns:
            fi_type = fi_df[fi_df["business_type"] == biz_key].nlargest(15, "importance")
            if len(fi_type) > 0:
                fig_fi = px.bar(
                    fi_type, x="importance", y="feature", orientation="h",
                    color="importance", color_continuous_scale="Blues",
                )
                fig_fi.update_layout(
                    height=400, yaxis={"categoryorder": "total ascending"},
                    margin=dict(t=20, b=20),
                )
                st.plotly_chart(fig_fi, use_container_width=True)
            else:
                st.info(f"No feature importance data for {biz_label}.")
        else:
            fi_path = os.path.join(DATA_DIR, "feature_importance.png")
            if os.path.exists(fi_path):
                st.image(fi_path, use_container_width=True)
            else:
                st.info("Run the ML notebook to generate feature importance data.")

    st.markdown("---")

    # Co-occurrence heatmap
    st.subheader("Business Type Co-occurrence Heatmap")
    st.markdown(
        "Shows which business types tend to appear in the same hexagons. "
        "Positive correlations suggest complementary foot traffic patterns."
    )

    biz_has_cols = {k: f"has_{k}" for k in BIZ_TYPES.keys()}
    available_biz_cols = {k: v for k, v in biz_has_cols.items() if v in active_grid.columns}

    if len(available_biz_cols) > 1 and n_hexes > 0:
        presence_df = active_grid[list(available_biz_cols.values())]
        presence_df.columns = [BIZ_TYPES[k]["label"] for k in available_biz_cols.keys()]
        cooccur = presence_df.corr()

        fig_cooccur = px.imshow(
            cooccur, text_auto=".2f",
            color_continuous_scale="RdYlGn", zmin=-0.3, zmax=0.8,
            title="Pairwise correlation of business type presence across hexagons",
        )
        fig_cooccur.update_layout(height=450, margin=dict(t=40, b=20))
        st.plotly_chart(fig_cooccur, use_container_width=True)
    else:
        st.info("Co-occurrence data not available. Run the notebook first.")

    st.markdown("---")

    # Feature correlation matrix
    st.subheader(f"Feature Correlation Matrix — {area_label}")
    available_features = [c for c in FEATURE_COLS if c in active_grid.columns]

    if n_hexes > 0 and has_type_cols:
        corr_cols = available_features + [COL_HAS]
        corr_matrix = active_grid[corr_cols].corr()

        fig_corr = px.imshow(
            corr_matrix,
            text_auto=".2f",
            color_continuous_scale="RdBu_r",
            zmin=-1, zmax=1,
            aspect="auto",
        )
        fig_corr.update_layout(height=550, margin=dict(t=30, b=30))
        st.plotly_chart(fig_corr, use_container_width=True)

    st.markdown("---")

    # Feature distribution explorer
    st.subheader(f"Feature Distribution by {biz_label} Presence — {area_label}")
    selected_feature = st.selectbox(
        "Select a feature to explore:",
        options=available_features,
        index=available_features.index("population") if "population" in available_features else 0,
    )

    if n_hexes > 0 and has_type_cols:
        plot_data = active_grid[[selected_feature, COL_HAS]].copy()
        plot_data["target_label"] = plot_data[COL_HAS].map(
            {0: f"No {biz_label}", 1: f"Has {biz_label}"}
        )

        fig_box = px.box(
            plot_data,
            x="target_label",
            y=selected_feature,
            color="target_label",
            color_discrete_map={
                f"No {biz_label}": "#3498db",
                f"Has {biz_label}": "#e74c3c",
            },
            labels={"target_label": ""},
        )
        fig_box.update_layout(height=400, showlegend=False, margin=dict(t=20, b=20))
        st.plotly_chart(fig_box, use_container_width=True)


# ── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #888; font-size: 0.85rem;'>"
    "London Retail Site Selection | MSc Business Analytics 2026 | "
    "Built with Streamlit + Pydeck + Plotly"
    "</p>",
    unsafe_allow_html=True,
)
