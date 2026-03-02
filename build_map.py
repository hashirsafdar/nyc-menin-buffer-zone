# build_map.py — Folium interactive map assembly
#
# Performance approach:
#   - Buffer polygons: single batched GeoJson per layer (not per-row)
#   - Markers: single GeoJson with CircleMarker point_to_layer (not per-row)
#   - Buffer resolution reduced to 16 vertices per circle (config.BUFFER_RESOLUTION=4)
#   - No MarkerCluster — individual dots visible at all zoom levels

import json

import folium
from folium.plugins import MeasureControl
import geopandas as gpd

from config import (
    BUFFER_FILL_OPACITY,
    BUFFER_LINE_OPACITY,
    DEFAULT_ZOOM,
    EDUCATION_COLOR,
    MARKER_FILL_OPACITY,
    MARKER_RADIUS,
    NYC_CENTER,
    RELIGION_COLORS,
)


def _build_base_map() -> folium.Map:
    m = folium.Map(location=NYC_CENTER, zoom_start=DEFAULT_ZOOM, tiles=None)
    folium.TileLayer("CartoDB positron", name="Light (CartoDB Positron)").add_to(m)
    folium.TileLayer("OpenStreetMap", name="OpenStreetMap").add_to(m)
    folium.TileLayer("CartoDB dark_matter", name="Dark (CartoDB Dark Matter)").add_to(m)
    return m


def _gdf_to_geojson_dict(gdf: gpd.GeoDataFrame, cols: list) -> dict:
    available = [c for c in cols if c in gdf.columns]
    subset = gdf[available + ["geometry"]].copy()
    return json.loads(subset.to_json())


def _add_buffer_layer(buf_gdf, feature_group, default_color):
    geojson_data = _gdf_to_geojson_dict(buf_gdf, ["name", "color"])
    folium.GeoJson(
        geojson_data,
        style_function=lambda feature, dc=default_color: {
            "fillColor": feature["properties"].get("color") or dc,
            "color": feature["properties"].get("color") or dc,
            "weight": 1,
            "fillOpacity": BUFFER_FILL_OPACITY,
            "opacity": BUFFER_LINE_OPACITY,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["name"], aliases=["Location:"], localize=True, sticky=False,
        ),
    ).add_to(feature_group)


def _add_marker_layer(pts_gdf, feature_group, default_color, popup_fields, popup_aliases):
    """Add markers as a single batched GeoJson with CircleMarker rendering."""
    cols = ["name", "color"] + [f for f in popup_fields if f != "name"]
    geojson_data = _gdf_to_geojson_dict(pts_gdf, cols)

    folium.GeoJson(
        geojson_data,
        marker=folium.CircleMarker(radius=MARKER_RADIUS, fill=True),
        style_function=lambda feature, dc=default_color: {
            "radius": MARKER_RADIUS,
            "fillColor": feature["properties"].get("color") or dc,
            "color": feature["properties"].get("color") or dc,
            "weight": 1.5,
            "fillOpacity": MARKER_FILL_OPACITY,
        },
        tooltip=folium.GeoJsonTooltip(
            fields=["name"], aliases=[""], localize=True, sticky=False,
        ),
        popup=folium.GeoJsonPopup(
            fields=popup_fields,
            aliases=popup_aliases,
            localize=True,
            max_width=280,
        ),
    ).add_to(feature_group)


def _legend_html(worship_pts, edu_pts) -> str:
    items = ""
    for religion, color in RELIGION_COLORS.items():
        if "religion_normalized" in worship_pts.columns:
            count = int((worship_pts["religion_normalized"] == religion).sum())
        else:
            count = 0
        label = religion.replace("_", " ").title()
        items += (
            f'<div style="display:flex;align-items:center;margin:3px 0;">'
            f'<div style="width:13px;height:13px;border-radius:50%;background:{color};'
            f'margin-right:8px;flex-shrink:0;border:1px solid rgba(0,0,0,0.15);"></div>'
            f'<span style="font-size:12px;">{label}'
            f'<span style="color:#999;"> ({count:,})</span></span></div>'
        )
    items += (
        f'<div style="display:flex;align-items:center;margin:10px 0 3px 0;'
        f'padding-top:8px;border-top:1px solid #e0e0e0;">'
        f'<div style="width:13px;height:13px;border-radius:3px;background:{EDUCATION_COLOR};'
        f'margin-right:8px;flex-shrink:0;border:1px solid rgba(0,0,0,0.15);"></div>'
        f'<span style="font-size:12px;">Educational Facilities'
        f'<span style="color:#999;"> ({len(edu_pts):,})</span></span></div>'
    )
    return (
        '<div style="position:fixed;bottom:40px;left:10px;z-index:9999;'
        'background:rgba(255,255,255,0.96);padding:12px 16px;border-radius:8px;'
        'box-shadow:0 2px 10px rgba(0,0,0,0.25);font-family:Arial,sans-serif;max-width:230px;">'
        '<div style="font-weight:bold;font-size:13px;margin-bottom:8px;'
        'border-bottom:1px solid #e8e8e8;padding-bottom:5px;">Places of Worship</div>'
        f'{items}'
        '<div style="margin-top:10px;padding-top:8px;border-top:1px solid #e8e8e8;'
        'font-size:10px;color:#999;line-height:1.5;">'
        'Shaded areas = proposed 100ft no-protest perimeters<br>'
        "under NYC Council Speaker Menin's bill (Int. 0908/0909-A, 2026)"
        '</div></div>'
    )


