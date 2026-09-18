# Official Register of Swiss Municipalities (BFS)

> Part of the [geodata.ch](../../README.md) cloud-native catalog of Swiss federal geodata. Agents: see [AGENTS.md](./AGENTS.md).

The official register of the communes of Switzerland maintained by the Federal Statistical Office (BFS): the canonical list of municipality numbers, names, cantons, and districts, with the mutation history that tracks mergers and renamings. This is the non-spatial key table that joins to swissBOUNDARIES3D and to all BFS municipal statistics.

**Coverage.** Every current and historical Swiss municipality since the register's historicized start.

**Source.** Produced by Swiss Federal Statistical Office (FSO/BFS) and mirrored here in cloud-native form. The authoritative copy and the original downloads live at the [source product page](https://www.bfs.admin.ch/bfs/en/home/basics/swiss-official-commune-register.html).

**License.** `other` — [swisstopo — free geodata, free use with source citation](https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata).

## Quick start

```python
import duckdb
con = duckdb.connect()
con.sql("INSTALL spatial; LOAD spatial;")
df = con.sql("SELECT * FROM read_parquet('https://ch-geodata.s3.eu-north-1.amazonaws.com/boundaries/municipality-register/municipality-register.parquet') LIMIT 100").df()
```

## Original source formats

geodata.ch mirrors this dataset from the authoritative swisstopo/BFS downloads. The originals remain the reference copy:

| Format | Media type | Title |
| --- | --- | --- |
| CSV | `text/csv` | Amtliches Gemeindeverzeichnis (CSV) |
| XLSX | `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` | Amtliches Gemeindeverzeichnis (Excel) |

Concrete per-release download URLs are resolved from the source STAC by the [build pipeline](../../tools/README.md); see also [docs/data-sources.md](../../docs/data-sources.md).

## Schema

| Column | Type | Description |
| --- | --- | --- |
| `bfs_nummer` | int | BFS municipality number — primary key; joins to swissboundaries3d and BFS statistics. |
| `gemeindename` | string | Official municipality name. |
| `kanton` | string | Canton abbreviation. |
| `bezirksname` | string | District name. |
| `gueltig_von` | date | Date from which this record is valid (mutation history). |
| `gueltig_bis` | date | Date until which this record is valid, null if current. |

## Coordinate reference system

- Source CRS: n/a (non-spatial)
- Published CRS: n/a (non-spatial)

## Suggested uses

- Resolving a BFS number to a current name/canton, including across historical mergers.
- Validating and enriching any dataset keyed by BFS number.

## Limitations and inappropriate uses

- This is a reference table, not spatial data; join it to swissboundaries3d for geometry.

## Definitions

- 'gueltig_von'/'gueltig_bis' bound the validity of each register record across the mutation history.

## Temporal note

Historicized register; interval start indicative of the mutation history retained.

---

_This page is generated from `tools/manifest/datasets.yaml`. Edit the manifest, not this file._
