#!/usr/bin/env python3
"""Regenerate the SVG map fragments for the Strontia Springs brief.

Reads places.json and basins/*.json (both committed), writes svg/*.svg fragments.
Nothing here touches the network; run fetch.sh first if the source data needs refreshing.

    python3 build_maps.py

Then splice the fragments into design-storm-strontia-springs-brief.html, replacing
the contents of the matching <svg> element (matched on its aria-label).
"""

import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))
BASINS = os.path.join(HERE, "basins")
OUT = os.path.join(HERE, "svg")

EARTH_RADIUS_KM = 6371.0088
KM_PER_DEGREE_LAT = 111.32
SQ_KM_PER_SQ_MI = 2.58999


def load_places():
    with open(os.path.join(HERE, "places.json")) as f:
        return json.load(f)


def ring(filename):
    with open(os.path.join(BASINS, filename)) as f:
        geometry = json.load(f)["features"][0]["geometry"]
    if geometry["type"] == "Polygon":
        return geometry["coordinates"][0]
    return geometry["coordinates"][0][0]


def linestrings(filename):
    with open(os.path.join(BASINS, filename)) as f:
        return [feature["geometry"]["coordinates"] for feature in json.load(f)["features"]]


def area_sq_mi(points):
    total = 0.0
    for i in range(len(points)):
        lon1, lat1 = points[i]
        lon2, lat2 = points[(i + 1) % len(points)]
        total += math.radians(lon2 - lon1) * (
            2 + math.sin(math.radians(lat1)) + math.sin(math.radians(lat2))
        )
    return abs(total * EARTH_RADIUS_KM * EARTH_RADIUS_KM / 2) / SQ_KM_PER_SQ_MI


def distance_km(a, b):
    scale = math.cos(math.radians((a[1] + b[1]) / 2))
    return math.hypot((b[0] - a[0]) * scale, b[1] - a[1]) * KM_PER_DEGREE_LAT


def simplify(points, tolerance):
    """Douglas-Peucker, on already-projected pixel coordinates."""
    if len(points) < 3 or tolerance <= 0:
        return points

    def perpendicular_distance(point, start, end):
        (x, y), (x1, y1), (x2, y2) = point, start, end
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            return math.hypot(x - x1, y - y1)
        t = max(0, min(1, ((x - x1) * dx + (y - y1) * dy) / (dx * dx + dy * dy)))
        return math.hypot(x - (x1 + t * dx), y - (y1 + t * dy))

    worst, index = 0.0, 0
    for i in range(1, len(points) - 1):
        d = perpendicular_distance(points[i], points[0], points[-1])
        if d > worst:
            worst, index = d, i
    if worst > tolerance:
        return simplify(points[: index + 1], tolerance)[:-1] + simplify(points[index:], tolerance)
    return [points[0], points[-1]]


class Projection:
    """Equirectangular with a cosine correction, good enough at one-state scale."""

    def __init__(self, bbox, width, height, pad, left_align=False):
        self.west, self.south, self.east, self.north = bbox
        self.scale_x = math.cos(math.radians((self.south + self.north) / 2))
        span_x = (self.east - self.west) * self.scale_x
        span_y = self.north - self.south
        self.scale = min((width - 2 * pad) / span_x, (height - 2 * pad) / span_y)
        self.offset_x = pad if left_align else pad + ((width - 2 * pad) - span_x * self.scale) / 2
        self.offset_y = pad + ((height - 2 * pad) - span_y * self.scale) / 2

    def __call__(self, lon, lat):
        return (
            self.offset_x + (lon - self.west) * self.scale_x * self.scale,
            self.offset_y + (self.north - lat) * self.scale,
        )

    def pixels_per_km(self):
        return self.scale / KM_PER_DEGREE_LAT


def path_data(coords, project, tolerance=0.0, close=True):
    points = [project(lon, lat) for lon, lat in coords]
    if tolerance:
        points = simplify(points, tolerance)
    d = "M" + " L".join("%.1f %.1f" % (x, y) for x, y in points)
    return d + (" Z" if close else "")


def bounds(*coord_lists):
    xs = [c[0] for coords in coord_lists for c in coords]
    ys = [c[1] for coords in coord_lists for c in coords]
    return (min(xs), min(ys), max(xs), max(ys))


