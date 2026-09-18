#!/usr/bin/env python3
"""Orchestrate the geodata.ch build: harvest -> download -> convert -> derive ->
enrich -> validate.

This is the end-to-end pipeline that turns the manifest and the live Swiss
sources into a published catalog. It runs inside the Federal network (proxy set)
and needs GDAL, tippecanoe, rio-cogeo, and the AWS CLI. In the public sandbox the
network steps cannot run; the steps are ordered and documented so the workflow is
reproducible.

Stages (each is idempotent and skippable):
  harvest   verify source STAC ids and read real extents      -> tools/cache/harvested
  download  fetch the original FileGDB/GPKG/XTF/GeoTIFF        -> tools/cache/src
  convert   originals -> GeoParquet / Parquet / COG            -> tools/cache/out
  derive    GeoParquet -> PMTiles, COG mosaics -> thumbnails   -> tools/cache/out
  enrich    write real bbox + file:size + file:checksum into   -> <catalog>
            the generated collection.json
  publish   sync tools/cache/out and the catalog to s3://ch-geodata (aws s3 sync)
  validate  run tools/validate.py and, when available, rashid

Run `python tools/generate_catalog.py` first to (re)create the metadata tree, then
this pipeline to fill it with real assets and byte-level statistics.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "tools" / "manifest"
CACHE = ROOT / "tools" / "cache"
HARVESTED = CACHE / "harvested"
OUT = CACHE / "out"

STAGES = ["harvest", "download", "convert", "derive", "enrich", "publish", "validate"]


def multihash_sha256(path: Path) -> str:
    """sha256 as a hex multihash (0x12 = sha2-256, 0x20 = 32-byte length)."""
    h = hashlib.sha256(path.read_bytes()).digest()
    return "1220" + h.hex()


def load_datasets():
    return yaml.safe_load((MANIFEST / "datasets.yaml").read_text())["datasets"]


# --------------------------------------------------------------------------- stages
def stage_harvest():
    subprocess.run([sys.executable, str(ROOT / "tools" / "harvest_stac.py")], check=True)


def stage_download(datasets):
    print("download: fetch each dataset's original from the hrefs recorded in "
          f"{HARVESTED.relative_to(ROOT)} into {(CACHE / 'src').relative_to(ROOT)} "
          "(curl/aws through the proxy). Skipping here — no network in sandbox.")


def stage_convert(datasets):
    print("convert: call tools/convert.py per dataset. For example:")
    for ds in datasets:
        leaf = ds["id"].split("/")[-1]
        if ds["data_type"] == "vector":
            print(f"  convert.py vector cache/src/{leaf}.gpkg {OUT.name}/{ds['id']}/{leaf}.parquet")
        elif ds["data_type"] == "tabular":
            print(f"  convert.py table  cache/src/{leaf}.csv  {OUT.name}/{ds['id']}/{leaf}.parquet")
        elif ds["data_type"] == "raster":
            print(f"  convert.py cog    cache/src/{leaf}/<tile>.tif {OUT.name}/{ds['id']}/<tile>.tif  (per tile)")


def stage_derive(datasets):
    print("derive: GeoParquet -> PMTiles (convert.py pmtiles), render thumbnails "
          "from the default style, and build the STAC-GeoParquet item mirror for "
          "raster collections (stac-geoparquet).")


def stage_enrich(datasets):
    """Write real extents + file:size/file:checksum into the generated JSON.

    Uses harvested extents (authoritative) and produced-asset bytes. Only runs
    for assets that actually exist on disk, so a partial build never fabricates a
    size or checksum (a stale value is worse than an absent one — core.md).
    """
    updated = 0
    for ds in datasets:
        cjson = ROOT / ds["id"] / "collection.json"
        if not cjson.exists():
            continue
        col = json.loads(cjson.read_text())
        rec_path = HARVESTED / (ds["id"].replace("/", "__") + ".json")
        if rec_path.exists():
            rec = json.loads(rec_path.read_text())
            if rec.get("extent", {}).get("spatial"):
                col["extent"]["spatial"] = rec["extent"]["spatial"]
            if rec.get("extent", {}).get("temporal"):
                col["extent"]["temporal"] = rec["extent"]["temporal"]
        for key, asset in col.get("assets", {}).items():
            href = asset.get("href", "")
            if href.startswith("./") or href.startswith("../"):
                continue
            local = OUT / ds["id"] / Path(href).name
            if local.exists():
                asset["file:size"] = local.stat().st_size
                asset["file:checksum"] = multihash_sha256(local)
        cjson.write_text(json.dumps(col, indent=2, ensure_ascii=False) + "\n")
        updated += 1
    print(f"enrich: updated {updated} collection.json files with real extents/checksums where assets exist.")


def stage_publish():
    print("publish: `aws s3 sync` tools/cache/out and the catalog tree to "
          "s3://ch-geodata, then set CORS + range-request headers per core.md "
          "(Data Storage). Skipping here.")


def stage_validate():
    subprocess.run([sys.executable, str(ROOT / "tools" / "validate.py")], check=True)
    print("validate: for the full data pass (GeoParquet ordering, COG stats, "
          "link/byte checks), run the Portolan validator `rashid` against the "
          "published catalog.")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stages", nargs="*", default=STAGES, choices=STAGES,
                    help="subset of stages to run (default: all)")
    args = ap.parse_args()
    datasets = load_datasets()
    OUT.mkdir(parents=True, exist_ok=True)

    for stage in args.stages:
        print(f"\n=== {stage} ===")
        if stage == "harvest":
            stage_harvest()
        elif stage == "download":
            stage_download(datasets)
        elif stage == "convert":
            stage_convert(datasets)
        elif stage == "derive":
            stage_derive(datasets)
        elif stage == "enrich":
            stage_enrich(datasets)
        elif stage == "publish":
            stage_publish()
        elif stage == "validate":
            stage_validate()


if __name__ == "__main__":
    main()
