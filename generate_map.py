#!/usr/bin/env python3
# generate_map.py — Entry point for NYC Menin proposal buffer zone map
#
# Usage:
#   python generate_map.py                         # Use cached OSM data
#   python generate_map.py --no-cache              # Force re-fetch from Overpass API
#   python generate_map.py --output ~/my_map.html  # Custom output path

import argparse
import shutil
import sys
import time
from pathlib import Path

_REQUIRED = ["osmnx", "geopandas", "folium", "shapely", "pyproj", "branca"]
import importlib.util
_missing = [p for p in _REQUIRED if not importlib.util.find_spec(p)]
if _missing:
    print(
        f"ERROR: Missing packages: {', '.join(_missing)}\n"
        f"Install with: pip install {' '.join(_missing)}",
        file=sys.stderr,
    )
    sys.exit(1)

from fetch_data import fetch_all
from process_data import process_all
from build_map import build_map

CACHE_DIR = Path("cache")
OUTPUT_DIR = Path("output")
DEFAULT_OUTPUT = OUTPUT_DIR / "nyc_buffer_zones.html"


def parse_args():
    p = argparse.ArgumentParser(description="Generate NYC Menin proposal 100ft buffer zone map")
    p.add_argument("--no-cache", action="store_true", help="Force re-fetch from Overpass API")
    p.add_argument("--output", default=str(DEFAULT_OUTPUT), help=f"Output HTML path (default: {DEFAULT_OUTPUT})")
    return p.parse_args()


def main():
    args = parse_args()
    output_path = Path(args.output)

    print("=" * 60)
    print("NYC Menin Protest Buffer Zone Map Generator")
    print("Proposal: 100ft no-protest zones around houses of")
    print("worship and educational facilities (Int. 0908/0909-A)")
    print("=" * 60)
    print()

    if args.no_cache and CACHE_DIR.exists():
        shutil.rmtree(CACHE_DIR)
        print("[cache] Cleared cached OSM data.\n")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    t0 = time.time()
    print("[1/4] Fetching OSM data for NYC...")
    print("      (First run queries Overpass API — may take 1-5 minutes)")
    worship_raw, education_raw = fetch_all()
    print(f"      Worship: {len(worship_raw):,}  |  Education: {len(education_raw):,}")
    print(f"      Fetch done in {time.time() - t0:.1f}s\n")

    t1 = time.time()
    print("[2/4] Processing geometries and computing 100ft buffers...")
    worship_pts, worship_buf, edu_pts, edu_buf = process_all(worship_raw, education_raw)
    print(f"      Done in {time.time() - t1:.1f}s\n")

    t2 = time.time()
    print("[3/4] Building interactive map...")
    m = build_map(worship_pts, worship_buf, edu_pts, edu_buf)
    print(f"      Done in {time.time() - t2:.1f}s\n")

    t3 = time.time()
    print(f"[4/4] Saving to {output_path}...")
    m.save(str(output_path))
    size_mb = output_path.stat().st_size / 1_000_000
    print(f"      Saved in {time.time() - t3:.1f}s  ({size_mb:.1f} MB)\n")

    print("=" * 60)
    print(f"Done in {time.time() - t0:.1f}s total")
    print(f"\nOpen: file://{output_path.resolve()}")
    print(f"\n  {len(worship_pts):,} places of worship with 100ft buffer zones")
    print(f"  {len(edu_pts):,} educational facilities with 100ft buffer zones")
    print("  Toggle layers via layer control (top-right)")
    print("  Measure tool (bottom-right) to verify 100ft radius")
    print("=" * 60)


if __name__ == "__main__":
    main()
