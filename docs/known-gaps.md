# Known gaps and honesty notes

This catalog is a **spec-compliant scaffold** (approach b): the full STAC
structure, documentation, provenance, and build tooling are complete, but the data
assets themselves are produced by the pipeline when it runs inside the Swiss
Federal network. This page is the honest inventory of what is real, what is
placeholder, and what a reviewer must not mistake for verified fact.

## Why the scaffold stops where it does

The authoring environment cannot reach the Swiss sources. `data.geo.admin.ch`,
`geocat.ch`, `docs.geo.admin.ch`, and `portolan-sdi.org` have no route from it, and
the Federal proxy (`prp01.adb.intra.admin.ch:8080`) is an internal host with no
public DNS. So the catalog was built from the Portolan specification (cloned from
GitHub) and well-known public facts about the datasets — never from live bytes.

Rule followed throughout: **an absent value beats a fabricated one** (Portolan
core.md). Nothing derived from data bytes was invented.

## What is real

- The STAC tree: 1 root catalog, 3 thematic catalogs, 10 collections, all valid
  STAC 1.1.0 and passing `tools/validate.py` (structure, links, Portolan rules).
- Provider, license, keyword, CRS, schema, and provenance metadata.
- Human-readable READMEs and agent-oriented AGENTS.md for every node.
- The build pipeline (`harvest → convert → derive → enrich → publish → validate`)
  with the exact GDAL/tippecanoe/rio-cogeo commands.
- National WGS84 bounding boxes (Switzerland's extent is public knowledge).

## What is placeholder, filled by `make build`

| Item | Current state | Filled by |
| --- | --- | --- |
| `data` / `visual` assets (`.parquet`, `.pmtiles`) | referenced at their future `s3://ch-geodata` URLs; **files not yet produced** | `convert` + `derive` + `publish` |
| Raster COG scenes + `items.parquet` mirror | described; scene items not generated | `convert` + `derive` |
| `thumbnail.png` | referenced; image not generated | `derive` (render from default style) |
| `file:size`, `file:checksum` | **omitted** (not guessed) | `enrich`, from real bytes only |
| Collection `extent` bbox/temporal | national extent + indicative dates | `enrich`, from harvested STAC |
| `source_stac` ids | follow swisstopo convention, `verify: pipeline` | `harvest` verifies vs. live API |
| Original per-release download hrefs | landing pages linked; exact file URLs not embedded | `harvest`, from source items |
| geocat.ch ISO 19139 record ids | resolved by keyword at build time | `harvest` |
| Table schemas (`table:columns`) | representative of the source model | regenerated from the Parquet footer during `convert` |

## Consequences for validation

`tools/validate.py` runs the **offline** passes only: STAC structure, required
Portolan metadata, link resolution on disk, asset roles/types. The **data pass**
of the real validator ([`rashid`](https://github.com/portolan-sdi/rashid)) —
GeoParquet spatial ordering, row-group statistics, COG overviews/statistics,
checksum-vs-bytes, HTTP range/CORS on the host — can only pass after `make build`
and `make publish`. Until then, treat the catalog as **metadata-valid, data-pending**.

## Deliberate simplifications

- **Partitioning.** `swisstlm3d` and `swissbuildings3d` are large and will be
  partitioned by theme/region in production. The scaffold models them as
  single-file collections and documents the intent; `convert.py` + the partition
  extension switch them over during the real build.
- **Multilingual trees.** Switzerland has four national languages. The catalog is
  authored in English with local attribute/place names preserved. Full
  alternate-language STAC trees (STAC Language extension) are a future enhancement,
  noted here rather than half-built.
- **geodienste.ch.** Assessed in `docs/geodienste-integration.md`, not integrated,
  per the task scope.
