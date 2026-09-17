# geodata.ch — Swiss Federal Geodata, Cloud-Native

> Agents: start with [AGENTS.md](./AGENTS.md).

geodata.ch is a cloud-native mirror of open geodata from the Swiss Federal Spatial Data Infrastructure (BGDI). It republishes a curated set of swisstopo and other federal datasets as GeoParquet, PMTiles, and Cloud-Optimized GeoTIFF so a person or an agent can query them directly from object storage with no server in between. Every collection links back to the authoritative swisstopo source and its original FileGDB, GeoPackage, and INTERLIS (XTF) downloads.

geodata.ch is a **mirror**: the datasets are produced by swisstopo and the Federal Statistical Office and republished here in cloud-native formats (GeoParquet, PMTiles, Cloud-Optimized GeoTIFF). Every collection links back to its authoritative source and original downloads.

- **Storage:** `s3://ch-geodata` (`arn:aws:s3:::ch-geodata`), served over HTTPS at `https://ch-geodata.s3.eu-central-2.amazonaws.com`.
- **License:** all data under `other` — [swisstopo — free geodata, free use with source citation](https://www.swisstopo.admin.ch/en/terms-of-use-free-geodata).
- **Spec:** Portolan `https://schemas.portolan-sdi.org/portolan/v0.2.0/schema.json` (STAC 1.1.0).

## Catalog contents

| Collection | Type | Geometry | Description |
| --- | --- | --- | --- |
| [swissTLM3D — Topographic Landscape Model](./swisstlm3d/README.md) | vector | Multiple (points, lines, polygons across ~70 layers) | swissTLM3D is the large-scale topographic landscape model of Switzerland: the most detailed and precise vector reference of roads, railways, buildings, watercourses, land cover, and more, with 3D geometry. |
| [swissTLMRegio — Generalized Topographic Model](./swisstlmregio/README.md) | vector | Lines and polygons (generalized) | swissTLMRegio is the small-scale (≈1:200,000) generalized derivative of swissTLM3D, covering Switzerland and neighbouring regions. |
| [swissNAMES3D — Geographical Names](./swissnames3d/README.md) | vector | Points, lines, polygons (named features) | swissNAMES3D is the complete set of geographical names of Switzerland: settlements, terrain features, waters, and named objects, each as a 3D point, line, or polygon. |
| [VECTOR200 — Land Cover](./vec200-landcover/README.md) | vector | Polygons | The land-cover layer of VECTOR200, the vectorized national map at 1:200,000. |
| [swissBUILDINGS3D — 3D Building Models](./swissbuildings3d/README.md) | vector | Polygons / multipolygons (3D building models) | swissBUILDINGS3D contains the buildings of Switzerland as 3D models with roof shapes, derived from the swisstopo stereo-photogrammetric workflow and the cadastral footprint. |
| [swissBOUNDARIES3D — Administrative Boundaries](./swissboundaries3d/README.md) | vector | Polygons (country, canton, district, municipality) | swissBOUNDARIES3D holds the administrative boundaries of Switzerland at four levels — country, canton, district, and municipality — with the official BFS municipality numbers. |
| [Official Register of Localities with Postal Codes (PLZ)](./ortschaftenverzeichnis-plz/README.md) | vector | Polygons and points (localities / postal areas) | The official directory of Swiss localities with their postal codes (PLZ), linking place names, postal codes, and municipalities. |
| [Official Register of Swiss Municipalities (BFS)](./municipality-register/README.md) | tabular | — | The official register of the communes of Switzerland maintained by the Federal Statistical Office (BFS): the canonical list of municipality numbers, names, cantons, and districts, with the mutation history that tracks mergers and renamings. |
| [swissALTI3D — High-Resolution Digital Terrain Model](./swissalti3d/README.md) | raster | Raster tiles (DTM) | swissALTI3D is the high-precision digital terrain model of Switzerland, describing the bare-earth surface without vegetation or buildings at 0. |
| [SWISSIMAGE 10 cm — Digital Orthophoto](./swissimage-dop10/README.md) | raster | Raster tiles (orthophoto) | SWISSIMAGE 10 cm (DOP10) is the seamless orthorectified aerial-image mosaic of Switzerland at 10 cm ground resolution in the lowlands. |

## Where the data comes from

The datasets originate in the Swiss Federal Spatial Data Infrastructure (BGDI). Their authoritative STAC API is at https://data.geo.admin.ch/api/stac/v0.9 . Original FileGDB, GeoPackage, and INTERLIS (XTF) downloads, plus ISO 19115 metadata from geocat.ch, are enumerated per collection and in [docs/data-sources.md](./docs/data-sources.md).

## Building and updating

The catalog metadata is generated from a single manifest and the data assets are produced by a repeatable pipeline. See [tools/README.md](./tools/README.md). Integration of cantonal data via geodienste.ch is assessed in [docs/geodienste-integration.md](./docs/geodienste-integration.md).

_This page is generated from `tools/manifest/`. Edit the manifest, not this file._
