#!/usr/bin/env python3
"""Build storm-impact.json, the data behind the Storm Impact static page.

Reads only files already in this repository; nothing touches the network and
nothing in ../data, ../strontia-brief, or ../water-system-3d is modified.

    python3 build_data.py

Inputs
  ../strontia-brief/series/*.json     USGS 15-minute values, Aug 14-15 2026
  ../data/USGS_South_Platte.csv        USGS daily summaries, gage 06707525
  ../data/Strontia 0407_0819.xlsx      Denver Water reservoir sonde casts
  ../data/FoothillsInfluent.csv        Denver Water daily TOC/alkalinity
  ../strontia-brief/places.json        Sensor coordinates
  ../strontia-brief/basins/*.json      River lines for the sensor map

Uses only the standard library; the xlsx is read directly as zipped XML.
Every number the page shows is computed here or on the page from these files.
"""

import csv
import json
import os
import re
import statistics
import zipfile
from datetime import date, datetime, timedelta
from xml.etree import ElementTree as ET

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
DATA = os.path.join(ROOT, "data")
BRIEF = os.path.join(ROOT, "strontia-brief")
OUT = os.path.join(HERE, "storm-impact.json")

# Window of daily and sonde data carried into the page.
WINDOW_START = date(2026, 7, 15)
WINDOW_END = date(2026, 8, 19)

# The two storms the planning doc compares. River peak day is from the daily
# USGS file; the 15-minute peak (Aug only) is found in the series file.
STORMS = [
    {"id": "aug14", "label": "Aug 14-15, 2026", "start": "2026-08-12",
     "end": "2026-08-20", "river_peak_date": "2026-08-15"},
    {"id": "jul28", "label": "Jul 28, 2026", "start": "2026-07-25",
     "end": "2026-08-02", "river_peak_date": "2026-07-28"},
]

# Depth bands in metres below the surface. The file's "Vertical Position" has no
# unit; Jake (Denver Water) confirmed metres.
BANDS = [(0, 5), (5, 15), (15, 25), (25, 35), (35, 50)]

# Foothills' primary intake pipe is 45 ft below the surface (Cassidi, Denver
# Water). Each cast reports the turbidity of its reading nearest that depth,
# if one lies within INTAKE_TOL_M. The sonde hangs mid-reservoir, roughly 400 m
# from the intake (Jake), so this is the sonde's reading at the intake's depth,
# not a reading at the intake itself.
INTAKE_DEPTH_FT = 45
INTAKE_DEPTH_M = round(INTAKE_DEPTH_FT * 0.3048, 2)
INTAKE_TOL_M = 1.0

# A new cast starts when consecutive sonde readings are this far apart.
CAST_GAP = timedelta(minutes=20)

# Denver Water's team found that the out-of-range sonde readings happen when
# the sonde drops to the bottom of the reservoir and stirs up
# sediment. A cast is treated as bottom contact when any reading at or below
# 34 m is more than 10x the cast's median turbidity
# between 20 and 30 m. In this file that flags exactly the 11 casts from Apr 7 to
# May 5, 2026 with spikes of 52 to 2,438 NTU near the bottom. Those casts are left
# out of the page entirely.
BOTTOM_REF = (20, 30)
BOTTOM_ZONE = 34
BOTTOM_FACTOR = 10


def parse_us_date(s):
    return datetime.strptime(s, "%m/%d/%Y").date()


def num(s):
    s = (s or "").strip()
    return float(s) if s else None


# ---------------------------------------------------------------- USGS 15-min

def read_usgs_iv(path):
    with open(path) as f:
        doc = json.load(f)
    out = {}
    for ts in doc["value"]["timeSeries"]:
        code = ts["variable"]["variableCode"][0]["value"]
        unit = ts["variable"]["unit"]["unitCode"]
        pts = []
        for v in ts["values"][0]["value"]:
            val = float(v["value"])
            # USGS uses -999999 as a no-data sentinel.
            if val <= -999990:
                continue
            pts.append([v["dateTime"][:16], val])
        out[code] = {"unit": unit, "points": pts,
                     "site": ts["sourceInfo"]["siteCode"][0]["value"],
                     "site_name": ts["sourceInfo"]["siteName"]}
    return out


# ------------------------------------------------------------------ sonde xlsx

def col_index(ref):
    letters = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def read_xlsx_rows(path):
    ns = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall("m:si", ns):
                shared.append("".join(t.text or "" for t in si.iter(
                    "{%s}t" % ns["m"])))
        with z.open("xl/worksheets/sheet1.xml") as f:
            for _, el in ET.iterparse(f):
                if el.tag != "{%s}row" % ns["m"]:
                    continue
                row = {}
                for c in el.findall("m:c", ns):
                    v = c.find("m:v", ns)
                    if v is None:
                        continue
                    if c.get("t") == "s":
                        row[col_index(c.get("r"))] = shared[int(v.text)]
                    else:
                        row[col_index(c.get("r"))] = v.text
                el.clear()
                if row:
                    width = max(row) + 1
                    yield [row.get(i) for i in range(width)]


