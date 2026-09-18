# Assessing geodienste.ch for integration into geodata.ch

This is an **assessment**, not an implementation. The current catalog mirrors
federal (swisstopo/BFS) data. geodienste.ch is the natural next source, and this
note records how it would fit the Portolan model, what is easy, and what is hard.

## What geodienste.ch is

[geodienste.ch](https://www.geodienste.ch/) is the platform of the Conference of
Cantonal Geoinformation Officers (KGK-CGC). It publishes **cantonal** geodata that
is harmonised to national models — most importantly the cadastral and
land-management datasets that the Confederation defines but the cantons produce and
maintain. Typical layers: cadastral survey (Amtliche Vermessung), zone plans
(Nutzungsplanung), agricultural data, contaminated-site registers (Kataster der
belasteten Standorte), and public-law restrictions (ÖREB/PLR-cadastre).

Its distinguishing feature is **per-canton, harmonised coverage**: the same
INTERLIS model is served for each of the 26 cantons (plus Liechtenstein), so a
national picture is assembled by unioning cantonal extracts.

## The API surface

The service is documented at
[geodienste.ch/api-docs](https://www.geodienste.ch/api-docs/index.html) and centres
on OGC web services plus bulk download, rather than a STAC API:

- **INTERLIS bulk download** per canton and dataset, as `.xtf` (INTERLIS 2) or
  `.itf` (INTERLIS 1), the authoritative transfer format.
- **OGC API / WFS / WMS / WMTS** endpoints for live access.
- A **download/status API** that reports, per dataset and canton, whether data is
  available, its currentness (`Aktualität`), and access level (public vs.
  authenticated), which matters because some cantonal data needs registration or a
  contract.

There is no single national STAC collection to mirror; the unit of access is
`(dataset, canton)`.

## How it maps to Portolan

The fit is good, with one clear modelling decision.

- **Formats.** INTERLIS/XTF converts to GeoParquet through `ogr2ogr` with the
  INTERLIS driver and a compiled model (`ili2gpkg`/`ilismeta`), exactly as the
  existing `convert.py` vector path does. No new format machinery is needed.
- **Structure.** A geodienste dataset is national-in-aggregate but cantonal in
  delivery. Two viable shapes:
  1. **One collection per dataset, partitioned by canton** — a partitioned
     GeoParquet collection with `partition:keys: [kanton]` and a `partition:glob`
     over 26 files. This is the recommended shape: one collection, one query
     surface, spatially prunable by canton. It matches the Portolan partitioned
     collection pattern directly.
  2. **A sub-catalog per dataset with one collection per canton** — only if
     cantonal editions diverge enough (schema, license, currentness) that a single
     schema is impossible.
- **Provenance.** Producer is the canton (or KGK-CGC as coordinator); host is
  geodata.ch → these are mirror collections with `via` links to the geodienste
  dataset page and, where present, the cantonal source. The download/status API's
  currentness timestamp feeds the mirror's `updated` field per canton.
- **A thematic catalog** `cadastre/` (or `cantonal/`) would sit beside the current
  `topography/`, `boundaries/`, and `terrain-imagery/` catalogs.

## What is hard

- **Access control.** Several geodienste datasets are not open: they require an
  account or a contract, or are available only to authorities. Those cannot be
  mirrored publicly to `s3://ch-geodata`. The status API must gate harvesting so
  the pipeline only mirrors datasets whose access level is public, and records the
  license **per canton** — which breaks the single-blanket-license assumption that
  holds for the current federal subset.
- **Heterogeneous currentness.** Cantons update on their own cadence, so a national
  partitioned collection mixes vintages. `updated` must be tracked per partition,
  and the README must state the spread, not a single date.
- **Model versions.** Cantons can lag between INTERLIS model versions during
  transitions, so a "single Parquet schema across all partitions" (a Portolan
  requirement for partitioned collections) is not guaranteed. The pipeline needs a
  schema-reconciliation step, or must fall back to shape (2) for datasets mid-
  transition.
- **Volume.** Cadastral survey for all cantons is large; partition files should
  target the 200 MB–1 GB range the spec recommends, which means per-canton or
  finer partitioning.

## Recommendation

Integrate geodienste.ch as a **second phase**, starting with one fully-open,
harmonised dataset (e.g. the ÖREB/PLR-cadastre or a public cadastral layer),
modelled as a single canton-partitioned collection under a new `cadastre/`
catalog. Drive harvesting from the geodienste status API so only public datasets
are mirrored, and extend the manifest to carry **per-canton license and
currentness**. Prove the pattern on one dataset before scaling to the full
cantonal set. No code in this repository needs to change to begin; the manifest
schema and `convert.py` already cover the vector/INTERLIS path, and only the
harvester needs a geodienste-specific front end.