def projected_bounds(coords, project):
    points = [project(lon, lat) for lon, lat in coords]
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return (min(xs), min(ys), max(xs), max(ys))


def eastern_arc(coords):
    """The east-facing half of a basin ring, walked north to south.

    For a west-slope basin this arc is the Continental Divide: the line where
    water stops draining to the Colorado River and starts draining east.
    """
    north_index = max(range(len(coords)), key=lambda i: coords[i][1])
    south_index = min(range(len(coords)), key=lambda i: coords[i][1])
    forward = (
        coords[north_index:south_index + 1]
        if north_index <= south_index
        else coords[north_index:] + coords[: south_index + 1]
    )
    backward = (
        coords[south_index:north_index + 1][::-1]
        if south_index <= north_index
        else (coords[south_index:] + coords[: north_index + 1])[::-1]
    )
    mean_lon = lambda arc: sum(c[0] for c in arc) / len(arc)
    return forward if mean_lon(forward) > mean_lon(backward) else backward


def scale_bar(project, x, y, km=40):
    width = km * project.pixels_per_km()
    return (
        '<g transform="translate(%.0f,%.0f)">'
        '<line x1="0" y1="0" x2="%.1f" y2="0" class="axisline"/>'
        '<line x1="0" y1="-4" x2="0" y2="4" class="axisline"/>'
        '<line x1="%.1f" y1="-4" x2="%.1f" y2="4" class="axisline"/>'
        '<text class="axis-txt" x="%.1f" y="-8" text-anchor="middle">%d km</text></g>'
        % (x, y, width, width, width, width / 2, km)
    )


def dot(x, y, fill, r=5):
    return (
        '<circle cx="%.1f" cy="%.1f" r="%s" fill="%s" stroke="var(--surface)" stroke-width="2"/>'
        % (x, y, r, fill)
    )


def label(x, y, text, cls="maplab", dx=9, dy=4, anchor="start"):
    return '<text class="%s" x="%.1f" y="%.1f" text-anchor="%s">%s</text>' % (
        cls,
        x + dx,
        y + dy,
        anchor,
        text,
    )


# --------------------------------------------------------------------------
# Map 1: the locator. Where all of this is, relative to Denver.
# --------------------------------------------------------------------------

COLORADO = (-109.0448, 36.9931, -102.0416, 41.0034)  # nominal state boundary


