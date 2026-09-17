#!/usr/bin/env python3
"""Harvest source metadata from the Swiss BGDI STAC API (and geocat.ch).

Runs inside the Swiss Federal network, where data.geo.admin.ch and geocat.ch are
reachable through the proxy. It:

  1. verifies every `source_stac` id in the manifest against the live API;
  2. reads the authoritative spatial/temporal extent of each collection;
  3. lists the original downloadable assets (FileGDB / GeoPackage / XTF / CSV /
     GeoTIFF) and their concrete hrefs, from the collection or its items;
  4. resolves the geocat.ch ISO 19115 metadata record id where available.

Output is written to tools/cache/harvested/<safe-id>.json and consumed by
build.py to fill real bbox statistics and original-download links into the
generated collections. Nothing here runs in the public sandbox: the hosts have
no public DNS. Set the proxy first:

    export HTTPS_PROXY=http://prp01.adb.intra.admin.ch:8080
    export HTTP_PROXY=$HTTPS_PROXY
    python tools/harvest_stac.py
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from urllib.parse import quote

import yaml

try:
    import requests
except ImportError:  # pragma: no cover
    print("This script needs `requests` (see tools/requirements.txt).", file=sys.stderr)
    raise

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "tools" / "manifest"
CACHE = ROOT / "tools" / "cache" / "harvested"

ORIGINAL_MEDIA = {
    "application/x.filegdb+zip", "application/x-filegdb",
    "application/geopackage+sqlite3",
    "application/interlis+xml", "application/x-interlis",
    "text/csv",
    "image/tiff; application=geotiff",
}


def session() -> "requests.Session":
    s = requests.Session()
    proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if proxy:
        s.proxies.update({"http": proxy, "https": proxy})
    s.headers.update({"Accept": "application/json", "User-Agent": "geodata-ch-harvester/0.1"})
    return s


def harvest_collection(s, stac_root: str, cid: str) -> dict:
    url = f"{stac_root}/collections/{cid}"
    r = s.get(url, timeout=60)
    r.raise_for_status()
    col = r.json()
    out = {
        "id": cid,
        "exists": True,
        "extent": col.get("extent", {}),
        "title": col.get("title"),
        "description": col.get("description"),
        "originals": [],
    }
    # Collection-level assets (some products publish full-dataset downloads here).
    for key, a in (col.get("assets") or {}).items():
        if a.get("type") in ORIGINAL_MEDIA:
            out["originals"].append({"key": key, "href": a["href"], "type": a["type"]})
    # Otherwise sample the first item's assets for the download href pattern.
    try:
        ir = s.get(f"{url}/items?limit=1", timeout=60)
        ir.raise_for_status()
        feats = ir.json().get("features", [])
        if feats:
            for key, a in (feats[0].get("assets") or {}).items():
                if a.get("type") in ORIGINAL_MEDIA:
                    out["originals"].append({"key": key, "href": a["href"], "type": a["type"], "from": "item"})
    except requests.RequestException as e:  # noqa: PERF203
        out["items_error"] = str(e)
    return out


def harvest_geocat(s, search: str) -> dict:
    """Resolve a geocat.ch record id by keyword search (best effort)."""
    api = "https://www.geocat.ch/geonetwork/srv/api/search/records/_search"
    body = {"query": {"query_string": {"query": quote(search)}}, "size": 1}
    try:
        r = s.post(api, json=body, timeout=60)
        r.raise_for_status()
        hits = r.json().get("hits", {}).get("hits", [])
        if hits:
            rid = hits[0].get("_id")
            return {"id": rid, "iso19139": f"https://www.geocat.ch/geonetwork/srv/api/records/{rid}/formatters/xml"}
    except requests.RequestException as e:  # noqa: PERF203
        return {"error": str(e)}
    return {}


def main():
    cat = yaml.safe_load((MANIFEST / "catalog.yaml").read_text())["catalog"]
    datasets = yaml.safe_load((MANIFEST / "datasets.yaml").read_text())["datasets"]
    stac_root = cat["bgdi_stac_root"]
    CACHE.mkdir(parents=True, exist_ok=True)
    s = session()

    failures = []
    for ds in datasets:
        cid = ds.get("source_stac")
        safe = ds["id"].replace("/", "__")
        rec: dict = {"manifest_id": ds["id"], "source_stac": cid}
        if cid:
            try:
                rec.update(harvest_collection(s, stac_root, cid))
            except requests.HTTPError as e:
                rec.update({"exists": False, "error": str(e)})
                failures.append(f"{ds['id']} -> {cid}: {e}")
        else:
            rec["note"] = "No source STAC; upstream is a non-STAC download (e.g. BFS)."
        rec["geocat"] = harvest_geocat(s, ds.get("geocat_search", ds["title"]))
        (CACHE / f"{safe}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False))
        print(f"harvested {ds['id']}: exists={rec.get('exists')}, originals={len(rec.get('originals', []))}")

    if failures:
        print("\nSTAC id verification failures (fix source_stac in datasets.yaml):", file=sys.stderr)
        for f in failures:
            print("  -", f, file=sys.stderr)
        sys.exit(1)
    print(f"\nWrote {len(datasets)} harvest records to {CACHE.relative_to(ROOT)}.")


if __name__ == "__main__":
    main()
