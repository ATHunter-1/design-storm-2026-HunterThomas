# Strontia Springs brief: source data

Everything the brief (`../design-storm-strontia-springs-brief.html`) draws or cites, saved locally so
the maps and figures can be rebuilt without re-deriving anything.

## Viewing the brief

The locator map loads the GeoJSON below with `fetch()`, which browsers block on `file://` URLs, so the
page needs to be served:

```
python3 eddd/data/serve.py
open http://localhost:8765/design-storm-strontia-springs-brief
```

Opened directly off disk, everything else still renders; only the interactive map is replaced with a note
saying how to serve it. Map tiles come from OpenStreetMap, so that part needs a network connection.

## What is here

| Path | What it is |
|------|-----------|
| `places.json` | Every coordinate in the brief, with the USGS station it came from and the DMS string it was converted from. The one non-USGS entry (Denver) is marked as such. |
| `basins/` | Drainage basin polygons and river lines from the USGS Network Linked Data Index, as returned. |
| `series/` | The 15-minute readings behind the storm chart: turbidity and conductance at 06707525, discharge at 06701900, 14&ndash;15 Aug 2026. |
| `vendor/` | Leaflet 1.9.4, vendored so the map works without a CDN. |
| `map.js` | The interactive locator map. Reads `places.json` and `basins/` directly, so those stay the single source of truth. |
| `build_maps.py` | Regenerates the static SVG fragments in `svg/` (currently just the blind-spot map). |
| `svg/` | Generated. Do not edit by hand. |

## Refetching from USGS

Nothing here changes unless the underlying record does, so this is rarely needed. The endpoints are
recorded in `places.json` under `_sources`. Basin polygons:

```
curl "https://api.water.usgs.gov/nldi/linked-data/nwissite/USGS-06707525/basin" -o basins/south-platte-above-strontia-06707525.json
```

Station metadata, which is where the coordinates and published drainage areas come from:

```
curl "https://waterservices.usgs.gov/nwis/site/?format=rdb&sites=06707525&siteOutput=expanded"
```

Note that `waterservices.usgs.gov` is scheduled for decommissioning in early 2027; the successor is the
OGC API at `api.waterdata.usgs.gov`.

## Rebuilding the static figures

```
python3 build_maps.py
```

It prints a check as it goes: the computed basin above Trumbull should come out at 2,029 sq mi against
the 2,028 USGS publishes. That agreement is what makes the other computed areas trustworthy, including
the 555 sq mi ungaged difference the brief leans on. If that check drifts, something upstream changed.

Then paste the fragment from `svg/blind-spot.svg` into the matching `<svg>` element in the brief,
matched on its `aria-label`.

## A caution

The published artifact version of this brief cannot load Leaflet or map tiles, because artifacts block
all external hosts. That copy carries static SVG maps instead and will drift from this one.
