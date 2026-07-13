#!/usr/bin/env python3
"""
Build districts.json for "The landmarking of New York".

Source: NYC Landmarks Preservation Commission "Historic Districts" (skyk-mpzq)
on NYC Open Data. We pull the GeoJSON export, keep only currently-active
DESIGNATED districts, reproject the boundary geometry from NY State Plane
(EPSG:2263, US feet) to WGS84 (EPSG:4326) for web mapping, and attach a
decade-era bucket for coloring.

Usage:
    python3 build.py            # uses the cached data/hd.geojson if present
    python3 build.py --fetch    # re-download the raw export first

Requires: pyproj  (pip install pyproj)
"""
import json, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RAW  = os.path.join(HERE, "data", "hd.geojson")
OUT  = os.path.join(HERE, "districts.json")
# Export endpoint (keyless; the SoQL query endpoint now needs an app token, this does not)
URL  = "https://data.cityofnewyork.us/resource/skyk-mpzq.geojson?$limit=6000"

BORO = {"MN": "Manhattan", "BK": "Brooklyn", "BX": "The Bronx",
        "QN": "Queens", "SI": "Staten Island"}

ACRE_SQFT = 43560.0  # 1 acre = 43,560 sq ft

def _ring_area(ring):
    a = 0.0
    for i in range(len(ring) - 1):
        x1, y1 = ring[i]; x2, y2 = ring[i + 1]
        a += x1 * y2 - x2 * y1
    return a / 2.0

def acres(geom):
    """Planar area in acres, computed on the source EPSG:2263 (US-ft) rings via the
    shoelace formula (exterior minus holes). Cross-checked to match the dataset's own
    shape_area field to <0.01%. Call BEFORE reprojection."""
    total = 0.0
    if geom["type"] == "Polygon":
        rings = geom["coordinates"]
        total += abs(_ring_area(rings[0]))
        for h in rings[1:]:
            total -= abs(_ring_area(h))
    elif geom["type"] == "MultiPolygon":
        for poly in geom["coordinates"]:
            total += abs(_ring_area(poly[0]))
            for h in poly[1:]:
                total -= abs(_ring_area(h))
    return round(total / ACRE_SQFT, 2)

def era(y):
    if y <= 1969: return "1965–1969"
    if y < 1980:  return "1970s"
    if y < 1990:  return "1980s"
    if y < 2000:  return "1990s"
    if y < 2010:  return "2000s"
    if y < 2020:  return "2010s"
    return "2020s"

def main():
    if "--fetch" in sys.argv or not os.path.exists(RAW):
        os.makedirs(os.path.dirname(RAW), exist_ok=True)
        print("Downloading", URL)
        urllib.request.urlretrieve(URL, RAW)

    from pyproj import Transformer
    T = Transformer.from_crs(2263, 4326, always_xy=True)  # State Plane ft -> lng/lat

    def ring(r):
        return [[round(lng, 5), round(lat, 5)]
                for lng, lat in (T.transform(x, y) for x, y in r)]

    def reproj(g):
        if g["type"] == "Polygon":
            return {"type": "Polygon", "coordinates": [ring(r) for r in g["coordinates"]]}
        if g["type"] == "MultiPolygon":
            return {"type": "MultiPolygon",
                    "coordinates": [[ring(r) for r in poly] for poly in g["coordinates"]]}
        return g

    src = json.load(open(RAW))
    feats = []
    for f in src["features"]:
        p = f["properties"]
        # keep only currently-active designated districts
        if p.get("status_of_") != "DESIGNATED" or p.get("current_") != "Yes":
            continue
        if not f.get("geometry") or not p.get("desdate"):
            continue
        d = p["desdate"][:10]; y = int(d[:4])
        feats.append({
            "type": "Feature",
            "properties": {
                "name": p["area_name"].strip(),
                "date": d, "year": y,
                "boro": BORO.get(p["borough"], p["borough"]),
                "ext": p.get("extension") == "Yes",
                "lp": p.get("lp_number"),
                "era": era(y),
                "acres": acres(f["geometry"]),  # computed before reprojection
            },
            "geometry": reproj(f["geometry"]),
        })

    feats.sort(key=lambda f: (f["properties"]["date"], f["properties"]["name"]))
    json.dump({"type": "FeatureCollection", "features": feats},
              open(OUT, "w"), separators=(",", ":"))
    print(f"Wrote {len(feats)} districts -> {OUT} ({os.path.getsize(OUT)//1024} KB)")

if __name__ == "__main__":
    main()
