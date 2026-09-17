# AGENTS.md — swissTLM3D — Topographic Landscape Model

## What this is and how it connects

The national topographic reference. Every other geodata.ch vector layer can be snapped to it.

**Keys.** No single national key; join thematically by geometry (spatial join) or by objektart within a theme.

## Access

- Base URL: `https://ch-geodata.s3.eu-central-2.amazonaws.com/topography/swisstlm3d/`
- S3: `s3://ch-geodata/topography/swisstlm3d/`
- CRS: EPSG:4326 (WGS84) (source EPSG:2056 (CH1903+ / LV95, with LN02 heights)).

## Runnable access patterns

```python
import duckdb
con = duckdb.connect(); con.sql('INSTALL spatial; LOAD spatial;')
con.sql("SELECT count(*) FROM read_parquet('https://ch-geodata.s3.eu-central-2.amazonaws.com/topography/swisstlm3d/swisstlm3d.parquet')").show()
```

**Roads within a bbox**

```sql
SELECT * FROM read_parquet('https://ch-geodata.s3.eu-central-2.amazonaws.com/topography/swisstlm3d/**/*.parquet') WHERE objektart LIKE 'Strasse%' AND ST_Intersects(geometry, ST_MakeEnvelope(7.4,46.9,7.5,47.0));
```

## Quirks and caveats

- This is a partitioned collection: read the whole theme with the partition glob, not a single file.
- Geometry is delivered in EPSG:4326; the source model is EPSG:2056 (metres). For area/length use a projected CRS.

## Provenance

Mirror of Federal Office of Topography swisstopo data. Source: https://www.swisstopo.admin.ch/en/landscape-model-swisstlm3d . Source STAC: https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.swisstlm3d .

_Generated from `tools/manifest/datasets.yaml`._
