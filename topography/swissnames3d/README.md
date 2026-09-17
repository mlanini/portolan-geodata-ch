# swissNAMES3D — Geographical Names

> Part of the [geodata.ch](../../README.md) cloud-native catalog of Swiss federal geodata. Agents: see [AGENTS.md](./AGENTS.md).

swissNAMES3D is the complete set of geographical names of Switzerland: settlements, terrain features, waters, and named objects, each as a 3D point, line, or polygon. It is the authoritative gazetteer for the country.

**Coverage.** Several hundred thousand named features across all four national languages.

**Source.** Produced by Federal Office of Topography swisstopo and mirrored here in cloud-native form. The authoritative copy and the original downloads live at the [source product page](https://www.swisstopo.admin.ch/en/geographical-names-swissnames3d); its machine metadata is the [source STAC collection](https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.swissnames3d).

**License.** `other` — [swisstopo — free geodata, free use with source citation](https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata).

## Quick start

```python
import duckdb
con = duckdb.connect()
con.sql("INSTALL spatial; LOAD spatial;")
df = con.sql("SELECT * FROM read_parquet('https://ch-geodata.s3.eu-north-1.amazonaws.com/topography/swissnames3d/swissnames3d.parquet') LIMIT 100").df()
```

## Original source formats

geodata.ch mirrors this dataset from the authoritative swisstopo/BFS downloads. The originals remain the reference copy:

| Format | Media type | Title |
| --- | --- | --- |
| GeoPackage | `application/geopackage+sqlite3` | swissNAMES3D (GeoPackage) |
| INTERLIS/XTF | `application/interlis+xml` | swissNAMES3D (INTERLIS 2, XTF) |
| CSV | `text/csv` | swissNAMES3D (CSV, point names) |

Concrete per-release download URLs are resolved from the source STAC by the [build pipeline](../../tools/README.md); see also [docs/data-sources.md](../../docs/data-sources.md).

## Schema

| Column | Type | Description |
| --- | --- | --- |
| `uuid` | string | Stable identifier of the named feature. |
| `name` | string | Official geographical name. |
| `objektart` | string | Feature category (e.g. Ortschaft, Gipfel, Fluss). |
| `sprachcode` | string | Language of the name (de/fr/it/rm). |
| `geometry` | binary | Feature geometry as WKB, EPSG:4326. |

## Coordinate reference system

- Source CRS: EPSG:2056 (CH1903+ / LV95)
- Published CRS: EPSG:4326 (WGS84)

## Suggested uses

- Geocoding and map labelling.
- Linking place names in text to coordinates.

## Limitations and inappropriate uses

- Names are multilingual and region-dependent; a feature may carry different names per language.

## Definitions

- 'objektart' categorizes the named feature; 'sprachcode' gives the language of the specific name record.

## Temporal note

Continuous maintenance; interval start indicative.

---

_This page is generated from `tools/manifest/datasets.yaml`. Edit the manifest, not this file._