def excel_datetime(serial):
    dt = datetime(1899, 12, 30) + timedelta(days=float(serial))
    return (dt + timedelta(microseconds=500000)).replace(microsecond=0)


def read_sonde(path):
    rows = read_xlsx_rows(path)
    header = [h.strip() if isinstance(h, str) else h for h in next(rows)]
    ix = {name: header.index(name) for name in
          ("Time stamp", "Vertical Position", "Turbidity NTU", "Temp C")}
    readings = []
    for r in rows:
        try:
            t = excel_datetime(r[ix["Time stamp"]])
            depth = float(r[ix["Vertical Position"]])
            turb = float(r[ix["Turbidity NTU"]])
            temp = float(r[ix["Temp C"]])
        except (TypeError, ValueError, IndexError):
            continue
        readings.append((t, depth, turb, temp))
    readings.sort(key=lambda x: x[0])

    casts = []
    for rd in readings:
        if not casts or rd[0] - casts[-1][-1][0] > CAST_GAP:
            casts.append([])
        casts[-1].append(rd)
    return readings, casts


def band_of(depth):
    for i, (lo, hi) in enumerate(BANDS):
        if lo <= depth < hi:
            return i
    return None


def bottom_contact(cast):
    ref = [r[2] for r in cast if BOTTOM_REF[0] <= r[1] < BOTTOM_REF[1]]
    deep = [r[2] for r in cast if r[1] >= BOTTOM_ZONE]
    return bool(ref and deep and
                max(deep) > BOTTOM_FACTOR * statistics.median(ref))


def summarize_cast(cast):
    by_band = [[] for _ in BANDS]
    for _, depth, turb, _ in cast:
        b = band_of(depth)
        if b is not None:
            by_band[b].append(turb)
    return [round(statistics.median(v), 2) if v else None for v in by_band]


def at_intake_depth(cast):
    near = min(cast, key=lambda r: abs(r[1] - INTAKE_DEPTH_M))
    if abs(near[1] - INTAKE_DEPTH_M) > INTAKE_TOL_M:
        return None
    return round(near[2], 2)


# ----------------------------------------------------------------- daily files

def read_gage_daily():
    out = []
    with open(os.path.join(DATA, "USGS_South_Platte.csv")) as f:
        for r in csv.DictReader(f):
            d = parse_us_date(r["Date"])
            if WINDOW_START <= d <= WINDOW_END:
                out.append({"date": d.isoformat(),
                            "turb_max": num(r["Turbidity_Max"]),
                            "turb_median": num(r["Turbidity_Median"]),
                            "cond_mean": num(r["Specific_Cond_Mean"])})
    return out


def read_toc():
    out = []
    with open(os.path.join(DATA, "FoothillsInfluent.csv")) as f:
        for r in csv.DictReader(f):
            d = parse_us_date(r["DATE"])
            if WINDOW_START <= d <= WINDOW_END:
                out.append({"date": d.isoformat(), "toc": num(r["TOC_mg_L"]),
                            "alk": num(r["Alk_mg_L"])})
    return out


# ------------------------------------------------------------------ geography

def read_places():
    with open(os.path.join(BRIEF, "places.json")) as f:
        p = json.load(f)
    g, fac = p["gages"], p["facilities"]

    def pt(src, key, label, role, order):
        return {"id": key, "label": label, "role": role, "order": order,
                "name": src[key]["name"],
                "lat": src[key]["lat"], "lon": src[key]["lon"]}

    return [
        pt(g, "flow", "Trumbull flow gage", "upstream", 0),
        pt(g, "turbidity", "River gage above Strontia", "river", 1),
        pt(fac, "strontia_springs_reservoir", "Strontia Springs Reservoir",
           "reservoir", 2),
        pt(fac, "strontia_springs_dam", "Strontia Springs Dam", "dam", 3),
        pt(fac, "conduit_26_intake", "Conduit 26 intake", "intake", 4),
        pt(fac, "foothills_plant", "Foothills plant", "plant", 5),
    ]


def read_rivers(bbox):
    lo_lon, lo_lat, hi_lon, hi_lat = bbox
    lines = []
    for name in ("mainstem-flowlines-06707525.json",
                 "downstream-mainstem-06707525.json"):
        with open(os.path.join(BRIEF, "basins", name)) as f:
            fc = json.load(f)
        for ft in fc["features"]:
            geom = ft["geometry"]
            parts = ([geom["coordinates"]] if geom["type"] == "LineString"
                     else geom["coordinates"])
            for part in parts:
                keep = [[round(x, 5), round(y, 5)] for x, y in part
                        if lo_lon <= x <= hi_lon and lo_lat <= y <= hi_lat]
                if len(keep) > 1:
                    lines.append(keep)
    return lines


