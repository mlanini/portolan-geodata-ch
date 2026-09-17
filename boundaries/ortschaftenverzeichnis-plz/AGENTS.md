# AGENTS.md — Official Register of Localities with Postal Codes (PLZ)

## What this is and how it connects

Bridges postal codes (plz) to administrative geography (bfs_nummer).

**Keys.** plz+zusatzziffer identify a locality; bfs_nummer joins to swissboundaries3d.

## Access

- Base URL: `https://ch-geodata.s3.eu-north-1.amazonaws.com/boundaries/ortschaftenverzeichnis-plz/`
- S3: `s3://ch-geodata/boundaries/ortschaftenverzeichnis-plz/`
- CRS: EPSG:4326 (WGS84) (source EPSG:2056 (CH1903+ / LV95)).

## Runnable access patterns

```python
import duckdb
con = duckdb.connect(); con.sql('INSTALL spatial; LOAD spatial;')
con.sql("SELECT count(*) FROM read_parquet('https://ch-geodata.s3.eu-north-1.amazonaws.com/boundaries/ortschaftenverzeichnis-plz/ortschaftenverzeichnis-plz.parquet')").show()
```

**Localities in a postal code**

```sql
SELECT ortschaftsname, bfs_nummer FROM read_parquet('https://ch-geodata.s3.eu-north-1.amazonaws.com/boundaries/ortschaftenverzeichnis-plz/ortschaftenverzeichnis-plz.parquet') WHERE plz = 3011;
```

## Quirks and caveats

- One PLZ can map to several localities and even several municipalities; never assume PLZ is 1:1 with a commune.

## Related collections

- `boundaries/swissboundaries3d`
- `boundaries/municipality-register`

## Provenance

Mirror of Federal Office of Topography swisstopo data. Source: https://www.swisstopo.admin.ch/en/official-directory-of-towns-and-cities . Source STAC: https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo-vd.ortschaftenverzeichnis_plz .

_Generated from `tools/manifest/datasets.yaml`._
