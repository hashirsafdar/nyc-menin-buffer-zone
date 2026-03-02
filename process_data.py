# process_data.py — Spatial processing: geometry normalization, CRS projection, buffering
#
# CRS rationale:
#   EPSG:2263 = NY State Plane Long Island Zone
#   Native unit: US Survey Feet — buffer(100) = exactly 100 US Survey feet (~30.48m)
#   Never use EPSG:3857 (Web Mercator) for distance calculations.

import pandas as pd
import geopandas as gpd

from config import (
    BUFFER_RESOLUTION,
    CRS_BUFFER_UNIT,
    CRS_DISPLAY,
    CRS_PROJECTED,
    EDUCATION_COLOR,
    RELIGION_COLORS,
)

_RELIGION_ALIASES = {
    "catholic": "christian",
    "protestant": "christian",
    "orthodox": "christian",
    "evangelical": "christian",
    "baptist": "christian",
    "lutheran": "christian",
    "methodist": "christian",
    "presbyterian": "christian",
    "pentecostal": "christian",
    "reformed": "christian",
    "roman_catholic": "christian",
    "sunni": "muslim",
    "shia": "muslim",
    "ahmadiyya": "muslim",
    "reform jewish": "jewish",
    "conservative jewish": "jewish",
    "orthodox jewish": "jewish",
    "reconstructionist": "jewish",
}


def standardize_geometry(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf.copy()
    gdf["footprint"] = gdf["geometry"].apply(
        lambda g: g if g is not None and g.geom_type in ("Polygon", "MultiPolygon")
        else None
    )
    gdf["geometry"] = gdf["geometry"].apply(
        lambda g: g.centroid if g is not None and g.geom_type != "Point" else g
    )
    gdf = gdf.set_geometry("geometry")
    gdf = gdf[gdf["geometry"].notna() & gdf["geometry"].is_valid]
    return gdf.reset_index(drop=True)


def _normalize_religion(row) -> str:
    raw = str(row.get("religion", "")).strip().lower()
    if not raw or raw == "nan":
        return "unknown"
    if raw in RELIGION_COLORS:
        return raw
    for alias, canonical in _RELIGION_ALIASES.items():
        if alias in raw:
            return canonical
    return "other"


def _format_address(row) -> str:
    parts = []
    for tag in ["addr:housenumber", "addr:street", "addr:city", "addr:postcode"]:
        val = row.get(tag, "")
        if isinstance(val, str) and val.strip() and val.strip() != "nan":
            parts.append(val.strip())
    return ", ".join(parts) if parts else ""


def clean_worship_data(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf.copy()
    gdf["religion_normalized"] = gdf.apply(_normalize_religion, axis=1)
    gdf["color"] = gdf["religion_normalized"].map(RELIGION_COLORS)
    gdf["name"] = (
        gdf["name"].astype(str)
        .replace("nan", "Unnamed Place of Worship")
        .fillna("Unnamed Place of Worship")
    )
    gdf["religion_display"] = (
        gdf["religion"].astype(str)
        .str.replace("_", " ").str.title()
        .replace("Nan", "Unknown")
    )
    gdf["denomination"] = (
        gdf.get("denomination", pd.Series(dtype=str))
        .astype(str).replace("nan", "").str.replace("_", " ").str.title()
        .fillna("")
    )
    gdf["address"] = gdf.apply(_format_address, axis=1)
    return gdf


def clean_education_data(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf = gdf.copy()
    gdf["name"] = (
        gdf["name"].astype(str)
        .replace("nan", "Unnamed Educational Facility")
        .fillna("Unnamed Educational Facility")
    )
    gdf["amenity_type"] = (
        gdf.get("amenity", pd.Series(dtype=str))
        .astype(str).replace("nan", "school").str.replace("_", " ").str.title()
        .fillna("School")
    )
    gdf["color"] = EDUCATION_COLOR
    gdf["address"] = gdf.apply(_format_address, axis=1)
    return gdf


def create_buffers(gdf: gpd.GeoDataFrame) -> gpd.GeoDataFrame:
    gdf_proj = gdf.to_crs(CRS_PROJECTED)
    # resolution=4 → 16 vertices per circle (vs default 64), ~4x smaller output
    buffer_geoms = gdf_proj["geometry"].buffer(CRS_BUFFER_UNIT, resolution=BUFFER_RESOLUTION)
    keep_cols = {c: gdf_proj[c] for c in ["name", "color"] if c in gdf_proj.columns}
    buf_gdf = gpd.GeoDataFrame(keep_cols, geometry=buffer_geoms, crs=CRS_PROJECTED)
    return buf_gdf.to_crs(CRS_DISPLAY)


def process_all(worship_raw: gpd.GeoDataFrame, education_raw: gpd.GeoDataFrame):
    print("[process] Standardizing worship geometry...")
    worship_pts = standardize_geometry(worship_raw)
    worship_pts = clean_worship_data(worship_pts)
    print(f"  {len(worship_pts)} worship locations retained")

    print("[process] Creating worship buffers (100ft)...")
    worship_buf = create_buffers(worship_pts)

    print("[process] Standardizing education geometry...")
    edu_pts = standardize_geometry(education_raw)
    edu_pts = clean_education_data(edu_pts)
    print(f"  {len(edu_pts)} education locations retained")

    print("[process] Creating education buffers (100ft)...")
    edu_buf = create_buffers(edu_pts)

    return worship_pts, worship_buf, edu_pts, edu_buf
