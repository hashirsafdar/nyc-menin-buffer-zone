# config.py — Shared constants for NYC buffer zone map

NYC_PLACE_NAME = "New York City, New York, USA"

# Buffer distance
BUFFER_FEET = 100
# EPSG:2263 (NY State Plane Long Island) uses US Survey Feet as its native unit,
# so buffer(100) in that CRS = exactly 100 US Survey feet (~30.48m)
CRS_PROJECTED = "EPSG:2263"
CRS_BUFFER_UNIT = 100       # feet — matches EPSG:2263 native unit
CRS_DISPLAY = "EPSG:4326"   # WGS84 for Folium/Leaflet display

# OSM tags to query
OSM_WORSHIP_TAGS = {"amenity": "place_of_worship"}
OSM_EDUCATION_TAGS = {
    "amenity": ["school", "college", "university", "kindergarten"]
}

# NYC borough names for fallback borough-by-borough queries
NYC_BOROUGHS = [
    "Manhattan, New York City, New York, USA",
    "Brooklyn, New York City, New York, USA",
    "Queens, New York City, New York, USA",
    "Bronx, New York City, New York, USA",
    "Staten Island, New York City, New York, USA",
]

# Religion → marker/buffer color mapping (OSM religion= field values)
RELIGION_COLORS = {
    "christian":  "#4A90D9",
    "jewish":     "#F5A623",
    "muslim":     "#27AE60",
    "hindu":      "#FF6B35",
    "buddhist":   "#9B59B6",
    "sikh":       "#E67E22",
    "other":      "#95A5A6",
    "unknown":    "#BDC3C7",
}

EDUCATION_COLOR = "#E74C3C"

# Map display settings
BUFFER_FILL_OPACITY = 0.35
BUFFER_LINE_OPACITY = 0.0
MARKER_RADIUS = 2
MARKER_FILL_OPACITY = 0.85
BUFFER_RESOLUTION = 4  # segments per quarter-circle (16 total vs default 64)

# Overpass API endpoints (tried in order on failure)
OVERPASS_ENDPOINTS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.ru/api/interpreter",
]

# Map display
NYC_CENTER = [40.7128, -74.0060]
DEFAULT_ZOOM = 11
