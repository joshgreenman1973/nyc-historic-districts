# The landmarking of New York — methodology

An animated map of every New York City historic district and the year it was declared, from Brooklyn Heights in 1965 to today.

## What it shows

Each shape is a **historic district** designated by the New York City Landmarks Preservation Commission (LPC). Districts appear on the map in the order they were declared, colored by the decade of designation, and a **running acreage total** climbs as each one lights up. Press play to watch the map fill in from 1965 forward; scrub the timeline or hit "Show all" to see the whole picture at once. **Hover** a district for its name, year and size; **click** it to pin the panel and open its official LPC designation report and Wikipedia page.

This map covers **only designated, currently active historic districts and extensions** — not individual landmarks, scenic landmarks, interior landmarks, or areas that were merely proposed, calendared, denied or overturned.

## The count

- **159 historic districts and extensions**, declared between **Nov. 23, 1965** (Brooklyn Heights, the first) and **Nov. 25, 2025** (Beverley Square West and Ditmas Park West, in Flatbush). This **matches the LPC's own published count** of "159 historic districts and extensions."
- By borough: **Manhattan 82, Brooklyn 47, Queens 14, The Bronx 13, Staten Island 3**.
- **25** of the 159 are **extensions** of an earlier district. Each carries its own, later designation date and is drawn as its own shape — so a district and its extensions light up in different years.

### A note on the earlier 141

The first version of this project used NYC Open Data's Historic Districts export (`skyk-mpzq` / `xbvj-gfnw`), which returns only **141** shapes and omits about 18 extensions. Switching to the LPC's live ArcGIS layer (below) fixed this: the count now equals the LPC's official 159, and every extension is dated and mapped individually. The Open Data export also under-measured the total area by ~395 acres because it was missing those extensions.

## Source

- **Boundaries, designation dates, district names, borough, extension flag, LP number and the official report links** all come from the LPC's own live ArcGIS feature service, layer **`Historic_Districts_LPC`** on `services5.arcgis.com/Oos4pNA2538iVFA1`. This is the data behind the commission's official **[Discover NYC Landmarks](https://www.landmarks.nyc/)** map, reached from the LPC **[maps page](https://www.nyc.gov/site/lpc/designations/maps.page)**. Query filter: `STATUS_OF_ = 'DESIGNATED' AND CURRENT_ = 'Yes'` (159 records).
- **Designation reports:** each district's `Report_URL` from the same layer (the commission's official PDF at s-media.nyc.gov), upgraded to HTTPS.
- **"Wikipedia" links** run a title search for the district name.
- **Base map tiles:** © OpenStreetMap contributors, © CARTO (dark base map, tinted warm in CSS).

## How it was processed

Everything is reproducible with `build.py` (requires `pyproj`):

1. **Fetch** the 159 designated, current districts from the ArcGIS layer as GeoJSON, requesting `outSR=4326` so the geometry arrives already in **WGS84 (lng/lat)** — no reprojection needed.
2. **Convert dates.** `DESIG_DATE` arrives as epoch milliseconds (UTC midnight) and is converted to an ISO date. Verified against known designations (Brooklyn Heights → 1965‑11‑23, Greenwich Village → 1969‑04‑29).
3. **Measure area.** Each district's acreage is the true **geodesic area** of its polygon on the WGS84 ellipsoid (`pyproj.Geod`, holes subtracted; ÷ 4,046.856 m² per acre).
4. **Round** coordinates to five decimal places (~1 m) to shrink the file.
5. **Bucket** each district into a decade era (1965–1969, 1970s … 2020s) for coloring.
6. **Sort** by designation date so the animation reveals districts chronologically.

Output: `districts.json`, a single WGS84 GeoJSON FeatureCollection (159 features, ~510 KB).

## Acres landmarked

- All 159 districts together cover **≈ 4,574 acres, about 7.1 square miles** (roughly eight Central Parks).
- This is the **sum** of the 159 individual district areas. A few older districts sit partly inside larger ones — Carnegie Hill within the Expanded Carnegie Hill district, and two small Central Park West blocks within the Upper West Side/Central Park West district — so **about 16 acres (0.36%) are counted in two districts.** The **unique protected land** (all shapes dissolved together) is **≈ 4,557 acres**. The running counter shows the summed figure, since each district "adds" its own acreage as it appears.
- Overlap was measured directly with a polygon union (`shapely`); only those three pairs overlap by more than half an acre.

## Notes and caveats

- The **designation date** shown is the day the commission voted to designate each area.
- Boundary polygons are derived by the LPC primarily from Department of City Planning tax-lot data and are simplified slightly here for the web (coordinates rounded to five decimals); they are indicative, not survey-grade.
- Some designations have complicated histories (amended, re-designated, partially overturned). This map reflects only the districts the LPC currently marks as designated and active.
- The LPC periodically designates new districts. Re-run `python3 build.py --fetch` to refresh against the live service; the total, acreage and newest year update automatically.

## Fact-check (July 2026)

Claims on the map, and how each was verified:

| Claim | Status | Basis |
|---|---|---|
| Brooklyn Heights was the **first** historic district, **Nov. 23, 1965** | ✅ | LPC layer `DESIG_DATE`; corroborated by the LPC/Wikipedia summary ("the first landmark district … was designated in November 1965"). |
| "**about seven months** after the Landmarks Law of April 1965" | ✅ | Landmarks Law passed the City Council April 7, 1965 and was signed by Mayor Wagner that month → to Nov. 23 is ~7 months. |
| **159** historic districts and extensions; borough split 82/47/14/13/3 | ✅ | Direct count of the LPC's live `Historic_Districts_LPC` layer; matches the commission's own published "159 historic districts and extensions." |
| **25** are extensions | ✅ | `EXTENSION = 'Yes'` in the LPC layer. |
| **≈ 4,574 acres / 7.1 sq mi** total (≈ 4,557 unique) | ✅ | Geodesic area of every polygon; overlap quantified via polygon union (16 acres across 3 pairs). |
| Greenwich Village designated **April 29, 1969** (LP‑00489) | ✅ | LPC layer; official report PDF resolves. |
| Latest districts: **Beverley Square West & Ditmas Park West, Nov. 25, 2025** | ✅ | LPC layer; corroborated by Nov. 2025 press coverage of the two new Flatbush districts. |

## A note on AI

This map was built with the help of AI. The underlying data is straight from the city's Landmarks Preservation Commission, but the processing and code have not been exhaustively hand-audited. Check any figure against the source before relying on it.
