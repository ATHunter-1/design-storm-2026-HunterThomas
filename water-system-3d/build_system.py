#!/usr/bin/env python3
"""Build system.json, the point-and-line data behind the 3D water system map.

Reads ../strontia-brief/places.json (USGS-verified coordinates) and
snotel-co-stations.json (NRCS AWDB station metadata, pulled 2026-08-31 from
https://wcc.sc.egov.usda.gov/awdbRestApi/services/v1/stations?stationTriplets=*:CO:SNTL&activeOnly=true).
Nothing here touches the network.

    python3 build_system.py

SNOTEL sites are the ones whose coordinates fall inside the four basin
polygons in ../strontia-brief/basins/, so every snow pillow shown drains to a
gage that is also shown. The few facilities not in places.json carry their
OpenStreetMap way id, resolved 2026-08-31.
"""

import csv
import json
import os
from datetime import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
BRIEF = os.path.join(HERE, "..", "strontia-brief")
INFLUENT_CSV = os.path.join(HERE, "..", "..", "design-storm", "data",
                            "FoothillsInfluent.csv")

BASIN_FILES = [
    "south-platte-above-strontia-06707525.json",
    "blue-river-below-dillon-09050700.json",
    "fraser-below-moffat-09023562.json",
    "williams-fork-parshall-09037500.json",
]

DISCHARGE = "00060"
TURBIDITY = "63680"

GAGES = {
    "turbidity": (
        "Strontia Springs Sentinel Gauge", TURBIDITY, "Turbidity, FNU",
        "The sentinel. The last measurement point before 80% of Denver's water "
        "enters Strontia Springs Reservoir. Reads temperature, conductance, "
        "dissolved oxygen, pH, and turbidity every 15 minutes. Water passing "
        "here reaches the plant intake in about four hours (Denver Water's "
        "raw water group), yet what the plant receives tracks these readings "
        "from a day or two earlier, because the reservoir mixes and settles "
        "what arrives; that lag is the warning window a soft sensor tries to "
        "use. In the August 2026 "
        "storm, evening rain became a 329 FNU spike here by 1:45 AM while "
        "the flow gauge upstream barely moved: the sediment washed in from "
        "side canyons between the two, the stretch no gauge watches."),
    "flow": (
        "South Platte Gauge near Trumbull", DISCHARGE, "Flow, cubic ft/s",
        "Nearest upstream flow gage to Strontia Springs, below Brush Creek "
        "near Trumbull. This is where the August 2026 storm pulse was measured."),
    "fraser_below_moffat": (
        "Fraser River below Moffat Tunnel", DISCHARGE, "Flow, cubic ft/s",
        "Measures Fraser River water just below the Moffat Tunnel outlet at "
        "Winter Park, on the west side of the Continental Divide."),
    "williams_fork": (
        "Williams Fork Gauge near Parshall", DISCHARGE, "Flow, cubic ft/s",
        "Williams Fork near Parshall, on the Colorado River side. Williams Fork "
        "Reservoir water is used to repay the west slope for water sent east."),
    "north_fork_at_grant": (
        "North Fork Gauge at Grant", DISCHARGE, "Flow, cubic ft/s",
        "North Fork of the South Platte at Grant, just below where Roberts "
        "Tunnel water from Dillon Reservoir pours in from under the divide."),
    "north_fork_confluence": (
        "North Fork Confluence Gauge", DISCHARGE, "Flow, cubic ft/s",
        "Where the North Fork (carrying Dillon water) joins the mainstem South "
        "Platte, 2 km above the sentinel gage."),
    "mainstem_at_south_platte": (
        "South Platte Mainstem Gauge", DISCHARGE, "Flow, cubic ft/s",
        "The mainstem South Platte at the town of South Platte, just above the "
        "North Fork confluence."),
}

