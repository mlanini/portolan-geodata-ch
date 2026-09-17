# swissBUILDINGS3D — 3D Building Models

> Part of the [geodata.ch](../../README.md) cloud-native catalog of Swiss federal geodata. Agents: see [AGENTS.md](./AGENTS.md).

swissBUILDINGS3D contains the buildings of Switzerland as 3D models with roof shapes, derived from the swisstopo stereo-photogrammetric workflow and the cadastral footprint. Republished as 2D footprints in GeoParquet with the full 3D model available from the source.

**Coverage.** Millions of building models covering Switzerland, updated region by region.

**Source.** Produced by Federal Office of Topography swisstopo and mirrored here in cloud-native form. The authoritative copy and the original downloads live at the [source product page](https://www.swisstopo.admin.ch/en/landscape-model-swissbuildings3d-3-0); its machine metadata is the [source STAC collection](https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.swissbuildings3d_3_0).

**License.** `other` — [swisstopo — free geodata, free use with source citation](https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata).

## Quick start

```python
import duckdb
con = duckdb.connect()
con.sql("INSTALL spatial; LOAD spatial;")
df = con.sql("SELECT * FROM read_parquet('https://ch-geodata.s3.eu-central-2.amazonaws.com/topography/swissbuildings3d/swissbuildings3d.parquet') LIMIT 100").df()
```

## Original source formats

geodata.ch mirrors this dataset from the authoritative swisstopo/BFS downloads. The originals remain the reference copy:

| Format | Media type | Title |
| --- | --- | --- |
| FileGDB | `application/x-filegdb` | swissBUILDINGS3D 3.0 (File Geodatabase, 3D) |
| INTERLIS/XTF | `application/interlis+xml` | swissBUILDINGS3D 3.0 (INTERLIS 2, XTF) |
| Citygml | `application/citygml+xml` | swissBUILDINGS3D (CityGML, where offered) |

Concrete per-release download URLs are resolved from the source STAC by the [build pipeline](../../tools/README.md); see also [docs/data-sources.md](../../docs/data-sources.md).

## Schema

| Column | Type | Description |
| --- | --- | --- |
| `uuid` | string | Stable building object identifier. |
| `egid` | string | Federal building identifier (EGID) where linked; joins to the building & dwelling register. |
| `dachtyp` | string | Roof type classification. |
| `geometry` | binary | 2D building footprint as WKB, EPSG:4326 (full 3D model in the source). |

## Coordinate reference system

- Source CRS: EPSG:2056 (CH1903+ / LV95), LN02 heights
- Published CRS: EPSG:4326 (WGS84), 2D footprints

## Suggested uses

- Urban analysis, solar-potential context, and 3D city visualization (via the source 3D model).
- Joining buildings to the building & dwelling register through EGID.

## Limitations and inappropriate uses

- Republished footprints are 2D; the roof geometry lives only in the source FileGDB/XTF/CityGML.
- swissBUILDINGS3D is a photogrammetric model, not a legal cadastral building layer.

## Definitions

- EGID is the federal building identifier maintained in the building & dwelling register (GWR).

## Temporal note

Rolling update by region; interval start indicative.

---

_This page is generated from `tools/manifest/datasets.yaml`. Edit the manifest, not this file._
