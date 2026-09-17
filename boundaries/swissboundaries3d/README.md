# swissBOUNDARIES3D — Administrative Boundaries

> Part of the [geodata.ch](../../README.md) cloud-native catalog of Swiss federal geodata. Agents: see [AGENTS.md](./AGENTS.md).

swissBOUNDARIES3D holds the administrative boundaries of Switzerland at four levels — country, canton, district, and municipality — with the official BFS municipality numbers. It is the authoritative boundary reference for the country.

**Coverage.** 26 cantons and ~2,130 municipalities (the municipality count falls over time as communes merge).

**Source.** Produced by Federal Office of Topography swisstopo and mirrored here in cloud-native form. The authoritative copy and the original downloads live at the [source product page](https://www.swisstopo.admin.ch/en/landscape-model-swissboundaries3d); its machine metadata is the [source STAC collection](https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.swissboundaries3d).

**License.** `other` — [swisstopo — free geodata, free use with source citation](https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata).

## Quick start

```python
import duckdb
con = duckdb.connect()
con.sql("INSTALL spatial; LOAD spatial;")
df = con.sql("SELECT * FROM read_parquet('https://ch-geodata.s3.eu-central-2.amazonaws.com/boundaries/swissboundaries3d/swissboundaries3d.parquet') LIMIT 100").df()
```

## Original source formats

geodata.ch mirrors this dataset from the authoritative swisstopo/BFS downloads. The originals remain the reference copy:

| Format | Media type | Title |
| --- | --- | --- |
| FileGDB | `application/x-filegdb` | swissBOUNDARIES3D (File Geodatabase) |
| GeoPackage | `application/geopackage+sqlite3` | swissBOUNDARIES3D (GeoPackage) |
| Shapefile | `application/x-shapefile` | swissBOUNDARIES3D (Shapefile) |
| INTERLIS/XTF | `application/interlis+xml` | swissBOUNDARIES3D (INTERLIS 2, XTF) |

Concrete per-release download URLs are resolved from the source STAC by the [build pipeline](../../tools/README.md); see also [docs/data-sources.md](../../docs/data-sources.md).

## Schema

| Column | Type | Description |
| --- | --- | --- |
| `bfs_nummer` | int | Official BFS municipality number — the national join key to municipal statistics. |
| `name` | string | Official municipality name. |
| `kanton` | string | Canton abbreviation (e.g. BE, ZH, VD). |
| `bezirk` | string | District name. |
| `einwohnerz` | int | Resident population figure carried by the boundary edition, where present. |
| `geometry` | binary | Boundary polygon as WKB, EPSG:4326. |

## Coordinate reference system

- Source CRS: EPSG:2056 (CH1903+ / LV95)
- Published CRS: EPSG:4326 (WGS84)

## Suggested uses

- Aggregating any point/area data to municipality, district, or canton.
- Choropleth mapping keyed by BFS number.

## Limitations and inappropriate uses

- Municipality numbers and geometries change over time; always pair an analysis with the boundary edition's date.

## Definitions

- The BFS number is the Federal Statistical Office municipality identifier; it is the backbone key of Swiss official statistics.

## Temporal note

Updated up to several times per year as municipalities merge; interval start indicative.

---

_This page is generated from `tools/manifest/datasets.yaml`. Edit the manifest, not this file._
