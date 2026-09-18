# AGENTS.md — swissTLMRegio — Generalized Topographic Model

## What this is and how it connects

Use for national overviews; drop to swisstlm3d when detail matters.

**Keys.** objektart for thematic filtering; no stable national feature id.

## Access

- Base URL: `https://ch-geodata.s3.eu-north-1.amazonaws.com/topography/swisstlmregio/`
- S3: `s3://ch-geodata/topography/swisstlmregio/`
- CRS: EPSG:4326 (WGS84) (source EPSG:2056 (CH1903+ / LV95)).

## Runnable access patterns

```python
import duckdb
con = duckdb.connect(); con.sql('INSTALL spatial; LOAD spatial;')
con.sql("SELECT count(*) FROM read_parquet('https://ch-geodata.s3.eu-north-1.amazonaws.com/topography/swisstlmregio/swisstlmregio.parquet')").show()
```

**National river network**

```sql
SELECT * FROM read_parquet('https://ch-geodata.s3.eu-north-1.amazonaws.com/topography/swisstlmregio/swisstlmregio.parquet') WHERE objektart LIKE '%Fluss%';
```

## Quirks and caveats

- Generalized geometry — nearby features from swisstlm3d will not overlay exactly.

## Provenance

Mirror of Federal Office of Topography swisstopo data. Source: https://www.swisstopo.admin.ch/en/landscape-model-swisstlmregio . Source STAC: https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.swisstlmregio .

_Generated from `tools/manifest/datasets.yaml`._
