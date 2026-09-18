# swissTLM3D — Topographic Landscape Model

> Part of the [geodata.ch](../../README.md) cloud-native catalog of Swiss federal geodata. Agents: see [AGENTS.md](./AGENTS.md).

swissTLM3D is the large-scale topographic landscape model of Switzerland: the most detailed and precise vector reference of roads, railways, buildings, watercourses, land cover, and more, with 3D geometry. Published here as a partitioned GeoParquet dataset per feature theme with PMTiles for the web.

**Coverage.** ~70 feature layers covering the whole of Switzerland and Liechtenstein at reference scale ~1:10,000.

**Source.** Produced by Federal Office of Topography swisstopo and mirrored here in cloud-native form. The authoritative copy and the original downloads live at the [source product page](https://www.swisstopo.admin.ch/en/landscape-model-swisstlm3d); its machine metadata is the [source STAC collection](https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.swisstlm3d).

**License.** `other` — [swisstopo — free geodata, free use with source citation](https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata).

## Quick start

```python
import duckdb
con = duckdb.connect()
con.sql("INSTALL spatial; LOAD spatial;")
df = con.sql("SELECT * FROM read_parquet('https://ch-geodata.s3.eu-north-1.amazonaws.com/topography/swisstlm3d/swisstlm3d.parquet') LIMIT 100").df()
```

## Original source formats

geodata.ch mirrors this dataset from the authoritative swisstopo/BFS downloads. The originals remain the reference copy:

| Format | Media type | Title |
| --- | --- | --- |
| FileGDB | `application/x-filegdb` | swissTLM3D (Esri File Geodatabase) |
| GeoPackage | `application/geopackage+sqlite3` | swissTLM3D (GeoPackage) |
| INTERLIS/XTF | `application/interlis+xml` | swissTLM3D (INTERLIS 2 transfer, XTF) |

Concrete per-release download URLs are resolved from the source STAC by the [build pipeline](../../tools/README.md); see also [docs/data-sources.md](../../docs/data-sources.md).

## Schema

| Column | Type | Description |
| --- | --- | --- |
| `objektart` | string | Feature class / object type code within the TLM theme. |
| `objektursprung` | string | Origin of the object (surveyed, derived, etc.). |
| `revision_jahr` | int | Year of last revision of the feature. |
| `geometry` | binary | Feature geometry as WKB, EPSG:4326 (3D collapsed to 2D in GeoParquet; Z retained in source). |

## Coordinate reference system

- Source CRS: EPSG:2056 (CH1903+ / LV95, with LN02 heights)
- Published CRS: EPSG:4326 (WGS84)

## Suggested uses

- Authoritative base map for cartography, routing, and hydrological network analysis.
- Reference geometry for snapping and conflating other vector datasets.

## Limitations and inappropriate uses

- swissTLM3D is a landscape model, not a cadastre: building footprints are generalized and are not legal parcel boundaries.
- Z values in the source are dropped in the 2D GeoParquet; use the source FileGDB/XTF when 3D geometry is required.

## Definitions

- 'objektart' codes follow the swissTLM3D data model; see the swisstopo object catalogue.

## Temporal note

Biannual update cycle; interval start is the first integrated release, indicative.

---

_This page is generated from `tools/manifest/datasets.yaml`. Edit the manifest, not this file._
