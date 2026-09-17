# Official Register of Localities with Postal Codes (PLZ)

> Part of the [geodata.ch](../../README.md) cloud-native catalog of Swiss federal geodata. Agents: see [AGENTS.md](./AGENTS.md).

The official directory of Swiss localities with their postal codes (PLZ), linking place names, postal codes, and municipalities. Published as GeoParquet with a PMTiles layer for the web.

**Coverage.** Every Swiss locality and its postal code, keyed to BFS municipality numbers.

**Source.** Produced by Federal Office of Topography swisstopo and mirrored here in cloud-native form. The authoritative copy and the original downloads live at the [source product page](https://www.swisstopo.admin.ch/en/official-directory-of-towns-and-cities); its machine metadata is the [source STAC collection](https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo-vd.ortschaftenverzeichnis_plz).

**License.** `other` — [swisstopo — free geodata, free use with source citation](https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata).

## Quick start

```python
import duckdb
con = duckdb.connect()
con.sql("INSTALL spatial; LOAD spatial;")
df = con.sql("SELECT * FROM read_parquet('https://ch-geodata.s3.eu-north-1.amazonaws.com/boundaries/ortschaftenverzeichnis-plz/ortschaftenverzeichnis-plz.parquet') LIMIT 100").df()
```

## Original source formats

geodata.ch mirrors this dataset from the authoritative swisstopo/BFS downloads. The originals remain the reference copy:

| Format | Media type | Title |
| --- | --- | --- |
| GeoPackage | `application/geopackage+sqlite3` | Ortschaftenverzeichnis PLZ (GeoPackage) |
| INTERLIS/XTF | `application/interlis+xml` | Ortschaftenverzeichnis PLZ (INTERLIS, XTF) |
| CSV | `text/csv` | Ortschaftenverzeichnis PLZ (CSV) |

Concrete per-release download URLs are resolved from the source STAC by the [build pipeline](../../tools/README.md); see also [docs/data-sources.md](../../docs/data-sources.md).

## Schema

| Column | Type | Description |
| --- | --- | --- |
| `plz` | int | Four-digit Swiss postal code. |
| `zusatzziffer` | int | PLZ addition digit distinguishing localities that share a postal code. |
| `ortschaftsname` | string | Official locality name. |
| `bfs_nummer` | int | BFS municipality number the locality belongs to — joins to swissboundaries3d. |
| `geometry` | binary | Locality point/area as WKB, EPSG:4326. |

## Coordinate reference system

- Source CRS: EPSG:2056 (CH1903+ / LV95)
- Published CRS: EPSG:4326 (WGS84)

## Suggested uses

- Resolving a postal code to a municipality or coordinate.
- Bridging postal-code-keyed business data to official municipal geography.

## Limitations and inappropriate uses

- PLZ areas are postal, not administrative; a postal code can straddle municipal boundaries — use bfs_nummer for administrative joins.

## Definitions

- PLZ + zusatzziffer together identify a postal locality uniquely.

## Temporal note

Regularly updated; interval start indicative.

---

_This page is generated from `tools/manifest/datasets.yaml`. Edit the manifest, not this file._
