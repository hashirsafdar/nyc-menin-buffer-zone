# fetch_data.py — Fetch OSM data for NYC religious and educational locations

import sys
from pathlib import Path

import geopandas as gpd
import osmnx as ox
import pandas as pd

from config import (
    CRS_DISPLAY,
    NYC_BOROUGHS,
    NYC_PLACE_NAME,
    OSM_EDUCATION_TAGS,
    OSM_WORSHIP_TAGS,
    OVERPASS_ENDPOINTS,
)

CACHE_DIR = Path("cache")


def _configure_osmnx():
    ox.settings.log_console = False
    ox.settings.use_cache = True
    ox.settings.cache_folder = str(CACHE_DIR / "osmnx_cache")
    try:
        ox.settings.requests_timeout = 300
        ox.settings.overpass_url = OVERPASS_ENDPOINTS[0]
    except AttributeError:
        ox.settings.timeout = 300
        ox.settings.overpass_endpoint = OVERPASS_ENDPOINTS[0]
    ox.settings.max_query_area_size = 50_000_000_000


def _fetch_place(place_name: str, tags: dict) -> gpd.GeoDataFrame:
    gdf = ox.features_from_place(place_name, tags=tags)
    gdf = gdf.reset_index()
    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs(CRS_DISPLAY)
    return gdf


def _fetch_by_borough(tags: dict, label: str) -> gpd.GeoDataFrame:
    gdfs = []
    for borough in NYC_BOROUGHS:
        borough_short = borough.split(",")[0].lower().replace(" ", "_")
        borough_cache = CACHE_DIR / f"{label}_{borough_short}.geojson"

        if borough_cache.exists():
            print(f"  [cache] {borough_short}")
            gdfs.append(gpd.read_file(borough_cache))
            continue

        print(f"  [fetch] {borough_short}...", end=" ", flush=True)
        try:
            gdf = _fetch_place(borough, tags)
            gdf.to_file(borough_cache, driver="GeoJSON")
            print(f"{len(gdf)} features")
            gdfs.append(gdf)
        except Exception as e:
            print(f"FAILED: {e}", file=sys.stderr)

    if not gdfs:
        raise RuntimeError("All borough fetches failed.")

    combined = pd.concat(gdfs, ignore_index=True)
    id_cols = [c for c in ["osmid", "element_type"] if c in combined.columns]
    if id_cols:
        combined = combined.drop_duplicates(subset=id_cols)
    return combined.reset_index(drop=True)


def fetch_features(tags: dict, label: str) -> gpd.GeoDataFrame:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_path = CACHE_DIR / f"{label}_raw.geojson"

    if cache_path.exists():
        print(f"[cache] Loading {label} from {cache_path}")
        return gpd.read_file(cache_path)

    print(f"[fetch] Querying OSM for {label} in NYC...")
    _configure_osmnx()

    try:
        gdf = _fetch_place(NYC_PLACE_NAME, tags)
        print(f"  Found {len(gdf)} {label} features")
    except Exception as e:
        print(f"  Full NYC query failed ({e}), trying borough-by-borough...",
              file=sys.stderr)
        gdf = _fetch_by_borough(tags, label)
        print(f"  Total after merging boroughs: {len(gdf)} {label} features")

    gdf.to_file(cache_path, driver="GeoJSON")
    print(f"  Cached to {cache_path}")
    return gdf


def fetch_all() -> tuple:
    worship = fetch_features(OSM_WORSHIP_TAGS, "worship")
    education = fetch_features(OSM_EDUCATION_TAGS, "education")
    return worship, education
