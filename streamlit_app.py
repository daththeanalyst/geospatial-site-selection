"""
Camden Specialty Coffee — Site Selection Dashboard
===================================================
Interactive visualisation of the ML-driven site recommendation pipeline.
Reads pre-computed outputs from the notebook pipeline (01 → 02 → 03 → ML).

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
    page_title="Camden Coffee Site Selection",
    page_icon="\u2615",
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


# ── Data Loading ────────────────────────────────────────────────────────────
DATA_DIR = "data/outputs"

@st.cache_resource
def load_grid():
    """Load the ML-scored hex grid and convert to WGS84 for visualisation."""
    path = os.path.join(DATA_DIR, "camden_ml_scored.parquet")
    grid = gpd.read_parquet(path)
    grid_wgs84 = grid.to_crs(epsg=4326)
    # Pre-compute lat/lng centroids for display
    grid_wgs84["latitude"] = grid_wgs84.geometry.centroid.y
    grid_wgs84["longitude"] = grid_wgs84.geometry.centroid.x
    return grid_wgs84

@st.cache_data
def load_recommendations():
    return pd.read_csv(os.path.join(DATA_DIR, "fp_recommendations.csv"))

@st.cache_data
def load_model_comparison():
    return pd.read_csv(os.path.join(DATA_DIR, "model_comparison.csv"))


# ── Check data availability ────────────────────────────────────────────────
required_files = [
    "camden_ml_scored.parquet",
    "fp_recommendations.csv",
    "model_comparison.csv",
]
missing = [f for f in required_files if not os.path.exists(os.path.join(DATA_DIR, f))]

if missing:
    st.markdown("""
    <div class="main-header">
        <h1>Camden Coffee Site Selection</h1>
        <p>MSc Business Analytics | Predictive Retail Siting</p>
    </div>
    """, unsafe_allow_html=True)
    st.error(
        f"**Missing output files:** {', '.join(missing)}\n\n"
        "Please run all 4 notebooks in order before launching the dashboard:\n"
        "1. `01_ingest_and_clean.ipynb`\n"
        "2. `02_spatial_indexing_and_enrichment.ipynb`\n"
        "3. `03_analytics_and_vision.ipynb`\n"
        "4. `camden_predictive_model.ipynb`"
    )
    st.stop()

# Load data
grid = load_grid()
fp_df = load_recommendations()
models_df = load_model_comparison()

# ── Derived metrics ─────────────────────────────────────────────────────────
n_hexes = len(grid)
n_fp = len(grid[grid["outcome"] == "False Positive (Recommendation)"])
best_auc = models_df["Mean AUC"].max()
best_model_name = models_df.loc[models_df["Mean AUC"].idxmax(), "Model"]
positive_rate = grid["has_coffee_shop"].mean()

FEATURE_COLS = [
    "population", "employed_total_perc", "age_16_to_34_perc",
    "level4_perc", "retired_perc", "no_qualifications_perc",
    "degree_centrality", "betweenness_centrality",
    "closeness_centrality", "clustering_coeff",
    "n_synergy", "n_anchors",
]

# ── Header ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>Camden Specialty Coffee — Site Selection Dashboard</h1>
    <p>Binary classification on H3 hexagons | LandScan + ONS Census + NetworkX | Spatial Block CV</p>
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
    # KPI cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-card">
            <h3>{n_hexes}</h3><p>H3 Hexagons (Res 9)</p>
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
            <h3>{positive_rate:.1%}</h3><p>Coffee Shop Presence Rate</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # Methodology and model comparison
    col_left, col_right = st.columns([1, 1])

    with col_left:
        st.subheader("Methodology")
        st.markdown("""
        This pipeline identifies **structural holes** in Camden's specialty coffee market
        using supervised machine learning on hexagonal spatial units.

        **Pipeline**: H3 Grid (Res 9, ~174m) → Feature Engineering (12 features across
        4 modalities) → Spatial Block CV (H3 parent-cell partitioning) → Model Comparison
        (LR vs RF vs XGBoost) → GridSearchCV Tuning → False Positive Extraction

        **Key Insight**: False Positives — hexagons the model predicts *should* have a coffee
        shop but currently don't — represent untapped market opportunities.
        These are **Burt's Structural Holes** validated by data rather than heuristic scoring.
        """)

        st.subheader("Model Comparison (Spatial CV)")
        st.dataframe(
            models_df.style.format({"Mean AUC": "{:.3f}", "Std AUC": "{:.3f}"}),
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

        # Outcome distribution
        st.subheader("Prediction Outcomes")
        outcome_counts = grid["outcome"].value_counts()
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


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2: INTERACTIVE MAP
# ═══════════════════════════════════════════════════════════════════════════
with tab2:
    st.subheader("3D Hex Map — Confusion Matrix Overlay")

    # Legend
    st.markdown("""
    <div style="margin-bottom: 1rem;">
        <span class="legend-item"><span class="legend-dot" style="background:#27ae60;"></span> Recommendation (FP)</span>
        <span class="legend-item"><span class="legend-dot" style="background:#e74c3c;"></span> Existing Shop (TP)</span>
        <span class="legend-item"><span class="legend-dot" style="background:#95a5a6;"></span> Not Suitable (TN)</span>
        <span class="legend-item"><span class="legend-dot" style="background:#f39c12;"></span> Missed by Model (FN)</span>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar filters
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
                "True Negative",
                "False Negative",
            ],
        )
        confidence_min = st.slider(
            "Min confidence (FP only):",
            min_value=0.0, max_value=1.0, value=0.0, step=0.05,
        )
        pop_range = st.slider(
            "Population range:",
            min_value=int(grid["population"].min()),
            max_value=int(grid["population"].max()),
            value=(int(grid["population"].min()), int(grid["population"].max())),
        )
        pitch = st.slider("Map pitch:", 0, 70, 50)

    # Apply filters
    filtered = grid[grid["outcome"].isin(outcome_filter)].copy()
    filtered = filtered[
        (filtered["population"] >= pop_range[0])
        & (filtered["population"] <= pop_range[1])
    ]
    # Confidence filter: only applies to FP hexes (keep all others)
    if confidence_min > 0:
        is_fp = filtered["outcome"] == "False Positive (Recommendation)"
        filtered = filtered[~is_fp | (filtered["predicted_prob"] >= confidence_min)]

    st.caption(f"Showing {len(filtered)} of {n_hexes} hexagons")

    # Build Pydeck map
    color_map = {
        "False Positive (Recommendation)": [39, 174, 96, 200],
        "True Positive": [231, 76, 60, 160],
        "True Negative": [149, 165, 166, 80],
        "False Negative": [243, 156, 18, 160],
    }

    viz_df = filtered[
        ["h3_index", "outcome", "predicted_prob", "population",
         "level4_perc", "n_synergy", "n_anchors", "n_competitors"]
    ].copy()
    viz_df["color"] = viz_df["outcome"].map(color_map)
    viz_df["elevation"] = viz_df.apply(
        lambda r: r["predicted_prob"] * 500
        if r["outcome"] == "False Positive (Recommendation)" else 10,
        axis=1,
    )
    # Round for cleaner tooltips
    viz_df["predicted_prob"] = viz_df["predicted_prob"].round(3)
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

    view_state = pdk.ViewState(
        latitude=51.54, longitude=-0.14,
        zoom=12.5, pitch=pitch, bearing=-15,
    )

    tooltip = {
        "html": (
            "<b>H3:</b> {h3_index}<br>"
            "<b>Outcome:</b> {outcome}<br>"
            "<b>P(coffee):</b> {predicted_prob}<br>"
            "<b>Population:</b> {population}<br>"
            "<b>Level 4%:</b> {level4_perc}<br>"
            "<b>Synergy:</b> {n_synergy} | <b>Anchors:</b> {n_anchors} | <b>Competitors:</b> {n_competitors}"
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


# ═══════════════════════════════════════════════════════════════════════════
# TAB 3: SITE RECOMMENDATIONS
# ═══════════════════════════════════════════════════════════════════════════
with tab3:
    st.subheader("Top Recommended Sites (False Positives)")
    st.markdown(
        "These hexagons possess all the learned features of successful coffee shop locations "
        "— high footfall, educated demographics, strong transit connectivity — "
        "but **no coffee shop currently exists**. They represent Burt's Structural Holes."
    )

    # Recommendations table
    fp_display = fp_df.copy()
    fp_display.insert(0, "Rank", range(1, len(fp_display) + 1))
    fp_display = fp_display.rename(columns={
        "predicted_prob": "Confidence",
        "population": "Population",
        "level4_perc": "Level 4 %",
        "age_16_to_34_perc": "Age 16-34 %",
        "employed_total_perc": "Employed %",
        "n_synergy": "Synergy POIs",
        "n_anchors": "Anchors",
        "betweenness_centrality": "Betweenness",
        "closeness_centrality": "Closeness",
    })

    display_cols = [
        "Rank", "h3_index", "Confidence", "Population",
        "Level 4 %", "Synergy POIs", "Anchors", "Betweenness",
    ]
    available_cols = [c for c in display_cols if c in fp_display.columns]

    st.dataframe(
        fp_display[available_cols].style.format({
            "Confidence": "{:.3f}",
            "Population": "{:.0f}",
            "Level 4 %": "{:.1f}",
            "Betweenness": "{:.4f}",
        }),
        use_container_width=True,
        hide_index=True,
        height=400,
    )

    st.markdown("---")

    # Demographic comparison
    st.subheader("Demographic Profile: Recommendations vs Camden")

    profile_cols = [
        "population", "level4_perc", "age_16_to_34_perc",
        "employed_total_perc", "betweenness_centrality",
    ]
    profile_labels = [
        "Population", "Level 4 Qual %", "Age 16-34 %",
        "Employment %", "Betweenness Centrality",
    ]

    fp_grid = grid[grid["outcome"] == "False Positive (Recommendation)"]
    tp_grid = grid[grid["outcome"] == "True Positive"]

    comparison = pd.DataFrame({
        "Feature": profile_labels,
        "Camden Average": [grid[c].mean() for c in profile_cols],
        "Recommended Sites (FP)": [fp_grid[c].mean() for c in profile_cols] if len(fp_grid) > 0 else [0]*len(profile_cols),
        "Existing Shops (TP)": [tp_grid[c].mean() for c in profile_cols] if len(tp_grid) > 0 else [0]*len(profile_cols),
    })

    # Normalise each row to Camden Average for fair comparison
    comparison_norm = comparison.copy()
    for col in ["Camden Average", "Recommended Sites (FP)", "Existing Shops (TP)"]:
        comparison_norm[col] = comparison[col] / comparison["Camden Average"]

    fig_comp = go.Figure()
    colors = {"Camden Average": "#3498db", "Recommended Sites (FP)": "#27ae60", "Existing Shops (TP)": "#e74c3c"}
    for col_name, color in colors.items():
        fig_comp.add_trace(go.Bar(
            name=col_name,
            x=comparison_norm["Feature"],
            y=comparison_norm[col_name],
            marker_color=color,
        ))
    fig_comp.update_layout(
        barmode="group",
        title="Feature Comparison (Normalised to Camden Average = 1.0)",
        yaxis_title="Ratio to Camden Average",
        height=400,
        margin=dict(t=40, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig_comp.add_hline(y=1.0, line_dash="dash", line_color="grey", annotation_text="Camden Average")
    st.plotly_chart(fig_comp, use_container_width=True)

    # Radar chart for top 5 FP sites
    if len(fp_grid) >= 5:
        st.subheader("Feature Profile — Top 5 Recommended Sites")
        radar_cols = ["population", "level4_perc", "age_16_to_34_perc",
                      "n_synergy", "betweenness_centrality"]
        radar_labels = ["Population", "Level 4 %", "Age 16-34 %", "Synergy", "Betweenness"]

        top5 = fp_grid.nlargest(5, "predicted_prob")

        # Normalise to [0, 1] for radar
        radar_data = top5[radar_cols].copy()
        for col in radar_cols:
            col_min = grid[col].min()
            col_max = grid[col].max()
            radar_data[col] = (radar_data[col] - col_min) / (col_max - col_min + 1e-9)

        fig_radar = go.Figure()
        for i, (idx, row) in enumerate(radar_data.iterrows()):
            fig_radar.add_trace(go.Scatterpolar(
                r=[row[c] for c in radar_cols] + [row[radar_cols[0]]],
                theta=radar_labels + [radar_labels[0]],
                name=f"Site {i+1}",
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
        st.subheader("ROC Curves (Spatial CV)")
        roc_path = os.path.join(DATA_DIR, "roc_curves.png")
        if os.path.exists(roc_path):
            st.image(roc_path, use_container_width=True)
        else:
            st.info("Run the ML notebook to generate ROC curves.")

    with col_b:
        st.subheader("Feature Importance (XGBoost)")
        fi_path = os.path.join(DATA_DIR, "feature_importance.png")
        if os.path.exists(fi_path):
            st.image(fi_path, use_container_width=True)
        else:
            st.info("Run the ML notebook to generate the feature importance chart.")

    st.markdown("---")

    # Interactive correlation heatmap
    st.subheader("Feature Correlation Matrix")

    available_features = [c for c in FEATURE_COLS if c in grid.columns]
    corr_cols = available_features + ["has_coffee_shop"]
    corr_matrix = grid[corr_cols].corr()

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
    st.subheader("Feature Distribution by Target Class")
    selected_feature = st.selectbox(
        "Select a feature to explore:",
        options=available_features,
        index=available_features.index("population") if "population" in available_features else 0,
    )

    plot_data = grid[[selected_feature, "has_coffee_shop"]].copy()
    plot_data["has_coffee_shop"] = plot_data["has_coffee_shop"].map(
        {0: "No Coffee Shop", 1: "Has Coffee Shop"}
    )

    fig_box = px.box(
        plot_data,
        x="has_coffee_shop",
        y=selected_feature,
        color="has_coffee_shop",
        color_discrete_map={
            "No Coffee Shop": "#3498db",
            "Has Coffee Shop": "#e74c3c",
        },
        labels={"has_coffee_shop": ""},
    )
    fig_box.update_layout(height=400, showlegend=False, margin=dict(t=20, b=20))
    st.plotly_chart(fig_box, use_container_width=True)


# ── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<p style='text-align: center; color: #888; font-size: 0.85rem;'>"
    "Camden Specialty Coffee Site Selection | MSc Business Analytics 2026 | "
    "Built with Streamlit + Pydeck + Plotly"
    "</p>",
    unsafe_allow_html=True,
)
