# AGENTS.md — Official Register of Swiss Municipalities (BFS)

## What this is and how it connects

Non-spatial key table. bfs_nummer is the join key to swissboundaries3d geometry.

**Keys.** bfs_nummer (primary key). Use gueltig_von/gueltig_bis to pick the record valid at a given date.

## Access

- Base URL: `https://ch-geodata.s3.eu-north-1.amazonaws.com/boundaries/municipality-register/`
- S3: `s3://ch-geodata/boundaries/municipality-register/`
- CRS: n/a (non-spatial) (source n/a (non-spatial)).

## Runnable access patterns

```python
import duckdb
con = duckdb.connect(); con.sql('INSTALL spatial; LOAD spatial;')
con.sql("SELECT count(*) FROM read_parquet('https://ch-geodata.s3.eu-north-1.amazonaws.com/boundaries/municipality-register/municipality-register.parquet')").show()
```

**Join register to geometry**

```sql
SELECT r.gemeindename, b.geometry FROM read_parquet('https://ch-geodata.s3.eu-north-1.amazonaws.com/boundaries/municipality-register/municipality-register.parquet') r JOIN read_parquet('../swissboundaries3d/swissboundaries3d.parquet') b USING (bfs_nummer) WHERE r.gueltig_bis IS NULL;
```

## Quirks and caveats

- A bfs_nummer can appear multiple times across history — filter by validity dates before joining.

## Related collections

- `boundaries/swissboundaries3d`

## Provenance

Mirror of Swiss Federal Statistical Office (FSO/BFS) data. Source: https://www.bfs.admin.ch/bfs/en/home/basics/swiss-official-commune-register.html . No upstream STAC; see the source page.

_Generated from `tools/manifest/datasets.yaml`._
