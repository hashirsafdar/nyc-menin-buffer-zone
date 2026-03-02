# NYC Menin Protest Buffer Zone Map

Interactive map visualizing what NYC Council Speaker Julie Menin's original bill (Int. 0908/0909-A, 2026) would have looked like — a mandatory **100ft no-protest perimeter** around every house of worship and educational facility in New York City.

The bill was amended in February 2026 to remove the fixed perimeter in favor of a flexible NYPD-determined response plan. This map shows the scope of the original proposal.

**[View the map](https://hashirsafdar.github.io/nyc-menin-buffer-zone/)**

## What's mapped

- **2,826 places of worship** — churches, mosques, temples, synagogues, and all other `amenity=place_of_worship` in OpenStreetMap, color-coded by religion
- **2,200 educational facilities** — schools, colleges, universities, and kindergartens
- Each location has a 100ft (30.48m) buffer zone drawn around it

## Data source

OpenStreetMap via the [Overpass API](https://overpass-api.de/). First run fetches live data and caches it locally.

## Run it yourself

Requires [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/hashirsafdar/nyc-menin-buffer-zone
cd nyc-menin-buffer-zone
uv sync
uv run python generate_map.py
open output/nyc_buffer_zones.html
```

Use `--no-cache` to re-fetch fresh data from Overpass API:

```bash
uv run python generate_map.py --no-cache
```

## How the buffers are computed

Buffers are calculated in **EPSG:2263** (NY State Plane Long Island), whose native unit is US Survey Feet. `buffer(100)` in that CRS = exactly 100 feet with less than 0.1% distortion across NYC. Results are reprojected to WGS84 for display.

## Background

- [Gothamist: NYC bill restricting protests outside religious institutions](https://gothamist.com/news/nyc-bill-restricting-protests-outside-religious-and-educational-institutions-gains-steam)
- [amNY: Council softens protest buffer zone bills](https://www.amny.com/news/council-protest-buffer-zone-bills/)
- [City & State: Menin gets mixed feedback on protest barrier bill](https://www.cityandstateny.com/politics/2026/02/hearing-menin-gets-mixed-feedback-her-protest-barrier-bill/411699/)
