# VECTOR200 — Land Cover

> Part of the [geodata.ch](../../README.md) cloud-native catalog of Swiss federal geodata. Agents: see [AGENTS.md](./AGENTS.md).

The land-cover layer of VECTOR200, the vectorized national map at 1:200,000. Polygons classify the country into land-cover types (forest, settlement, water, glacier, and more) for national-scale thematic mapping.

**Coverage.** National land-cover polygons at reference scale 1:200,000.

**Source.** Produced by Federal Office of Topography swisstopo and mirrored here in cloud-native form. The authoritative copy and the original downloads live at the [source product page](https://www.swisstopo.admin.ch/en/landscape-model-vector200); its machine metadata is the [source STAC collection](https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.vec200-landcover).

**License.** `other` — [swisstopo — free geodata, free use with source citation](https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata).

## Quick start

```python
import duckdb
con = duckdb.connect()
con.sql("INSTALL spatial; LOAD spatial;")
df = con.sql("SELECT * FROM read_parquet('https://ch-geodata.s3.eu-central-2.amazonaws.com/topography/vec200-landcover/vec200-landcover.parquet') LIMIT 100").df()
```

## Original source formats

geodata.ch mirrors this dataset from the authoritative swisstopo/BFS downloads. The originals remain the reference copy:

| Format | Media type | Title |
| --- | --- | --- |
| FileGDB | `application/x-filegdb` | VECTOR200 (File Geodatabase) |
| GeoPackage | `application/geopackage+sqlite3` | VECTOR200 (GeoPackage) |
| Shapefile | `application/x-shapefile` | VECTOR200 land cover (Shapefile) |

Concrete per-release download URLs are resolved from the source STAC by the [build pipeline](../../tools/README.md); see also [docs/data-sources.md](../../docs/data-sources.md).

## Schema

| Column | Type | Description |
| --- | --- | --- |
| `objval` | string | Land-cover class code (e.g. Wald, Siedl, Fels). |
| `geometry` | binary | Land-cover polygon as WKB, EPSG:4326. |

## Coordinate reference system

- Source CRS: EPSG:2056 (CH1903+ / LV95)
- Published CRS: EPSG:4326 (WGS84)

## Suggested uses

- National land-cover context and cartographic backdrops.
- Coarse masking (e.g. forest vs. settlement) for national analyses.

## Limitations and inappropriate uses

- 1:200,000 generalization: unsuitable for parcel- or field-level land-cover work; use swissTLM3D land cover for detail.

## Definitions

- 'objval' codes follow the VECTOR200 land-cover classification.

## Temporal note

Periodic update; interval start indicative.

---

_This page is generated from `tools/manifest/datasets.yaml`. Edit the manifest, not this file._
