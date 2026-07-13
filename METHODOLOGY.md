# The landmarking of New York — methodology

An animated map of every New York City historic district and the year it was declared, from Brooklyn Heights in 1965 to today.

## What it shows

Each shape is a **historic district** designated by the New York City Landmarks Preservation Commission (LPC). Districts appear on the map in the order they were declared and are colored by the decade of designation. Press play to watch the map fill in from 1965 forward; scrub the timeline or hit "Show all" to see the whole picture at once.

This map counts **only designated, currently active historic districts** — not individual landmarks, scenic landmarks, interior landmarks, or areas that were merely proposed, calendared, denied or overturned.

## The count

- **141 districts**, declared between **Nov. 23, 1965** (Brooklyn Heights, the first, roughly six months after the Landmarks Law took effect) and **Nov. 25, 2025**.
- By borough: **Manhattan 70, Brooklyn 42, Queens 13, The Bronx 13, Staten Island 3**.
- **13** of the 141 are **extensions** of an earlier district. Each extension carries its own, later designation date and is mapped and dated on its own — so, for example, an original district and its later extension light up in different years.

## Source

- **Boundaries, designation dates, district names, borough, extension flag and LP number:** LPC *Historic Districts* dataset on NYC Open Data, dataset id **`skyk-mpzq`** ([page](https://data.cityofnewyork.us/Housing-Development/Historic-Districts-Map-/xbvj-gfnw)). Pulled via the keyless GeoJSON export endpoint `https://data.cityofnewyork.us/resource/skyk-mpzq.geojson`.
- **Designation reports:** the "Read the designation report" link on each district opens the LPC's official PDF at `https://s-media.nyc.gov/agencies/lpc/lp/{NNNN}.pdf`, where `NNNN` is the district's LP number, zero-padded to four digits (LP-00489 → `0489.pdf`). This pattern was spot-checked against several districts across boroughs and decades.
- **Base map tiles:** © OpenStreetMap contributors, © CARTO (dark base map, tinted warm in CSS).

## How it was processed

Everything is reproducible with `build.py` (requires `pyproj`):

1. **Filter.** Keep records where `status_of_ = "DESIGNATED"` and `current_ = "Yes"` and a designation date exists. The export already returns exactly the 141 active designated districts.
2. **Reproject.** The raw `the_geom` in this dataset is in **NY State Plane Long Island, US feet (EPSG:2263)** — *not* lat/lng. Each ring is transformed to **WGS84 (EPSG:4326)** with `pyproj` so it maps correctly in Leaflet. (Skipping this step was the one real gotcha: unprojected coordinates collapse to a single point.)
3. **Round** coordinates to five decimal places (~1 m) to shrink the file.
4. **Bucket** each district into a decade era (1965–1969, 1970s … 2020s) for coloring, using the four-digit designation year.
5. **Sort** features by designation date so the animation reveals them chronologically.

Output: `districts.json`, a single WGS84 GeoJSON FeatureCollection (~440 KB).

## Notes and caveats

- The **designation date** shown is the day the commission voted to designate the district.
- Boundary polygons are derived by the LPC primarily from Department of City Planning tax-lot data and are simplified slightly here for the web; they are indicative, not survey-grade.
- A handful of designations have complicated histories (amended, re-designated, partially overturned). This map reflects the boundary the LPC currently marks as active (`current_ = "Yes"`), which can differ from the original action.
- The LPC periodically designates new districts. Re-run `python3 build.py --fetch` to refresh against the live dataset; the total and the newest year will update automatically.

## A note on AI

This map was built with the help of AI. The underlying data is straight from the city's Landmarks Preservation Commission, but the processing and code have not been exhaustively hand-audited. Check any figure against the source dataset before relying on it.
