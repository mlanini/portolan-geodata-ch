# AGENTS.md — swissBOUNDARIES3D — Administrative Boundaries

## What this is and how it connects

The boundary reference. bfs_nummer is THE join key across Swiss federal data.

**Keys.** bfs_nummer joins to boundaries/municipality-register and to almost all BFS statistics.

## Access

- Base URL: `https://ch-geodata.s3.eu-central-2.amazonaws.com/boundaries/swissboundaries3d/`
- S3: `s3://ch-geodata/boundaries/swissboundaries3d/`
- CRS: EPSG:4326 (WGS84) (source EPSG:2056 (CH1903+ / LV95)).

## Runnable access patterns

```python
import duckdb
con = duckdb.connect(); con.sql('INSTALL spatial; LOAD spatial;')
con.sql("SELECT count(*) FROM read_parquet('https://ch-geodata.s3.eu-central-2.amazonaws.com/boundaries/swissboundaries3d/swissboundaries3d.parquet')").show()
```

**Point-in-municipality lookup**

```sql
SELECT b.name, b.bfs_nummer FROM read_parquet('https://ch-geodata.s3.eu-central-2.amazonaws.com/boundaries/swissboundaries3d/swissboundaries3d.parquet') b WHERE ST_Contains(b.geometry, ST_Point(7.447,46.948));
```

## Quirks and caveats

- Communes merge frequently, so a bfs_nummer can be retired; join against the matching year of the municipality register.

## Related collections

- `boundaries/municipality-register`
- `boundaries/ortschaftenverzeichnis-plz`

## Provenance

Mirror of Federal Office of Topography swisstopo data. Source: https://www.swisstopo.admin.ch/en/landscape-model-swissboundaries3d . Source STAC: https://data.geo.admin.ch/api/stac/v0.9/collections/ch.swisstopo.swissboundaries3d .

_Generated from `tools/manifest/datasets.yaml`._
