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

Requires: pyproj, shapely  (pip install pyproj shapely)
"""
import json, os, sys, urllib.request, urllib.parse, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
RAW  = os.path.join(HERE, "data", "hd_arcgis.geojson")
LAND = os.path.join(HERE, "data", "borough_boundaries.geojson")
META = os.path.join(HERE, "data", "fetch_meta.json")
OUT  = os.path.join(HERE, "districts.json")

SERVICE = ("https://services5.arcgis.com/Oos4pNA2538iVFA1/arcgis/rest/services/"
           "Historic_Districts/FeatureServer/0/query")
LAYER_INFO = ("https://services5.arcgis.com/Oos4pNA2538iVFA1/arcgis/rest/services/"
              "Historic_Districts/FeatureServer/0?f=json")
# DCP Borough Boundaries, water areas excluded (NYC Open Data gthc-hcne)
LAND_URL = "https://data.cityofnewyork.us/api/geospatial/gthc-hcne?method=export&format=GeoJSON"
LAND_BORO = {"Manhattan": "Manhattan", "Brooklyn": "Brooklyn", "Queens": "Queens",
             "Bronx": "The Bronx", "Staten Island": "Staten Island"}
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
    def get(url):
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as r:
            return r.read()

    if "--fetch" in sys.argv or not os.path.exists(RAW):
        os.makedirs(os.path.dirname(RAW), exist_ok=True)
        url = SERVICE + "?" + urllib.parse.urlencode(PARAMS)
        print("Downloading", url)
        open(RAW, "wb").write(get(url))
        info = json.loads(get(LAYER_INFO))
        edited = (info.get("editingInfo") or {}).get("dataLastEditDate")
        json.dump({"retrieved": datetime.date.today().isoformat(),
                   "layer_edited": iso(edited) if edited else None},
                  open(META, "w"), indent=1)
    if "--fetch" in sys.argv or not os.path.exists(LAND):
        print("Downloading", LAND_URL)
        open(LAND, "wb").write(get(LAND_URL))
    fetch_meta = json.load(open(META)) if os.path.exists(META) else {}

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

    # Overlap and water. A few districts overlap, and a few boundaries reach into the water.
    #   net     = each district's NEW footprint: its area minus ground already covered by an
    #             earlier-designated district. Summed chronologically it equals the union, so the
    #             running acreage counter never double-counts overlapping districts.
    #   netLand = the same, clipped to land (DCP borough boundaries, water excluded). Used for the
    #             "% of borough land" chips, whose denominator is that same land boundary.
    from shapely.geometry import shape
    from shapely.ops import unary_union
    def gac(geom):
        if geom.is_empty: return 0.0
        a, _ = g.geometry_area_perimeter(geom)
        return abs(a) / ACRE_M2
    land_feats = json.load(open(LAND))["features"]
    land = unary_union([shape(f["geometry"]).buffer(0) for f in land_feats])
    boro_land = {}
    for lf in land_feats:
        b = LAND_BORO[lf["properties"]["boroname"]]
        boro_land[b] = round(boro_land.get(b, 0) + gac(shape(lf["geometry"]).buffer(0)), 1)
    acc = None; acc_land = None
    for f in feats:
        gm = shape(f["geometry"]).buffer(0)
        gl = gm.intersection(land)
        if acc is None:
            net, net_land = gac(gm), gac(gl)
            acc, acc_land = gm, gl
        else:
            net = gac(gm) - gac(gm.intersection(acc))
            net_land = gac(gl) - gac(gl.intersection(acc_land))
            acc = unary_union([acc, gm]); acc_land = unary_union([acc_land, gl])
        f["properties"]["net"] = round(max(net, 0.0), 2)
        f["properties"]["netLand"] = round(max(net_land, 0.0), 2)

    P = [f["properties"] for f in feats]
    meta = {
        "retrieved": fetch_meta.get("retrieved"),
        "layer_edited": fetch_meta.get("layer_edited"),
        "count": len(P),
        "extensions": sum(p["ext"] for p in P),
        "first": {"name": P[0]["name"], "date": P[0]["date"]},
        "last": [{"name": p["name"], "date": p["date"]} for p in P if p["date"] == P[-1]["date"]],
        "sum_acres": round(sum(p["acres"] for p in P), 1),
        "unique_acres": round(sum(p["net"] for p in P), 1),
        "unique_land_acres": round(sum(p["netLand"] for p in P), 1),
        "boro_land_acres": boro_land,
    }

    json.dump({"type": "FeatureCollection", "meta": meta, "features": feats},
              open(OUT, "w"), separators=(",", ":"))
    tot = sum(f["properties"]["acres"] for f in feats)
    print(f"Wrote {len(feats)} districts -> {OUT} ({os.path.getsize(OUT)//1024} KB)")
    print(f"Total: {tot:,.0f} acres summed · {meta['unique_acres']:,.0f} unique "
          f"({meta['unique_acres']/640:.2f} sq mi) · {meta['unique_land_acres']:,.0f} unique on land")
    for b, a in boro_land.items():
        n = sum(p["netLand"] for p in P if p["boro"] == b)
        print(f"  {b}: {n:,.0f} of {a:,.0f} land acres = {n/a*100:.2f}%")
    print("Meta:", json.dumps({k: meta[k] for k in ("retrieved", "layer_edited", "count", "extensions")}))

if __name__ == "__main__":
    main()
