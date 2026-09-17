# swissALTI3D — High-Resolution Digital Terrain Model

> Part of the [geodata.ch](../../README.md) cloud-native catalog of Swiss federal geodata. Agents: see [AGENTS.md](./AGENTS.md).

swissALTI3D is the high-precision digital terrain model of Switzerland, describing the bare-earth surface without vegetation or buildings at 0.5 m resolution in populated areas. Republished as a Cloud-Optimized GeoTIFF scene collection, one item per tile.

**Coverage.** Nationwide 0.5 m bare-earth DTM (2 m variant also offered by the source), tiled at 1 km.

**Source.** Produced by Federal Office of Topography swisstopo and mirrored here in cloud-native form. The authoritative copy and the original downloads live at the [source product page](https://www.swisstopo.admin.ch/en/height-model-swissalti3d); its machine metadata is the [source STAC collection](https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.swissalti3d).

**License.** `other` — [swisstopo — free geodata, free use with source citation](https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata).

## Quick start

```python
# Query every scene from the STAC-GeoParquet item mirror, then open a tile.
import duckdb, rioxarray as rxr
con = duckdb.connect(); con.sql('INSTALL spatial; LOAD spatial;')
items = con.sql("SELECT id, assets FROM read_parquet('https://ch-geodata.s3.eu-north-1.amazonaws.com/terrain-imagery/swissalti3d/items.parquet') LIMIT 10").df()
# da = rxr.open_rasterio(<cog url from items.assets>)
```

## Original source formats

geodata.ch mirrors this dataset from the authoritative swisstopo/BFS downloads. The originals remain the reference copy:

| Format | Media type | Title |
| --- | --- | --- |
| GeoTIFF | `image/tiff; application=geotiff` | swissALTI3D (GeoTIFF tiles, 0.5 m / 2 m) |
| XYZ | `text/plain` | swissALTI3D (XYZ ASCII grid) |

Concrete per-release download URLs are resolved from the source STAC by the [build pipeline](../../tools/README.md); see also [docs/data-sources.md](../../docs/data-sources.md).

## Coordinate reference system

- Source CRS: EPSG:2056 (CH1903+ / LV95), LN02 heights
- Published CRS: EPSG:2056 (CH1903+ / LV95) COG tiles

## Suggested uses

- Hydrological modelling, slope/aspect and hillshade generation, line-of-sight analysis.
- Terrain correction and normalization of other rasters.

## Limitations and inappropriate uses

- swissALTI3D is a terrain (bare-earth) model: it excludes vegetation and buildings — use a surface model (DSM) for those.
- Acquisition dates vary by region; a national mosaic mixes vintages.

## Definitions

- DTM = digital terrain model (bare earth), distinct from a DSM (digital surface model).

## Temporal note

Rolling acquisition by region on a ~6-year cycle; interval start indicative.

---

_This page is generated from `tools/manifest/datasets.yaml`. Edit the manifest, not this file._