RESERVOIRS = {
    "dillon": ("Dillon Reservoir",
               "Denver Water's largest reservoir, on the Blue River west of "
               "the Continental Divide. Its water reaches Denver through the "
               "23-mile Roberts Tunnel."),
    "gross": ("Gross Reservoir",
               "North system storage in the foothills. Receives Fraser River "
               "water delivered by the Moffat Tunnel via South Boulder Creek."),
    "cheesman": ("Cheesman Reservoir",
               "Denver Water's oldest mountain reservoir (1905), on the "
               "mainstem South Platte above the sentinel gage."),
    "eleven_mile": ("Eleven Mile Canyon Reservoir",
               "High-plains storage on the South Platte in South Park. The "
               "marker sits at the dam, near Lake George."),
    "antero": ("Antero Reservoir",
               "The uppermost South Platte reservoir, in South Park."),
    "chatfield": ("Chatfield Reservoir",
               "Army Corps flood-control lake below Waterton Canyon. A "
               "Denver-side landmark rather than part of the supply chain."),
    "marston": ("Marston Forebay",
               "Terminal storage inside Denver, beside the Marston Treatment "
               "Plant. Fed by gravity from Waterton Canyon through Conduit 20. "
               "A forebay, not a lake: it has no natural inputs, water is "
               "moved here specifically to be treated."),
}


def load_places():
    with open(os.path.join(BRIEF, "places.json")) as f:
        return json.load(f)


def load_snotel_stations():
    with open(os.path.join(HERE, "snotel-co-stations.json")) as f:
        return json.load(f)


def basin_rings():
    rings = []
    for filename in BASIN_FILES:
        with open(os.path.join(BRIEF, "basins", filename)) as f:
            geometry = json.load(f)["features"][0]["geometry"]
        if geometry["type"] == "Polygon":
            rings.append(geometry["coordinates"][0])
        else:
            rings.extend(polygon[0] for polygon in geometry["coordinates"])
    return rings


def point_in_ring(point, ring):
    x, y = point
    crossings = False
    for i in range(len(ring)):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % len(ring)]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1:
            crossings = not crossings
    return crossings


def in_any_basin(station, rings):
    point = (station["longitude"], station["latitude"])
    return any(point_in_ring(point, ring) for ring in rings)


HIVIS_IMAGE = "https://usgs-nims-images.s3.amazonaws.com/overlay/{c}/{c}_newest.jpg"
HIVIS_PAGE = "https://apps.usgs.gov/hivis/camera/{c}"

CAMERAS_BY_POINT_ID = {
    "gage-06701900": [
        ("CO_South_Platte_River_Blw_Brush_Crk_near_Trumbull_Upstream",
         "Looking upstream at the gauge"),
        ("CO_South_Platte_River_Blw_Brush_Crk_near_Trumbull_Downstream",
         "Looking downstream"),
    ],
    "gage-09023562": [
        ("CO_Moffat_Tunnel_CAM",
         "The Fraser River just below the Moffat Tunnel west portal"),
    ],
    "res-dillon": [
        ("CO_Blue_River_Below_Dillon",
         "The Blue River just below Dillon Dam, at USGS gage 09050700"),
    ],
}


STORAGE_BY_POINT_ID = {
    "res-dillon": ("DILRESCO", 257304, "1987"),
    "res-cheesman": ("CHERESCO", 79064, "1989"),
    "res-chatfield": ("CHARESCO", 28709, "1988"),
    "dam-strontia": ("STRRESCO", 7863, "2021"),
}


def attach_storage(points):
    for point in points:
        entry = STORAGE_BY_POINT_ID.get(point["id"])
        if entry:
            abbrev, capacity_af, telemetry_since = entry
            point["capacity_af"] = capacity_af
            point["chart"] = {"type": "dwr", "abbrev": abbrev,
                              "label": "Water in storage, acre-feet",
                              "since": telemetry_since}


def attach_cameras(points):
    for point in points:
        cams = CAMERAS_BY_POINT_ID.get(point["id"])
        if cams:
            point["photos"] = [
                {"url": HIVIS_IMAGE.format(c=c), "page": HIVIS_PAGE.format(c=c),
                 "label": label} for c, label in cams]


def gage_points(places):
    points = []
    for key, (name, param, chart_label, blurb) in GAGES.items():
        gage = places["gages"][key]
        points.append({
            "id": f"gage-{gage['site']}",
            "kind": "gage",
            "name": name,
            "usgs_name": gage["name"],
            "lat": gage["lat"],
            "lon": gage["lon"],
            "blurb": blurb,
            "chart": {"type": "usgs", "site": gage["site"], "param": param,
                      "label": chart_label},
        })
    return points


