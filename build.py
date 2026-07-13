#!/usr/bin/env python3
"""
Build districts.json for "The landmarking of New York".

Source: the Landmarks Preservation Commission's OWN live ArcGIS feature service —
the layer that powers the official "Discover NYC Landmarks" map
(services5.arcgis.com/Oos4pNA2538iVFA1 → Historic_Districts_LPC). This is the
authoritative, complete set: 159 designated, currently-active historic districts
and extensions, each broken out with its own designation date and official
designation-report URL.

(An earlier version of this project used NYC Open Data's skyk-mpzq / xbvj-gfnw
export, which is a consolidated snapshot with only 141 shapes — it omits ~18
extensions. The ArcGIS service matches the LPC's published count of 159.)

Usage:
    python3 build.py            # uses cached data/hd_arcgis.geojson if present
    python3 build.py --fetch    # re-download from the live ArcGIS service

Requires: pyproj  (pip install pyproj)
"""
import json, os, sys, urllib.request, urllib.parse, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
RAW  = os.path.join(HERE, "data", "hd_arcgis.geojson")
OUT  = os.path.join(HERE, "districts.json")

SERVICE = ("https://services5.arcgis.com/Oos4pNA2538iVFA1/arcgis/rest/services/"
           "Historic_Districts/FeatureServer/0/query")
PARAMS = {
    "where": "STATUS_OF_='DESIGNATED' AND CURRENT_='Yes'",
    "outFields": "AREA_NAME,DESIG_DATE,BOROUGH,EXTENSION,LP_NUMBER,Report_URL",
    "outSR": "4326",          # WGS84 lng/lat — no reprojection needed
    "f": "geojson",
}

BORO = {"MN": "Manhattan", "BK": "Brooklyn", "BX": "The Bronx",
        "QN": "Queens", "SI": "Staten Island"}
ACRE_M2 = 4046.8564224        # 1 acre in square meters

def era(y):
    if y <= 1969: return "1965–1969"
    if y < 1980:  return "1970s"
    if y < 1990:  return "1980s"
    if y < 2000:  return "1990s"
    if y < 2010:  return "2000s"
    if y < 2020:  return "2010s"
    return "2020s"

def iso(ms):
    # ArcGIS dates are epoch milliseconds at UTC midnight
    return datetime.datetime.utcfromtimestamp(ms / 1000).strftime("%Y-%m-%d")

def main():
    if "--fetch" in sys.argv or not os.path.exists(RAW):
        os.makedirs(os.path.dirname(RAW), exist_ok=True)
        url = SERVICE + "?" + urllib.parse.urlencode(PARAMS)
        print("Downloading", url)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as r, open(RAW, "wb") as f:
            f.write(r.read())

    from pyproj import Geod
    g = Geod(ellps="WGS84")

    def ring_acres(coords):
        lons = [c[0] for c in coords]; lats = [c[1] for c in coords]
        a, _ = g.polygon_area_perimeter(lons, lats)
        return abs(a) / ACRE_M2   # geodesic area in acres

    def acres(geom):
        t = geom["type"]; tot = 0.0
        if t == "Polygon":
            rings = geom["coordinates"]
            tot += ring_acres(rings[0])
            for h in rings[1:]: tot -= ring_acres(h)
        elif t == "MultiPolygon":
            for poly in geom["coordinates"]:
                tot += ring_acres(poly[0])
                for h in poly[1:]: tot -= ring_acres(h)
        return round(tot, 2)

    def rnd(geom):
        r = lambda c: [round(c[0], 5), round(c[1], 5)]
        if geom["type"] == "Polygon":
            geom["coordinates"] = [[r(p) for p in ring] for ring in geom["coordinates"]]
        elif geom["type"] == "MultiPolygon":
            geom["coordinates"] = [[[r(p) for p in ring] for ring in poly]
                                   for poly in geom["coordinates"]]
        return geom

    src = json.load(open(RAW))
    feats = []
    for f in src["features"]:
        p = f["properties"]
        if not f.get("geometry") or not p.get("DESIG_DATE"):
            continue
        d = iso(p["DESIG_DATE"]); y = int(d[:4])
        report = (p.get("Report_URL") or "").strip().replace("http://", "https://") or None
        feats.append({
            "type": "Feature",
            "properties": {
                "name": p["AREA_NAME"].strip(),
                "date": d, "year": y,
                "boro": BORO.get(p.get("BOROUGH"), p.get("BOROUGH")),
                "ext": p.get("EXTENSION") == "Yes",
                "lp": p.get("LP_NUMBER"),
                "report": report,
                "era": era(y),
                "acres": acres(f["geometry"]),
            },
            "geometry": rnd(f["geometry"]),
        })

    feats.sort(key=lambda f: (f["properties"]["date"], f["properties"]["name"]))
    json.dump({"type": "FeatureCollection", "features": feats},
              open(OUT, "w"), separators=(",", ":"))
    tot = sum(f["properties"]["acres"] for f in feats)
    print(f"Wrote {len(feats)} districts -> {OUT} ({os.path.getsize(OUT)//1024} KB)")
    print(f"Total: {tot:,.0f} acres ({tot/640:.2f} sq mi)")

if __name__ == "__main__":
    main()
