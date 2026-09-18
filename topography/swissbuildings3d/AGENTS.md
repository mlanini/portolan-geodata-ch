# AGENTS.md — swissBUILDINGS3D — 3D Building Models

## What this is and how it connects

Building footprints keyed by EGID; the 3D model is in the source.

**Keys.** egid joins to the federal building & dwelling register; uuid is the internal stable id.

## Access

- Base URL: `https://ch-geodata.s3.eu-north-1.amazonaws.com/topography/swissbuildings3d/`
- S3: `s3://ch-geodata/topography/swissbuildings3d/`
- CRS: EPSG:4326 (WGS84), 2D footprints (source EPSG:2056 (CH1903+ / LV95), LN02 heights).

## Runnable access patterns

```python
import duckdb
con = duckdb.connect(); con.sql('INSTALL spatial; LOAD spatial;')
con.sql("SELECT count(*) FROM read_parquet('https://ch-geodata.s3.eu-north-1.amazonaws.com/topography/swissbuildings3d/swissbuildings3d.parquet')").show()
```

**Buildings by roof type**

```sql
SELECT dachtyp, count(*) FROM read_parquet('https://ch-geodata.s3.eu-north-1.amazonaws.com/topography/swissbuildings3d/**/*.parquet') GROUP BY dachtyp ORDER BY 2 DESC;
```

## Quirks and caveats

- Partitioned collection — read via the glob. 3D is not in the GeoParquet.
- Not every building carries an EGID; handle nulls before joining.

## Provenance

Mirror of Federal Office of Topography swisstopo data. Source: https://www.swisstopo.admin.ch/en/landscape-model-swissbuildings3d-3-0 . Source STAC: https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.swissbuildings3d_3_0 .

_Generated from `tools/manifest/datasets.yaml`._