# ---------------------------------------------------------------- comparisons

def storm_summary(storm, iv_turb, gage_daily, casts_out, toc):
    peak_day = storm["river_peak_date"]
    peak_date = date.fromisoformat(peak_day)
    daily = {d["date"]: d for d in gage_daily}

    river = {"date": peak_day, "value": daily[peak_day]["turb_max"],
             "unit": "FNU", "resolution": "daily maximum", "time": None}
    fine = [p for p in iv_turb if p[0].startswith(peak_day)]
    if fine:
        t, v = max(fine, key=lambda p: p[1])
        river.update(value=v, time=t, resolution="15-minute")
    anchor = datetime.fromisoformat(river["time"] or peak_day + "T12:00")

    # Baseline: median of daily-median turbidity over the 5 days before.
    before = [daily[(peak_date - timedelta(days=k)).isoformat()]["turb_median"]
              for k in range(1, 6)
              if (peak_date - timedelta(days=k)).isoformat() in daily]
    before = [b for b in before if b is not None]
    river["baseline_median"] = (round(statistics.median(before), 1)
                                if before else None)

    # Reservoir: the full cast with the highest band median within 4 days
    # after the river peak day starts.
    lo = datetime.combine(peak_date, datetime.min.time())
    hi = lo + timedelta(days=4)
    best = None
    for c in casts_out:
        t = datetime.fromisoformat(c["t"])
        if not (lo <= t < hi) or not c["full"]:
            continue
        for b, v in enumerate(c["bands"]):
            if v is not None and (best is None or v > best["value"]):
                best = {"value": v, "time": c["t"], "band": b}
    pre = [c["bands"] for c in casts_out if c["full"]
           and lo - timedelta(days=3) <= datetime.fromisoformat(c["t"]) < lo]
    if best:
        b = best["band"]
        vals = [x[b] for x in pre if x[b] is not None]
        best["band_label"] = "%d-%d" % BANDS[b]
        best["baseline_median"] = (round(statistics.median(vals), 2)
                                   if vals else None)
        best["hours_after_river_peak"] = round(
            (datetime.fromisoformat(best["time"]) - anchor)
            .total_seconds() / 3600, 1)

    # Reservoir at the intake's depth: same window and baseline rule.
    idp = None
    for c in casts_out:
        t = datetime.fromisoformat(c["t"])
        if (lo <= t < hi and c["full"] and c["at_intake"] is not None
                and (idp is None or c["at_intake"] > idp["value"])):
            idp = {"value": c["at_intake"], "time": c["t"]}
    if idp:
        vals = [c["at_intake"] for c in casts_out if c["full"]
                and c["at_intake"] is not None
                and lo - timedelta(days=3) <= datetime.fromisoformat(c["t"]) < lo]
        idp["depth_m"] = INTAKE_DEPTH_M
        idp["baseline_median"] = (round(statistics.median(vals), 2)
                                  if vals else None)
        idp["hours_after_river_peak"] = round(
            (datetime.fromisoformat(idp["time"]) - anchor)
            .total_seconds() / 3600, 1)

    # Plant: highest TOC from the river peak day through 4 days after (first
    # day if tied), against the median of the 5 days before.
    tocd = {d["date"]: d["toc"] for d in toc}
    base = [tocd[k] for k in ((peak_date - timedelta(days=i)).isoformat()
                              for i in range(1, 6)) if tocd.get(k) is not None]
    after = [(k, tocd[k]) for k in ((peak_date + timedelta(days=i)).isoformat()
                                    for i in range(0, 5))
             if tocd.get(k) is not None]
    plant = None
    if after:
        top = max(v for _, v in after)
        k = next(k for k, v in after if v == top)
        plant = {"date": k, "value": top, "unit": "mg/L",
                 "baseline_median": round(statistics.median(base), 2)
                 if base else None,
                 "days_after_river_peak":
                     (date.fromisoformat(k) - peak_date).days}

    return {"id": storm["id"], "river": river, "reservoir": best,
            "intake_depth": idp, "plant": plant}


# ------------------------------------------------------------------------ main