def _stats_html(worship_pts, edu_pts) -> str:
    total = len(worship_pts) + len(edu_pts)
    return (
        '<div style="position:fixed;bottom:40px;right:10px;z-index:9999;'
        'background:rgba(255,255,255,0.96);padding:12px 16px;border-radius:8px;'
        'box-shadow:0 2px 10px rgba(0,0,0,0.25);font-family:Arial,sans-serif;min-width:210px;">'
        '<div style="font-weight:bold;font-size:13px;margin-bottom:8px;'
        'border-bottom:1px solid #e8e8e8;padding-bottom:5px;">'
        'Menin Bill — Buffer Zone Coverage</div>'
        '<div style="font-size:12px;line-height:2;">'
        f'Places of worship: <b>{len(worship_pts):,}</b><br>'
        f'Educational facilities: <b>{len(edu_pts):,}</b><br>'
        '<div style="border-top:1px solid #e8e8e8;margin-top:4px;padding-top:4px;">'
        f'Total covered locations: <b>{total:,}</b></div></div>'
        '<div style="margin-top:8px;font-size:10px;color:#999;line-height:1.5;">'
        'Each location has a 100ft (30.48m) perimeter.<br>'
        'Data: OpenStreetMap contributors.</div></div>'
    )


def build_map(worship_pts, worship_buf, edu_pts, edu_buf) -> folium.Map:
    m = _build_base_map()

    # Buffer layers (underneath markers)
    worship_buffer_fg = folium.FeatureGroup(
        name="&#x26EA; Places of Worship — Buffer Zones (100ft)", show=True
    )
    _add_buffer_layer(worship_buf, worship_buffer_fg, RELIGION_COLORS["unknown"])
    worship_buffer_fg.add_to(m)

    edu_buffer_fg = folium.FeatureGroup(
        name="&#x1F393; Educational Facilities — Buffer Zones (100ft)", show=True
    )
    _add_buffer_layer(edu_buf, edu_buffer_fg, EDUCATION_COLOR)
    edu_buffer_fg.add_to(m)

    # Marker layers (batched GeoJson, no clustering)
    worship_marker_fg = folium.FeatureGroup(
        name="&#x26EA; Places of Worship — Locations", show=False
    )
    _add_marker_layer(
        worship_pts, worship_marker_fg, RELIGION_COLORS["unknown"],
        popup_fields=["name", "religion_display", "denomination", "address"],
        popup_aliases=["Name", "Religion", "Denomination", "Address"],
    )
    worship_marker_fg.add_to(m)

    edu_marker_fg = folium.FeatureGroup(
        name="&#x1F393; Educational Facilities — Locations", show=False
    )
    _add_marker_layer(
        edu_pts, edu_marker_fg, EDUCATION_COLOR,
        popup_fields=["name", "amenity_type", "address"],
        popup_aliases=["Name", "Type", "Address"],
    )
    edu_marker_fg.add_to(m)

    folium.LayerControl(collapsed=False, position="topright").add_to(m)
    MeasureControl(
        primary_length_unit="feet",
        secondary_length_unit="miles",
        primary_area_unit="sqfeet",
        position="bottomright",
    ).add_to(m)

    m.get_root().html.add_child(folium.Element(_legend_html(worship_pts, edu_pts)))
    m.get_root().html.add_child(folium.Element(_stats_html(worship_pts, edu_pts)))

    return m
