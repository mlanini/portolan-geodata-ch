# swissTLMRegio — Generalized Topographic Model

> Part of the [geodata.ch](../../README.md) cloud-native catalog of Swiss federal geodata. Agents: see [AGENTS.md](./AGENTS.md).

swissTLMRegio is the small-scale (≈1:200,000) generalized derivative of swissTLM3D, covering Switzerland and neighbouring regions. It suits country-wide overview maps and analyses that do not need full TLM detail.

**Coverage.** Country-wide generalized topography at reference scale ~1:200,000.

**Source.** Produced by Federal Office of Topography swisstopo and mirrored here in cloud-native form. The authoritative copy and the original downloads live at the [source product page](https://www.swisstopo.admin.ch/en/landscape-model-swisstlmregio); its machine metadata is the [source STAC collection](https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.swisstlmregio).

**License.** `other` — [swisstopo — free geodata, free use with source citation](https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata).

## Quick start

```python
import duckdb
con = duckdb.connect()
con.sql("INSTALL spatial; LOAD spatial;")
df = con.sql("SELECT * FROM read_parquet('https://ch-geodata.s3.eu-central-2.amazonaws.com/topography/swisstlmregio/swisstlmregio.parquet') LIMIT 100").df()
```

## Original source formats

geodata.ch mirrors this dataset from the authoritative swisstopo/BFS downloads. The originals remain the reference copy:

| Format | Media type | Title |
| --- | --- | --- |
| FileGDB | `application/x-filegdb` | swissTLMRegio (File Geodatabase) |
| GeoPackage | `application/geopackage+sqlite3` | swissTLMRegio (GeoPackage) |
| INTERLIS/XTF | `application/interlis+xml` | swissTLMRegio (INTERLIS 2, XTF) |

Concrete per-release download URLs are resolved from the source STAC by the [build pipeline](../../tools/README.md); see also [docs/data-sources.md](../../docs/data-sources.md).

## Schema

| Column | Type | Description |
| --- | --- | --- |
| `objektart` | string | Generalized feature class code. |
| `name` | string | Feature name where carried (e.g. main roads, rivers). |
| `geometry` | binary | Generalized geometry as WKB, EPSG:4326. |

## Coordinate reference system

- Source CRS: EPSG:2056 (CH1903+ / LV95)
- Published CRS: EPSG:4326 (WGS84)

## Suggested uses

- Small-scale overview and print maps of Switzerland.
- Fast national-extent analyses where full TLM detail is unnecessary.

## Limitations and inappropriate uses

- Geometry is generalized: do not use for local measurement or precise overlay against large-scale data.

## Definitions

- Feature classes are a generalized subset of the swissTLM3D object catalogue.

## Temporal note

Annual update; interval start indicative.

---

_This page is generated from `tools/manifest/datasets.yaml`. Edit the manifest, not this file._