def reservoir_points(places):
    points = []
    for key, (name, blurb) in RESERVOIRS.items():
        reservoir = places["reservoirs"][key]
        points.append({
            "id": f"res-{key}",
            "kind": "reservoir",
            "name": name,
            "usgs_name": reservoir["name"],
            "lat": reservoir["lat"],
            "lon": reservoir["lon"],
            "blurb": blurb,
        })
    points.append({
        "id": "res-ralston",
        "kind": "reservoir",
        "name": "Ralston Reservoir",
        "lat": 39.8276, "lon": -105.2496,
        "source": "OpenStreetMap way 64108533, natural=water, centroid",
        "blurb": "North system forebay. Gross Reservoir water is delivered here "
                 "on its way to the Northwater Treatment Plant.",
    })
    return points


def snotel_points(stations, rings):
    points = []
    for station in stations:
        if not in_any_basin(station, rings):
            continue
        points.append({
            "id": "sntl-" + station["stationId"],
            "kind": "snotel",
            "name": station["name"] + " SNOTEL",
            "lat": round(station["latitude"], 5),
            "lon": round(station["longitude"], 5),
            "elevation_ft": station["elevation"],
            "blurb": "Automated snow-measuring station at "
                     f"{int(station['elevation']):,} ft. A pressure-sensing "
                     "pillow weighs the snowpack; the water content of that "
                     "snow is next year's supply.",
            "chart": {"type": "snotel", "triplet": station["stationTriplet"],
                      "label": "Snow water equivalent, inches"},
        })
    return points


def facility_points(places):
    facilities = places["facilities"]
    foothills = facilities["foothills_plant"]
    marston_plant = facilities["marston_plant"]
    dam = facilities["strontia_springs_dam"]
    diversion = facilities["marston_diversion_dam"]
    return [
        {"id": "plant-foothills", "kind": "plant",
         "name": "Foothills Treatment Plant",
         "lat": foothills["lat"], "lon": foothills["lon"],
         "influent": True,
         "blurb": "Denver Water's largest treatment plant. Receives Strontia "
                  "Springs water through Conduit 26, treats it, and sends it "
                  "to the city."},
        {"id": "plant-marston", "kind": "plant",
         "name": "Marston Treatment Plant",
         "lat": marston_plant["lat"], "lon": marston_plant["lon"],
         "blurb": "Treats South Platte water delivered by gravity through "
                  "Conduit 20, plus Strontia Springs water."},
        {"id": "plant-northwater", "kind": "plant",
         "name": "Northwater Treatment Plant",
         "lat": 39.8239, "lon": -105.2284,
         "source": "OpenStreetMap way 791966622, man_made=water_works, centroid",
         "blurb": "The new north system plant beside Ralston Reservoir, "
                  "treating Moffat Tunnel water. Successor to the 1937 Moffat "
                  "plant."},
        {"id": "plant-moffat", "kind": "plant",
         "name": "Moffat Treatment Plant",
         "lat": 39.7493, "lon": -105.1208,
         "source": "OpenStreetMap way 366263859, man_made=water_works, centroid",
         "blurb": "The 1937 north system plant in Lakewood, being retired as "
                  "Northwater takes over its role."},
        {"id": "dam-strontia", "kind": "reservoir",
         "name": "Strontia Springs Dam",
         "lat": dam["lat"], "lon": dam["lon"],
         "blurb": "The 243-ft dam in Waterton Canyon that 80% of Denver's "
                  "water passes through. Diverts to the Foothills and Marston "
                  "plants. Aurora draws its supply here too."},
        {"id": "dam-marston-diversion", "kind": "reservoir",
         "name": "Conduit 20 Diversion",
         "lat": diversion["lat"], "lon": diversion["lon"],
         "blurb": "The second, smaller intake 2.6 miles below Strontia "
                  "Springs Dam: an instream diversion structure with a weir "
                  "that forms a small forebay in the river. The conduit "
                  "intake here delivers water directly to Marston Forebay "
                  "and the Marston Treatment Plant."},
    ]


