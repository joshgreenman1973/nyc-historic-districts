# The landmarking of New York: methodology

An animated map of every New York City historic district and the year it was declared, from Brooklyn Heights in 1965 to today.

## Scope

Each shape is a historic district designated by the New York City Landmarks Preservation Commission (LPC). The commission's [landmark types and criteria page](https://www.nyc.gov/site/lpc/designations/landmark-types-criteria.page) explains what a historic district is, and its [About LPC page](https://www.nyc.gov/site/lpc/about/about-lpc.page) covers what designation means and the history of the 1965 Landmarks Law.

Districts appear on the map in the order they were declared, colored by the decade of designation, and a running acreage total climbs as each one lights up. Press play to watch the map fill in from 1965 forward. Drag along the timeline to move through the years, or press "Show all" to see every district at once. Hover over a district (or tap it on a phone) for its name, date and size, with links to its LPC designation report and a Wikipedia search.

The map covers only designated, currently active historic districts and extensions. It leaves out individual landmarks, interior landmarks, scenic landmarks and areas that were proposed, calendared, denied or overturned.

## Count

- 159 historic districts and extensions, declared between Nov. 23, 1965 (Brooklyn Heights, the first) and Nov. 25, 2025 (Beverley Square West and Ditmas Park West, in Flatbush). The LPC's own count at the end of 2025 was also 159.
- By borough: Manhattan 82, Brooklyn 47, Queens 14, the Bronx 13, Staten Island 3.
- 25 of the 159 are extensions of an earlier district. Each extension has its own, later designation date and is drawn as its own shape, so a district and its extensions light up in different years.

### Earlier version: 141 records

The first version of this project used New York City Open Data's Historic Districts dataset (`skyk-mpzq`), which had 141 records when last checked on Nov. 11, 2026. Matching LP numbers against the LPC's mapping layer, 18 of the 159 have no separate record in that dataset: 12 extensions and six other districts (Carnegie Hill, Murray Hill, Douglaston Hill, East Village/Lower East Side, Vinegar Hill and Dorrance Brooks Square). An earlier version of this note said all 18 were extensions. This version uses the LPC layer, where every district and extension is a separate, dated record.

## Sources

