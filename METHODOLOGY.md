# The landmarking of New York — methodology

An animated map of every New York City historic district and the year it was declared, from Brooklyn Heights in 1965 to today.

## What it shows

Each shape is a **historic district** designated by the New York City Landmarks Preservation Commission (LPC). Districts appear on the map in the order they were declared and are colored by the decade of designation. A **running acreage total** climbs as each district lights up. Press play to watch the map fill in from 1965 forward; scrub the timeline or hit "Show all" to see the whole picture at once. **Hover** a district for its name, year and size; **click** it to pin the panel and open its LPC designation report and Wikipedia page.

This map covers **only designated, currently active historic districts** — not individual landmarks, scenic landmarks, interior landmarks, or areas that were merely proposed, calendared, denied or overturned.

## The count — and why it isn't a round number

This is the one number that deserves a careful footnote.

- The map draws the **141 distinct historic-district areas** in the LPC's current mapping layer (`skyk-mpzq`), declared between **Nov. 23, 1965** (Brooklyn Heights, the first) and **Nov. 25, 2025**. By borough: **Manhattan 70, Brooklyn 42, Queens 13, The Bronx 13, Staten Island 3**.
- **The LPC's own headline count is higher.** The commission has cited roughly **150 historic districts** (per its 2024 materials) and **159 "historic districts and extensions"** (late 2025, after two new Flatbush districts). The gap is a **counting convention**, not missing data: the LPC tallies each designation *action* separately, while its mapping layer folds many later **extensions** back into the parent district's single boundary. So 141 is the number of separate shapes on this map, not a claim about the LPC's official total.
- **13** of the 141 do appear as their own shapes and dates (where the layer keeps an extension separate — e.g. Greenwich Village's 2006 extension, Cobble Hill's 1988 extension). Others (e.g. Park Slope's 2012 extension, the Upper East Side's) are merged into the parent boundary, which then carries the **original** designation year.

## Acres landmarked

- **≈ 4,179 acres — about 6.5 square miles** across all 141 districts (roughly eight Central Parks).
- Computed as the planar area of each boundary polygon via the shoelace formula on the **source State Plane coordinates (EPSG:2263, US survey feet)**, converted at **43,560 sq ft per acre**. This was cross-checked against the LPC dataset's own `shape_area` field and matches to **within 0.01%**.
- Extensions do not overlap their parent districts, so summing areas does not double-count.

## Source

- **Boundaries, designation dates, district names, borough, extension flag and LP number:** LPC *Historic Districts* dataset on NYC Open Data, dataset id **`skyk-mpzq`** ([page](https://data.cityofnewyork.us/Housing-Development/Historic-Districts-Map-/xbvj-gfnw)). Pulled via the keyless GeoJSON export endpoint `https://data.cityofnewyork.us/resource/skyk-mpzq.geojson`.
- **Designation reports:** the "Read the designation report" link on each district opens the LPC's official PDF at `https://s-media.nyc.gov/agencies/lpc/lp/{NNNN}.pdf`, where `NNNN` is the district's LP number, zero-padded to four digits (LP-00489 → `0489.pdf`). This pattern was spot-checked against several districts across boroughs and decades.
- **Base map tiles:** © OpenStreetMap contributors, © CARTO (dark base map, tinted warm in CSS).

## How it was processed

Everything is reproducible with `build.py` (requires `pyproj`):

1. **Filter.** Keep records where `status_of_ = "DESIGNATED"` and `current_ = "Yes"` and a designation date exists. The export already returns exactly the 141 active designated districts.
2. **Reproject.** The raw `the_geom` in this dataset is in **NY State Plane Long Island, US feet (EPSG:2263)** — *not* lat/lng. Each ring is transformed to **WGS84 (EPSG:4326)** with `pyproj` so it maps correctly in Leaflet. (Skipping this step was the one real gotcha: unprojected coordinates collapse to a single point.)
3. **Measure.** Compute each district's acreage from the State Plane rings *before* reprojection (shoelace area, holes subtracted; ÷ 43,560).
4. **Round** coordinates to five decimal places (~1 m) to shrink the file.
5. **Bucket** each district into a decade era (1965–1969, 1970s … 2020s) for coloring, using the four-digit designation year.
6. **Sort** features by designation date so the animation reveals them chronologically.

Output: `districts.json`, a single WGS84 GeoJSON FeatureCollection (~440 KB).

## Notes and caveats

- The **designation date** shown is the day the commission voted to designate the district.
- Boundary polygons are derived by the LPC primarily from Department of City Planning tax-lot data and are simplified slightly here for the web; they are indicative, not survey-grade.
- A handful of designations have complicated histories (amended, re-designated, partially overturned). This map reflects the boundary the LPC currently marks as active (`current_ = "Yes"`), which can differ from the original action.
- The LPC periodically designates new districts. Re-run `python3 build.py --fetch` to refresh against the live dataset; the total and the newest year will update automatically.

## Fact-check (July 2026)

Claims on the map, and how each was verified:

| Claim | Status | Basis |
|---|---|---|
| Brooklyn Heights was the **first** historic district, **Nov. 23, 1965** | ✅ | LPC dataset `desdate`; corroborated by the LPC/Wikipedia summary ("the first landmark district, the Brooklyn Heights Historic District, was designated in November 1965"). |
| "**about seven months** after the Landmarks Law of April 1965" | ✅ (corrected) | Landmarks Law passed the City Council April 7, 1965 and signed by Mayor Wagner that month → to Nov. 23 is ~7 months. (An earlier draft said "roughly six months.") |
| **141** mapped district areas; borough split 70/42/13/13/3 | ✅ | Direct count of the LPC boundary layer. Framed as mapped areas, **not** the LPC's official total. |
| LPC total is **~150 / 159** districts-and-extensions | ✅ | LPC 2024 materials (≈150) and Nov. 2025 designation announcement (159 "historic districts and extensions"). The 141-vs-159 gap is explained above. |
| **≈ 4,179 acres / 6.5 sq mi** total | ✅ | Computed from polygons; matches the dataset's `shape_area` to <0.01%. |
| Greenwich Village designated **April 29, 1969** (LP-00489) | ✅ | LPC dataset; report PDF resolves at the s-media LP path. |
| Latest districts: **Beverley Square West & Ditmas Park West, Nov. 25, 2025** | ✅ | LPC dataset; corroborated by Nov. 2025 press coverage of the two new Flatbush districts. |

Sources for the LPC's own counts: the commission's [Wikipedia summary](https://en.wikipedia.org/wiki/New_York_City_Landmarks_Preservation_Commission) and its 2025 designation announcements. "Wikipedia" links in the app run a title search for each district name (they always resolve; a small number of smaller districts may not have a dedicated article).

## A note on AI

This map was built with the help of AI. The underlying data is straight from the city's Landmarks Preservation Commission, but the processing and code have not been exhaustively hand-audited. Check any figure against the source dataset before relying on it.
