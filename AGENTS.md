# AGENTS.md — geodata.ch

Cloud-native mirror of Swiss federal geodata. Query the data directly from object storage; there is no server.

## Access

- HTTPS base: `https://ch-geodata.s3.eu-north-1.amazonaws.com`
- S3 base: `s3://ch-geodata`
- Root STAC: `https://ch-geodata.s3.eu-north-1.amazonaws.com/catalog.json`
- Vector and tabular data are GeoParquet/Parquet (query with DuckDB spatial or GeoPandas over HTTP range requests). Raster is Cloud-Optimized GeoTIFF with a STAC-GeoParquet item mirror per collection.

## Collections

- `topography/swisstlm3d` — swissTLM3D — Topographic Landscape Model (vector)
- `topography/swisstlmregio` — swissTLMRegio — Generalized Topographic Model (vector)
- `topography/swissnames3d` — swissNAMES3D — Geographical Names (vector)
- `topography/vec200-landcover` — VECTOR200 — Land Cover (vector)
- `topography/swissbuildings3d` — swissBUILDINGS3D — 3D Building Models (vector)
- `boundaries/swissboundaries3d` — swissBOUNDARIES3D — Administrative Boundaries (vector)
- `boundaries/ortschaftenverzeichnis-plz` — Official Register of Localities with Postal Codes (PLZ) (vector)
- `boundaries/municipality-register` — Official Register of Swiss Municipalities (BFS) (tabular)
- `terrain-imagery/swissalti3d` — swissALTI3D — High-Resolution Digital Terrain Model (raster)
- `terrain-imagery/swissimage-dop10` — SWISSIMAGE 10 cm — Digital Orthophoto (raster)

## Cross-dataset join keys

- **`bfs_nummer`** (integer) is the national municipality key. It joins `boundaries/swissboundaries3d`, `boundaries/municipality-register`, and `boundaries/ortschaftenverzeichnis-plz`, and reaches almost all Swiss federal statistics.
- **`egid`** joins `topography/swissbuildings3d` to the federal building & dwelling register.
- **`plz`** (+`zusatzziffer`) keys postal localities in `boundaries/ortschaftenverzeichnis-plz`.

## Coordinate systems

Vector/tabular data is published in EPSG:4326 (WGS84). The Swiss source CRS is EPSG:2056 (CH1903+/LV95), in metres. For area or length, transform to EPSG:2056 first — `ST_Area` on WGS84 degrees is meaningless. Raster tiles are kept in EPSG:2056.

## Example: query one collection

```python
import duckdb
con = duckdb.connect(); con.sql('INSTALL spatial; LOAD spatial;')
con.sql("SELECT count(*) FROM read_parquet('https://ch-geodata.s3.eu-north-1.amazonaws.com/boundaries/swissboundaries3d/swissboundaries3d.parquet')").show()
```

_Generated from `tools/manifest/`._