def tunnel_lines(places):
    gages = places["gages"]
    reservoirs = places["reservoirs"]
    facilities = places["facilities"]
    dillon = reservoirs["dillon"]
    grant = gages["north_fork_at_grant"]
    fraser = gages["fraser_below_moffat"]
    dam = facilities["strontia_springs_dam"]
    foothills = facilities["foothills_plant"]
    diversion = facilities["marston_diversion_dam"]
    marston = reservoirs["marston"]
    return [
        {"id": "roberts", "name": "Roberts Tunnel", "kind": "tunnel",
         "coords": [[dillon["lon"], dillon["lat"]], [grant["lon"], grant["lat"]]],
         "blurb": "23 miles under the Continental Divide. Carries Dillon "
                  "Reservoir water east to the North Fork of the South Platte "
                  "at Grant. Straight line drawn between the verified portals."},
        {"id": "moffat", "name": "Moffat Water Tunnel", "kind": "tunnel",
         "coords": [[-105.646021, 39.9021997], [fraser["lon"], fraser["lat"]]],
         "source": "Portals from OpenStreetMap ways 626775058/17053656 (the "
                   "rail tunnel the water tunnel parallels); west end matches "
                   "USGS gage 09023562 within 70 m.",
         "blurb": "6.2 miles under the divide at Winter Park, beside the "
                  "railroad tunnel. Carries Fraser basin water east into South "
                  "Boulder Creek, bound for Gross Reservoir."},
        {"id": "conduit-26", "name": "Conduit 26", "kind": "tunnel",
         "coords": [[dam["lon"], dam["lat"]], [foothills["lon"], foothills["lat"]]],
         "blurb": "3.7 miles of 120-inch pipe from Strontia Springs Dam to the "
                  "Foothills plant. Capacity 750 million gallons a day. At "
                  "that full capacity the published diameter and flow work "
                  "out to about 15 ft/s, so water leaving the dam is only "
                  "about 20 minutes from the plant. Even from the sentinel "
                  "gauge, through the reservoir, to the intake is only about "
                  "four hours; the days-long lag the soft sensor uses comes "
                  "from mixing and settling in the reservoir, not travel."},
        {"id": "conduit-20", "name": "Conduit 20", "kind": "tunnel",
         "coords": [[diversion["lon"], diversion["lat"]], [marston["lon"], marston["lat"]]],
         "blurb": "Gravity conduit from the Conduit 20 Diversion in Waterton "
                  "Canyon to Marston Forebay inside Denver."},
    ]


def influent_series():
    toc, alk = [], []
    with open(INFLUENT_CSV) as f:
        for row in csv.DictReader(f):
            day = datetime.strptime(row["DATE"], "%m/%d/%Y").date().isoformat()
            if row["TOC_mg_L"]:
                toc.append({"t": day, "v": float(row["TOC_mg_L"])})
            if row["Alk_mg_L"]:
                alk.append({"t": day, "v": float(row["Alk_mg_L"])})
    return {"_comment": "Generated by build_system.py from "
                        "eddd/design-storm/data/FoothillsInfluent.csv.",
            "toc": toc, "alk": alk}


def build():
    places = load_places()
    rings = basin_rings()
    stations = load_snotel_stations()
    points = (reservoir_points(places) + gage_points(places)
              + snotel_points(stations, rings) + facility_points(places))
    attach_cameras(points)
    attach_storage(points)
    system = {
        "_comment": "Generated by build_system.py. Do not edit by hand.",
        "points": points,
        "lines": tunnel_lines(places),
    }
    out = os.path.join(HERE, "system.json")
    with open(out, "w") as f:
        json.dump(system, f, indent=1)
    with open(os.path.join(HERE, "foothills-influent.json"), "w") as f:
        json.dump(influent_series(), f, separators=(",", ":"))
    kinds = {}
    for point in system["points"]:
        kinds[point["kind"]] = kinds.get(point["kind"], 0) + 1
    print(f"wrote {out}: {kinds}, {len(system['lines'])} lines")


if __name__ == "__main__":
    build()
