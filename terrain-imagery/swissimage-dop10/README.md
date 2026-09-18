# SWISSIMAGE 10 cm — Digital Orthophoto

> Part of the [geodata.ch](../../README.md) cloud-native catalog of Swiss federal geodata. Agents: see [AGENTS.md](./AGENTS.md).

SWISSIMAGE 10 cm (DOP10) is the seamless orthorectified aerial-image mosaic of Switzerland at 10 cm ground resolution in the lowlands. Republished as a Cloud-Optimized GeoTIFF scene collection, one item per tile.

**Coverage.** Nationwide RGB orthophoto at 10 cm (lowlands) / 25 cm (alpine), on a rolling 3-year update.

**Source.** Produced by Federal Office of Topography swisstopo and mirrored here in cloud-native form. The authoritative copy and the original downloads live at the [source product page](https://www.swisstopo.admin.ch/en/orthoimage-swissimage-10); its machine metadata is the [source STAC collection](https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.swissimage-dop10).

**License.** `other` — [swisstopo — free geodata, free use with source citation](https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata).

## Quick start

```python
# Query every scene from the STAC-GeoParquet item mirror, then open a tile.
import duckdb, rioxarray as rxr
con = duckdb.connect(); con.sql('INSTALL spatial; LOAD spatial;')
items = con.sql("SELECT id, assets FROM read_parquet('https://ch-geodata.s3.eu-north-1.amazonaws.com/terrain-imagery/swissimage-dop10/items.parquet') LIMIT 10").df()
# da = rxr.open_rasterio(<cog url from items.assets>)
```

## Original source formats

geodata.ch mirrors this dataset from the authoritative swisstopo/BFS downloads. The originals remain the reference copy:

| Format | Media type | Title |
| --- | --- | --- |
| GeoTIFF (COG) | `image/tiff; application=geotiff; profile=cloud-optimized` | SWISSIMAGE 10 cm (Cloud-Optimized GeoTIFF tiles) |

Concrete per-release download URLs are resolved from the source STAC by the [build pipeline](../../tools/README.md); see also [docs/data-sources.md](../../docs/data-sources.md).

## Coordinate reference system

- Source CRS: EPSG:2056 (CH1903+ / LV95)
- Published CRS: EPSG:2056 (CH1903+ / LV95) COG tiles

## Suggested uses

- Visual basemap and photo-interpretation backdrop.
- Training data and validation imagery for computer-vision workflows.

## Limitations and inappropriate uses

- Tiles are flown across different years; colour and season differ between neighbouring tiles in a national mosaic.
- Orthophotos are 2D imagery, not elevation — pair with swissALTI3D for terrain.

## Definitions

- DOP10 = Digitales OrthoPhoto at 10 cm resolution.

## Temporal note

Rolling 3-year national coverage; interval start indicative.

---

_This page is generated from `tools/manifest/datasets.yaml`. Edit the manifest, not this file._
