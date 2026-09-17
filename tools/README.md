# geodata.ch tooling

Everything here turns one manifest and the live Swiss sources into a published
Portolan catalog. Metadata and data are generated separately so the fast,
offline metadata build never depends on the network.

## Layout

| Path | Purpose |
| --- | --- |
| `manifest/catalog.yaml` | Catalog-wide config: bucket, base URL, license, providers, extent. |
| `manifest/datasets.yaml` | One entry per collection: schema, provenance, extent, agent notes. |
| `generate_catalog.py` | Manifest → STAC tree + every README.md / AGENTS.md / style. |
| `validate.py` | Offline structural + Portolan checks (no bytes, no network). |
| `harvest_stac.py` | Verify source STAC ids and read real extents from data.geo.admin.ch + geocat.ch. |
| `convert.py` | GDAL/tippecanoe/rio-cogeo wrappers: originals → GeoParquet / PMTiles / COG. |
| `build.py` | Orchestrator: harvest → download → convert → derive → enrich → publish → validate. |

## Offline (works anywhere)

```bash
make generate    # rewrite the catalog from tools/manifest/
make validate    # 4 catalogs + 10 collections, structural + Portolan rules
make check       # CI guard: fail if the tree is stale vs. the manifest
```

Edit metadata in `tools/manifest/`, never in the generated files — `make check`
enforces this.

## Online (Swiss Federal network only)

The Swiss sources have no public DNS, so these steps need the Federal proxy:

```bash
export HTTPS_PROXY=http://prp01.adb.intra.admin.ch:8080
export HTTP_PROXY=$HTTPS_PROXY
pip install -r tools/requirements.txt   # plus GDAL>=3.9, tippecanoe on PATH

make harvest     # verify source_stac ids, cache real extents + geocat records
make build       # full pipeline into tools/cache/out, enrich JSON with real stats
make publish     # aws s3 sync to s3://ch-geodata (needs credentials + CORS setup)
```

`build.py` refuses to write a `file:size` or `file:checksum` for an asset that is
not present on disk, so a partial run never fabricates byte-level metadata.

## Verifying against the real spec

After `make publish`, run the Portolan validator
[`rashid`](https://github.com/portolan-sdi/rashid) against the published root
`catalog.json` for the full data pass (GeoParquet spatial ordering, COG
statistics, link resolution over HTTP). `validate.py` here covers only the
offline structural and metadata checks.