def build_locator(places):
    south_platte = ring("south-platte-above-strontia-06707525.json")
    blue = ring("blue-river-below-dillon-09050700.json")
    fraser = ring("fraser-below-moffat-09023562.json")
    williams_fork = ring("williams-fork-parshall-09037500.json")

    gages = places["gages"]
    reservoirs = places["reservoirs"]
    denver = (places["places"]["denver"]["lon"], places["places"]["denver"]["lat"])

    def coord(entry):
        return (entry["lon"], entry["lat"])

    frame = bounds(south_platte, blue, fraser, williams_fork, [denver])
    frame = (frame[0] - 0.10, frame[1] - 0.10, frame[2] + 0.12, frame[3] + 0.10)
    project = Projection(frame, 760, 560, 20, left_align=True)

    parts = []

    # basins, west-slope first so the big east-slope one draws over nothing
    for coords, fill, stroke, tolerance in (
        (blue, "var(--teal-wash)", "var(--teal)", 0.5),
        (fraser, "var(--teal-wash)", "var(--teal)", 0.4),
        (williams_fork, "var(--teal-wash)", "var(--teal)", 0.5),
        (south_platte, "var(--silt-wash)", "var(--silt)", 0.7),
    ):
        parts.append(
            '<path d="%s" fill="%s" stroke="%s" stroke-width="1.5" stroke-linejoin="round"/>'
            % (path_data(coords, project, tolerance), fill, stroke)
        )

    # The Continental Divide, drawn as the real thing rather than a straight line:
    # the eastern boundary of the Blue River basin IS the divide along this stretch,
    # because everything east of it drains to the Atlantic instead of the Pacific.
    for basin in (williams_fork, fraser, blue):
        parts.append(
            '<path d="%s" fill="none" stroke="var(--ink)" stroke-width="2.6" opacity="0.6" '
            'stroke-dasharray="9 6" stroke-linecap="round"/>'
            % path_data(eastern_arc(basin), project, 0.6, close=False)
        )
    fraser_arc = eastern_arc(fraser)
    anchor_point = project(*fraser_arc[len(fraser_arc) // 2])
    parts.append(
        '<text class="maplab" x="%.0f" y="%.0f">Continental Divide</text>'
        % (anchor_point[0] + 26, anchor_point[1] + 4)
    )
    parts.append(
        '<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" class="axisline"/>'
        % (anchor_point[0] + 21, anchor_point[1], anchor_point[0] + 4, anchor_point[1])
    )

    # Roberts Tunnel, drawn between two verified endpoints
    dillon = project(*coord(reservoirs["dillon"]))
    grant = project(*coord(gages["north_fork_at_grant"]))
    parts.append(
        '<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="var(--teal)" '
        'stroke-width="2.4" stroke-dasharray="7 4"/>' % (dillon[0], dillon[1], grant[0], grant[1])
    )
    parts.append(
        '<text class="maplab-soft" x="%.0f" y="%.0f">Roberts Tunnel &#183; 23 mi</text>'
        % (dillon[0] + 16, dillon[1] + 19)
    )

    # points, in draw order
    for key, entry, kind, dx, dy, anchor in (
        ("Dillon Reservoir", reservoirs["dillon"], "teal", -9, -6, "end"),
        ("Williams Fork Res.", reservoirs["williams_fork_reservoir"], "teal", 9, -4, "start"),
        ("Fraser", gages["fraser_below_moffat"], "teal", 9, 4, "start"),
        ("Grant", gages["north_fork_at_grant"], "muted", 9, -6, "start"),
        ("Antero", reservoirs["antero"], "muted", 9, 4, "start"),
        ("Eleven Mile", reservoirs["eleven_mile"], "muted", 9, 4, "start"),
        ("Cheesman", reservoirs["cheesman"], "muted", 9, 4, "start"),
        ("Chatfield", reservoirs["chatfield"], "muted", -9, 4, "end"),
        ("Marston", reservoirs["marston"], "muted", 9, 4, "start"),
    ):
        x, y = project(*coord(entry))
        fill = "var(--teal)" if kind == "teal" else "var(--muted)"
        parts.append(dot(x, y, fill, 4))
        parts.append(label(x, y, key, "maplab-soft", dx, dy, anchor))

    # the gage, emphasised
    gx, gy = project(*coord(gages["turbidity"]))
    parts.append(dot(gx, gy, "var(--silt)", 6.5))
    parts.append(label(gx, gy, "Strontia Springs", "maplab", 11, -3))
    parts.append(label(gx, gy, "gage 06707525", "maplab-soft", 11, 11))

    # Denver, the anchor everyone knows
    dx_, dy_ = project(*denver)
    parts.append('<rect x="%.1f" y="%.1f" width="10" height="10" fill="var(--ink)"/>' % (dx_ - 5, dy_ - 5))
    parts.append(label(dx_, dy_, "DENVER", "maplab-city", 13, 4))

    km = distance_km(coord(gages["turbidity"]), denver)
    parts.append(
        '<text class="maplab-soft" x="%.0f" y="%.0f">%.0f mi (%.0f km) from the gage</text>'
        % (dx_ + 13, dy_ + 20, km / 1.609, km)
    )

    parts.append(scale_bar(project, 560, 536))

    # Colorado locator inset, top right
    inset = Projection(COLORADO, 150, 108, 4)
    ix, iy = 596, 26
    x0, y0 = inset(COLORADO[0], COLORADO[3])
    x1, y1 = inset(COLORADO[2], COLORADO[1])
    parts.append(
        '<g transform="translate(%d,%d)"><rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" '
        'fill="none" stroke="var(--muted)" stroke-width="1.2"/>' % (ix, iy, x0, y0, x1 - x0, y1 - y0)
    )
    bx0, by0 = inset(frame[0], frame[3])
    bx1, by1 = inset(frame[2], frame[1])
    parts.append(
        '<rect x="%.1f" y="%.1f" width="%.1f" height="%.1f" fill="var(--silt-wash)" '
        'stroke="var(--silt)" stroke-width="1.2"/>' % (bx0, by0, bx1 - bx0, by1 - by0)
    )
    parts.append(
        '<text class="maplab-soft" x="%.1f" y="%.1f" text-anchor="middle">COLORADO</text></g>'
        % ((x0 + x1) / 2, y1 + 13)
    )

    return "\n        ".join(parts)


# --------------------------------------------------------------------------
# Map 2: the blind spot. What the flow gage measures versus what reaches the reservoir.
# --------------------------------------------------------------------------


def build_blind_spot(places):
    full = ring("south-platte-above-strontia-06707525.json")
    upper = ring("south-platte-above-trumbull-06701900.json")
    rivers = linestrings("mainstem-flowlines-06707525.json")
    gages = places["gages"]

    frame = bounds(full)
    frame = (frame[0] - 0.05, frame[1] - 0.05, frame[2] + 0.05, frame[3] + 0.05)
    project = Projection(frame, 760, 470, 18, left_align=True)

    parts = [
        '<path d="%s" fill="var(--silt-wash)" stroke="var(--silt)" stroke-width="1.6" '
        'stroke-linejoin="round"/>' % path_data(full, project, 0.5),
        '<path d="%s" fill="var(--sunken)" stroke="var(--muted)" stroke-width="1.2" '
        'stroke-dasharray="4 3" stroke-linejoin="round"/>' % path_data(upper, project, 0.5),
    ]
    for line in rivers:
        d = path_data(line, project, 0.6, close=False)
        if len(d) > 28:
            parts.append(
                '<path d="%s" fill="none" stroke="var(--teal)" stroke-width="1.1" '
                'stroke-linecap="round" opacity="0.85"/>' % d
            )

    flow_x, flow_y = project(gages["flow"]["lon"], gages["flow"]["lat"])
    turb_x, turb_y = project(gages["turbidity"]["lon"], gages["turbidity"]["lat"])
    parts.append(dot(flow_x, flow_y, "var(--muted)", 6))
    parts.append(label(flow_x, flow_y, "Flow gage 06701900", "maplab", 11))
    parts.append(label(flow_x, flow_y, "saw nothing", "maplab-soft", 11, 21))
    parts.append(dot(turb_x, turb_y, "var(--silt)", 6))
    parts.append(label(turb_x, turb_y, "Turbidity gage 06707525", "maplab", 11))
    parts.append(label(turb_x, turb_y, "303 FNU", "maplab-soft", 11, 21))

    gap = area_sq_mi(full) - area_sq_mi(upper)
    full_bounds = projected_bounds(full, project)
    upper_bounds = projected_bounds(upper, project)
    hx = full_bounds[2] + 58
    hy = full_bounds[1] + 18
    band_x = (full_bounds[0] + full_bounds[2]) / 2 * 0.62 + full_bounds[0] * 0.38
    band_y = (full_bounds[1] + upper_bounds[1]) / 2
    parts.append('<text class="maplab-hero" x="%.0f" y="%.0f">~%d sq mi</text>' % (hx, hy, round(gap / 5) * 5))
    parts.append('<text class="maplab-soft" x="%.0f" y="%.0f">ungaged for flow</text>' % (hx, hy + 17))
    parts.append(
        '<line x1="%.0f" y1="%.0f" x2="%.0f" y2="%.0f" class="axisline"/>'
        % (hx - 8, hy - 5, band_x, band_y)
    )
    parts.append(scale_bar(project, 600, 438))

    return "\n          ".join(parts)


def main():
    os.makedirs(OUT, exist_ok=True)
    places = load_places()

    fragments = {
        "locator.svg": build_locator(places),
        "blind-spot.svg": build_blind_spot(places),
    }
    for name, fragment in fragments.items():
        with open(os.path.join(OUT, name), "w") as f:
            f.write(fragment)
        print("wrote svg/%s (%d chars)" % (name, len(fragment)))

    full = ring("south-platte-above-strontia-06707525.json")
    upper = ring("south-platte-above-trumbull-06701900.json")
    print("\nchecks")
    print("  basin above Strontia   %6.0f sq mi" % area_sq_mi(full))
    print("  basin above Trumbull   %6.0f sq mi  (USGS publishes 2028)" % area_sq_mi(upper))
    print("  ungaged difference     %6.0f sq mi" % (area_sq_mi(full) - area_sq_mi(upper)))


if __name__ == "__main__":
    main()
