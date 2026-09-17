# Data sources and original downloads

geodata.ch is a **mirror**. Every collection is produced by a Swiss federal
authority and republished here in cloud-native form. This page records where each
dataset comes from and which original formats it mirrors, so a user can always
reach the authoritative copy. Per-release download URLs are resolved from the
source STAC by `tools/harvest_stac.py`; the pages below are the stable landing
points.

## The Swiss Federal Spatial Data Infrastructure (BGDI)

- **STAC API:** https://data.geo.admin.ch/api/stac/v0.9 — the machine interface to
  all federal geodata. Each collection here carries a `canonical` link to its BGDI
  STAC collection and a `metadata` asset pointing at the same URL.
- **Documentation:** https://docs.geo.admin.ch/ — the BGDI/`geo.admin.ch` developer
  docs (STAC usage, the `data.geo.admin.ch` download service, tile services).
- **ISO 19115 metadata:** https://www.geocat.ch/ — the national geometadata
  catalogue. `harvest_stac.py` resolves each dataset's geocat record id and links
  its ISO 19139 XML, which carries lineage, quality, and contact metadata beyond
  what STAC exposes.

## Datasets in this catalog

| Collection | Producer | Source STAC id | Original formats mirrored |
| --- | --- | --- | --- |
| `topography/swisstlm3d` | swisstopo | `ch.swisstopo.swisstlm3d` | FileGDB, GeoPackage, INTERLIS/XTF |
| `topography/swisstlmregio` | swisstopo | `ch.swisstopo.swisstlmregio` | FileGDB, GeoPackage, INTERLIS/XTF |
| `topography/swissnames3d` | swisstopo | `ch.swisstopo.swissnames3d` | GeoPackage, INTERLIS/XTF, CSV |
| `topography/vec200-landcover` | swisstopo | `ch.swisstopo.vec200-landcover` | FileGDB, GeoPackage, Shapefile |
| `topography/swissbuildings3d` | swisstopo | `ch.swisstopo.swissbuildings3d_3_0` | FileGDB, INTERLIS/XTF, CityGML |
| `boundaries/swissboundaries3d` | swisstopo | `ch.swisstopo.swissboundaries3d` | FileGDB, GeoPackage, Shapefile, INTERLIS/XTF |
| `boundaries/ortschaftenverzeichnis-plz` | swisstopo | `ch.swisstopo-vd.ortschaftenverzeichnis_plz` | GeoPackage, INTERLIS/XTF, CSV |
| `boundaries/municipality-register` | BFS | — (non-STAC) | CSV, XLSX |
| `terrain-imagery/swissalti3d` | swisstopo | `ch.swisstopo.swissalti3d` | GeoTIFF, XYZ |
| `terrain-imagery/swissimage-dop10` | swisstopo | `ch.swisstopo.swissimage-dop10` | GeoTIFF (COG) |

> **Source STAC ids are marked `verify: pipeline` in the manifest.** They follow
> swisstopo's published `ch.<office>.<product>` convention but were authored
> offline. `make harvest` verifies every id against the live API and fails on any
> mismatch, so a wrong id is caught before a build.

## What geodata.ch changes and does not change

- **Formats.** Vector originals (FileGDB/GeoPackage/XTF) become GeoParquet + a
  PMTiles visual derivative. Non-spatial tables (CSV/XLSX) become Parquet. Raster
  (GeoTIFF) becomes Cloud-Optimized GeoTIFF scene collections with a
  STAC-GeoParquet item mirror.
- **CRS.** Vector/tabular data is reprojected from EPSG:2056 (CH1903+/LV95) to
  EPSG:4326 (WGS84) for portability; raster tiles keep EPSG:2056. The source CRS
  is recorded per collection.
- **Semantics.** Attribute names, codes, and values are preserved from the source
  model. The mirror adds no interpretation.
- **Authority.** swisstopo/BFS remain the authoritative source. For legal,
  cadastral, or safety-critical use, consult the original.

## License

All datasets are published under the single blanket term
[swisstopo free geodata](https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata):
free to use, including commercially, provided the source is cited. In Portolan
terms this is `license: "other"` with a `license` link, applied uniformly across
every collection. The BFS municipality register is likewise open government data
under the same citation requirement.