def main():
    series = os.path.join(BRIEF, "series")
    gage_iv = read_usgs_iv(os.path.join(
        series, "06707525-turbidity-conductance-aug14-15.json"))
    flow_iv = read_usgs_iv(os.path.join(
        series, "06701900-discharge-aug14-15.json"))

    readings, casts = read_sonde(os.path.join(DATA, "Strontia 0407_0819.xlsx"))
    excluded = [c for c in casts if bottom_contact(c)]
    casts = [c for c in casts if not bottom_contact(c)]
    max_depth = max(r[1] for c in casts for r in c)
    casts_out = []
    for c in casts:
        t0 = c[0][0]
        if not (WINDOW_START <= t0.date() <= WINDOW_END):
            continue
        depths = [r[1] for r in c]
        casts_out.append({
            "t": t0.isoformat(timespec="minutes"),
            "t_end": c[-1][0].isoformat(timespec="minutes"),
            # A full cast reaches past 40 m; the short
            # ones only sample the top few metres.
            "full": max(depths) >= 40,
            "bands": summarize_cast(c),
            "at_intake": at_intake_depth(c),
            "readings": [[round(r[1], 2), round(r[2], 2), round(r[3], 2)]
                         for r in c],
        })

    gage_daily = read_gage_daily()
    toc = read_toc()
    places = read_places()
    lats = [p["lat"] for p in places]
    lons = [p["lon"] for p in places]
    bbox = [min(lons) - 0.02, min(lats) - 0.02,
            max(lons) + 0.02, max(lats) + 0.02]

    turb = gage_iv["63680"]["points"]
    summaries = [storm_summary(s, turb, gage_daily, casts_out, toc)
                 for s in STORMS]

    out = {
        "_generated_by": "storm-impact/build_data.py",
        "_generated_at": datetime.now().isoformat(timespec="seconds"),
        "_notice": ("All readings are provisional and subject to revision. "
                    "Denver Water data terms apply; see data/TERMS.md."),
        "storms": STORMS,
        "summaries": summaries,
        "bands": [list(b) for b in BANDS],
        "intake": {"depth_ft": INTAKE_DEPTH_FT, "depth_m": INTAKE_DEPTH_M,
                   "tolerance_m": INTAKE_TOL_M,
                   "source": ("Primary intake pipe 45 ft below the surface "
                              "(Cassidi, Denver Water). Values are the sonde's "
                              "reading nearest that depth; the sonde is mid-"
                              "reservoir, roughly 400 m from the intake (Jake).")},
        "sonde_max_depth": round(max_depth, 1),
        "sonde_excluded_bottom_contact": [
            {"t": c[0][0].isoformat(timespec="minutes"),
             "max_turbidity": round(max(r[2] for r in c), 1),
             "in_window": WINDOW_START <= c[0][0].date() <= WINDOW_END}
            for c in excluded],
        "gage_15min": {
            "site": gage_iv["63680"]["site"],
            "site_name": gage_iv["63680"]["site_name"],
            "turbidity": {"unit": "FNU", "points": turb},
            "conductance": {"unit": "uS/cm @25C",
                            "points": gage_iv["00095"]["points"]},
        },
        "trumbull_15min": {
            "site": flow_iv["00060"]["site"],
            "site_name": flow_iv["00060"]["site_name"],
            "unit": "cfs", "points": flow_iv["00060"]["points"],
        },
        "gage_daily": gage_daily,
        "sonde_casts": casts_out,
        "toc_daily": toc,
        "places": places,
        "map_bbox": [round(v, 4) for v in bbox],
        "rivers": read_rivers(bbox),
    }
    with open(OUT, "w") as f:
        json.dump(out, f, separators=(",", ":"))

    # Cross-check against the daily band-median table in
    # docs/scenario-2-planning.md.
    print("wrote %s (%d casts, %d KB)" % (os.path.relpath(OUT, ROOT),
                                          len(casts_out),
                                          os.path.getsize(OUT) // 1024))
    print("left out %d bottom-contact casts: %s" % (len(excluded), ", ".join(
        "%s (%.0f NTU)" % (c[0][0].strftime("%b %d %H:%M"),
                           max(r[2] for r in c)) for c in excluded)))
    for sm in summaries:
        it = sm["intake_depth"]
        if it:
            print("%s: at intake depth (%.2f m) peak %.2f NTU at %s, baseline %s, "
                  "%.1f h after river peak" % (sm["id"], INTAKE_DEPTH_M, it["value"],
                  it["time"], it["baseline_median"], it["hours_after_river_peak"]))
    print("daily median turbidity by band (all readings that day):")
    for d in range(13, 20):
        day = date(2026, 8, d)
        vals = [[] for _ in BANDS]
        for t, depth, tb, _ in readings:
            if t.date() == day and band_of(depth) is not None:
                vals[band_of(depth)].append(tb)
        print("  Aug %d  " % d + "  ".join(
            "%5.1f" % statistics.median(v) if v else "   - " for v in vals))
    for s in summaries:
        print(json.dumps(s))


if __name__ == "__main__":
    main()
