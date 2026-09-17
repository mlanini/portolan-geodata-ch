# AGENTS.md — swissNAMES3D — Geographical Names

## What this is and how it connects

The national gazetteer; the stable key is 'uuid'.

**Keys.** uuid is stable per feature; filter language with sprachcode.

## Access

- Base URL: `https://ch-geodata.s3.eu-north-1.amazonaws.com/topography/swissnames3d/`
- S3: `s3://ch-geodata/topography/swissnames3d/`
- CRS: EPSG:4326 (WGS84) (source EPSG:2056 (CH1903+ / LV95)).

## Runnable access patterns

```python
import duckdb
con = duckdb.connect(); con.sql('INSTALL spatial; LOAD spatial;')
con.sql("SELECT count(*) FROM read_parquet('https://ch-geodata.s3.eu-north-1.amazonaws.com/topography/swissnames3d/swissnames3d.parquet')").show()
```

**Find a peak by name**

```sql
SELECT name, geometry FROM read_parquet('https://ch-geodata.s3.eu-north-1.amazonaws.com/topography/swissnames3d/swissnames3d.parquet') WHERE objektart LIKE '%Gipfel%' AND name = 'Matterhorn';
```

## Quirks and caveats

- A place can appear multiple times with different sprachcode values — filter or group by language.

## Provenance

Mirror of Federal Office of Topography swisstopo data. Source: https://www.swisstopo.admin.ch/en/geographical-names-swissnames3d . Source STAC: https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.swissnames3d .

_Generated from `tools/manifest/datasets.yaml`._
