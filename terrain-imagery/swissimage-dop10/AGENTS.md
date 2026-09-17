# AGENTS.md — SWISSIMAGE 10 cm — Digital Orthophoto

## What this is and how it connects

RGB orthophoto COG tiles, one STAC item per tile, already cloud-optimized at the source.

**Keys.** n/a (raster). Each scene item carries footprint and acquisition datetime.

## Access

- Base URL: `https://ch-geodata.s3.eu-central-2.amazonaws.com/terrain-imagery/swissimage-dop10/`
- S3: `s3://ch-geodata/terrain-imagery/swissimage-dop10/`
- CRS: EPSG:2056 (CH1903+ / LV95) COG tiles (source EPSG:2056 (CH1903+ / LV95)).

## Runnable access patterns

**Load one tile with rioxarray**

```python
import rioxarray as rxr; da = rxr.open_rasterio('COG_TILE_URL')
```

## Quirks and caveats

- Neighbouring tiles can differ in acquisition year and season; filter items by datetime for a consistent mosaic.
- Source tiles are already valid COGs — geodata.ch mirrors them and may re-tile for consistency.

## Provenance

Mirror of Federal Office of Topography swisstopo data. Source: https://www.swisstopo.admin.ch/en/orthoimage-swissimage-10 . Source STAC: https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.swissimage-dop10 .

_Generated from `tools/manifest/datasets.yaml`._
