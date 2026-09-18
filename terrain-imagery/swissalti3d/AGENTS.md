# AGENTS.md — swissALTI3D — High-Resolution Digital Terrain Model

## What this is and how it connects

Bare-earth DTM COG tiles, one STAC item per tile. Read the item mirror to query all tiles at once.

**Keys.** n/a (raster). Each scene item carries its own footprint and acquisition datetime.

## Access

- Base URL: `https://ch-geodata.s3.eu-north-1.amazonaws.com/terrain-imagery/swissalti3d/`
- S3: `s3://ch-geodata/terrain-imagery/swissalti3d/`
- CRS: EPSG:2056 (CH1903+ / LV95) COG tiles (source EPSG:2056 (CH1903+ / LV95), LN02 heights).

## Runnable access patterns

**Load a tile with rioxarray**

```python
import rioxarray as rxr; da = rxr.open_rasterio('COG_TILE_URL')
```

## Quirks and caveats

- Tiles are in EPSG:2056 (metres); reproject on read if you need WGS84.
- Elevation is bare earth — do not expect building/vegetation heights.

## Provenance

Mirror of Federal Office of Topography swisstopo data. Source: https://www.swisstopo.admin.ch/en/height-model-swissalti3d . Source STAC: https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.swissalti3d .

_Generated from `tools/manifest/datasets.yaml`._