- **District data.** Boundaries, designation dates, names, borough, extension flag, LP number and report links come from the LPC's own ArcGIS mapping service, layer `Historic_Districts_LPC` on `services5.arcgis.com/Oos4pNA2538iVFA1`. The same data runs the commission's [Discover NYC Landmarks](https://www.landmarks.nyc/) map, linked from the LPC [maps page](https://www.nyc.gov/site/lpc/designations/maps.page). Query filter: `STATUS_OF_ = 'DESIGNATED' AND CURRENT_ = 'Yes'` (159 records).
- **Snapshot date.** The page shows a saved copy of that layer. The current copy was retrieved Nov. 11, 2026; the LPC last edited the layer on Dec. 4, 2025. Both dates are stored in `districts.json` (`meta.retrieved`, `meta.layer_edited`) and shown on the page.
- **Borough land boundaries.** Department of City Planning (DCP) Borough Boundaries, water areas excluded ([New York City Open Data `gthc-hcne`](https://data.cityofnewyork.us/d/gthc-hcne), version 26c), saved in `data/borough_boundaries.geojson`.
- **Designation reports.** Each district's `Report_URL` from the LPC layer, the commission's PDF at s-media.nyc.gov, switched to HTTPS. All 159 links opened on Nov. 11, 2026.
- **Wikipedia links** run a title search for the district name.
- **Base map tiles.** © OpenStreetMap contributors, © CARTO (dark base map, tinted warm in CSS).

## Processing

`build.py` reproduces everything. It needs the Python packages `pyproj` and `shapely`.

1. **Fetch** the 159 designated, current districts from the LPC layer as GeoJSON, in longitude and latitude (`outSR=4326`), along with the layer's last-edit date and the DCP borough boundaries.
2. **Convert dates.** `DESIG_DATE` arrives as milliseconds since 1970 and is converted to a calendar date. Checked against known designations: Brooklyn Heights, 1965‑11‑23; Greenwich Village, 1969‑04‑29.
3. **Measure area.** Each district's acreage (`acres`) is the area of its boundary measured on the curved surface of the earth, using the standard WGS84 model (`pyproj.Geod`), with holes subtracted and converted at 4,046.856 square meters per acre.
4. **Remove overlap and water.** In designation order, each district gets `net`, the ground it adds that no earlier district covers, and `netLand`, the same area clipped to the DCP land boundary.
5. **Round** coordinates to five decimal places (about one meter) to shrink the file.
6. **Group** each district into a decade (1965–1969, 1970s through 2020s) for coloring, and sort by designation date.
7. **Write summary figures** to `meta` in `districts.json`: retrieval and layer-edit dates, count, extensions, first and last designations, summed acres, acres with overlap removed, the same on land only, and each borough's land acres.

The output, `districts.json`, is a single GeoJSON file with 159 features, about 520 KB.

## Acres landmarked

- The running counter counts each piece of ground once by adding each district's `net` area. At full extent that is about 4,557 acres, or 7.1 square miles, a little more than five times the size of Central Park (843 acres).
- A few older districts sit partly inside larger ones: Carnegie Hill within the Expanded Carnegie Hill district, and two small Central Park West blocks within the Upper West Side/Central Park West district. Adding up every district's full area, with those overlaps counted twice, gives about 4,574 acres, 16 acres (0.36%) more. An earlier version of the page put the summed figure in the counter under the label "acres landmarked," which overstated the ground covered by those 16 acres.
- The size shown when you hover over a single district is that district's full area.
- Overlap was measured with a polygon union (`shapely`). Only those three pairs overlap by more than half an acre.

## Share of each borough landmarked

The borough chips show the percentage of each borough's land that sits inside a historic district.

- **Numerator.** Each borough's district area using `netLand`: overlapping districts count once, and the shapes are clipped to the DCP land boundary. Clipping removes about 18 acres of water, almost all of it in the Douglaston (11 acres) and South Street Seaport (5 acres) districts. Added up over the districts shown at any point in the animation, it equals the land covered at that moment, so the percentage climbs correctly as districts appear.
- **Denominator.** Each borough's land area from the same DCP boundary, so both parts of the fraction use one definition of land. An earlier version divided unclipped district shapes by rounded 2020 Census land areas.
- **Result at full extent:** Manhattan 12.3%, Brooklyn 3.2%, Staten Island 1.1%, Queens 1.0%, the Bronx 1.0%; citywide 2.3%. The page computes these from the data and rounds to one decimal place. The change in method moved Manhattan from 12.4% to 12.3% and the citywide figure from 2.4% to 2.3%.

## Notes and caveats

- The designation date is the day the commission voted to designate each area.
- The LPC draws its boundary shapes mainly from DCP tax-lot data, and this map rounds their coordinates for the web. They are approximate; the designation reports give the legal boundaries.
- Some designations have complicated histories (amended, re-designated, partly overturned). This map reflects only the districts the LPC currently marks as designated and active.

## Refreshing the data

Run `python3 build.py --fetch`, then commit `districts.json`. The page reads its numbers from that file, so the counters, borough percentages, timeline end year, decade labels, retrieval date and the figures in the About panel all update. Two things need a hand edit after a rebuild: the `<meta name="description">` tag, which says 159, and the sentence "The commission's own count at the end of 2025 was also 159." The figures in this methodology file are also written by hand.

## Fact-check (July 2026, revised Nov. 2026)

| Claim | Status | Basis |
|---|---|---|
| Brooklyn Heights was the first historic district, Nov. 23, 1965 | ✅ | LPC layer `DESIG_DATE`; LPC and Wikipedia both date the first district to November 1965. |
| "About seven months" after the Landmarks Law of April 1965 | ✅ | The City Council passed the law April 7, 1965, and Mayor Robert F. Wagner signed it that month; Nov. 23 is about seven months later. |
| 159 historic districts and extensions; borough split 82/47/14/13/3 | ✅ | Count of the LPC's `Historic_Districts_LPC` layer; the commission's year-end 2025 release also says 159. |
| 25 are extensions | ✅ | `EXTENSION = 'Yes'` in the LPC layer. |
| About 4,557 acres (7.1 square miles) with overlap removed; 4,574 summed | ✅ | Measured area of every boundary; overlap measured with a polygon union (16 acres across three pairs). Reproduced in an outside review, Nov. 2026 (4,557.36 and 4,573.67). |
| Greenwich Village designated April 29, 1969 (LP‑00489) | ✅ | LPC layer; the designation report PDF opens. |
| Newest districts: Beverley Square West and Ditmas Park West, Nov. 25, 2025 | ✅ | LPC layer; Nov. 2025 press coverage of the two Flatbush districts. LPC press releases list no new historic districts in 2026 through October. |
| A little more than five Central Parks | ✅ (corrected) | 4,557 ÷ 843 = 5.4. Earlier copy said "roughly eight." |
| Open Data's 141 records lack 12 extensions and six other districts | ✅ (corrected) | LP-number match against the LPC layer, Nov. 11, 2026. Earlier copy said "about 18 extensions." |
| Borough shares: Manhattan 12.3%, citywide 2.3% | ✅ (revised) | District area on land ÷ borough land, both from DCP boundaries with water excluded. |

## Use of AI

This map was built with the help of AI. The data comes directly from the Landmarks Preservation Commission, but the processing and code have not been fully checked by hand. Check any figure against the source before relying on it.
