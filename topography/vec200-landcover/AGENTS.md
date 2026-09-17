# AGENTS.md — VECTOR200 — Land Cover

## What this is and how it connects

Coarse national land cover; pair with swissboundaries3d for per-canton statistics.

**Keys.** objval is the class; aggregate area by it.

## Access

- Base URL: `https://ch-geodata.s3.eu-central-2.amazonaws.com/topography/vec200-landcover/`
- S3: `s3://ch-geodata/topography/vec200-landcover/`
- CRS: EPSG:4326 (WGS84) (source EPSG:2056 (CH1903+ / LV95)).

## Runnable access patterns

```python
import duckdb
con = duckdb.connect(); con.sql('INSTALL spatial; LOAD spatial;')
con.sql("SELECT count(*) FROM read_parquet('https://ch-geodata.s3.eu-central-2.amazonaws.com/topography/vec200-landcover/vec200-landcover.parquet')").show()
```

**Forest area by class**

```sql
SELECT objval, SUM(ST_Area(ST_Transform(geometry,'EPSG:4326','EPSG:2056')))/1e6 AS km2 FROM read_parquet('https://ch-geodata.s3.eu-central-2.amazonaws.com/topography/vec200-landcover/vec200-landcover.parquet') GROUP BY objval;
```

## Quirks and caveats

- Areas must be computed in a projected CRS (EPSG:2056), not the published EPSG:4326.

## Provenance

Mirror of Federal Office of Topography swisstopo data. Source: https://www.swisstopo.admin.ch/en/landscape-model-vector200 . Source STAC: https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.vec200-landcover .

_Generated from `tools/manifest/datasets.yaml`._
