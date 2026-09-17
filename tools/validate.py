#!/usr/bin/env python3
"""Offline validation for the geodata.ch catalog.

Checks what can be verified without the data bytes or network:
  - every catalog.json / collection.json is valid JSON and STAC 1.1.0 typed
  - required Portolan structure (title, description, providers, license, links)
  - every relative structural / doc / style link resolves to a file on disk
  - AGENTS.md and README.md exist beside every node
  - assets carry href, type, and at least one role; https (not s3) for absolute
  - the Portolan extension URI is declared on catalogs and collections

It does NOT check byte-level requirements (GeoParquet ordering, COG stats,
checksums); those run in the data pass of the real validator (rashid) after the
build pipeline produces the assets.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
PORTOLAN_PREFIX = "https://schemas.portolan-sdi.org/portolan/"
errors: list[str] = []
warnings: list[str] = []


def err(msg): errors.append(msg)
def warn(msg): warnings.append(msg)


def load(path: Path):
    try:
        return json.loads(path.read_text())
    except Exception as e:  # noqa: BLE001
        err(f"{path.relative_to(ROOT)}: invalid JSON: {e}")
        return None


def is_remote(href: str) -> bool:
    return urlparse(href).scheme in ("http", "https", "s3", "gs")


def check_links_resolve(path: Path, obj):
    base = path.parent
    for link in obj.get("links", []):
        rel, href = link.get("rel"), link.get("href", "")
        if not href:
            err(f"{path.relative_to(ROOT)}: link rel={rel} has no href")
            continue
        if rel == "self":
            if not href.startswith("http"):
                err(f"{path.relative_to(ROOT)}: self link must be absolute https")
            continue
        if is_remote(href):
            continue  # external (via/canonical/license) — not resolved offline
        target = (base / href).resolve()
        if not target.exists():
            err(f"{path.relative_to(ROOT)}: link rel={rel} -> {href} does not resolve")


def check_doc_files(path: Path):
    for fn in ("README.md", "AGENTS.md"):
        if not (path.parent / fn).exists():
            err(f"{path.relative_to(ROOT)}: missing {fn}")


def check_common(path: Path, obj, is_collection: bool):
    if obj.get("stac_version") != "1.1.0":
        err(f"{path.relative_to(ROOT)}: stac_version must be 1.1.0")
    if not any(u.startswith(PORTOLAN_PREFIX) for u in obj.get("stac_extensions", [])):
        err(f"{path.relative_to(ROOT)}: missing Portolan extension URI")
    if not obj.get("title"):
        err(f"{path.relative_to(ROOT)}: missing title")
    if not obj.get("description"):
        err(f"{path.relative_to(ROOT)}: missing description")
    rels = [l.get("rel") for l in obj.get("links", [])]
    for req in ("root", "agents", "describedby"):
        if req not in rels:
            err(f"{path.relative_to(ROOT)}: missing '{req}' link")
    check_links_resolve(path, obj)
    check_doc_files(path)


def check_collection(path: Path, obj):
    check_common(path, obj, True)
    # license
    lic = obj.get("license")
    if not lic:
        err(f"{path.relative_to(ROOT)}: collection missing license")
    if lic == "other" and not any(l.get("rel") == "license" for l in obj["links"]):
        err(f"{path.relative_to(ROOT)}: license 'other' requires a license link")
    # providers: >=1 producer, exactly one host, host last
    provs = obj.get("providers", [])
    roles = [set(p.get("roles", [])) for p in provs]
    if not provs:
        err(f"{path.relative_to(ROOT)}: no providers")
    else:
        hosts = [i for i, r in enumerate(roles) if "host" in r]
        if len(hosts) != 1:
            err(f"{path.relative_to(ROOT)}: must have exactly one host provider")
        elif hosts[0] != len(provs) - 1:
            err(f"{path.relative_to(ROOT)}: host provider must be listed last")
        if not any("producer" in r for r in roles):
            err(f"{path.relative_to(ROOT)}: no producer provider")
    # extent bbox sane WGS84
    try:
        bbox = obj["extent"]["spatial"]["bbox"][0]
        w, s, e, n = bbox[:4]
        if not (-180 <= w <= 180 and -180 <= e <= 180 and -90 <= s <= 90 and -90 <= n <= 90 and s <= n):
            err(f"{path.relative_to(ROOT)}: bbox not valid WGS84: {bbox}")
    except Exception:  # noqa: BLE001
        err(f"{path.relative_to(ROOT)}: missing/invalid spatial extent")
    # assets
    assets = obj.get("assets", {})
    if not assets:
        err(f"{path.relative_to(ROOT)}: collection has no assets")
    for key, a in assets.items():
        href = a.get("href", "")
        if not href:
            err(f"{path.relative_to(ROOT)}: asset {key} missing href")
        if not a.get("type"):
            err(f"{path.relative_to(ROOT)}: asset {key} missing type")
        if not a.get("roles"):
            err(f"{path.relative_to(ROOT)}: asset {key} missing roles")
        if urlparse(href).scheme == "s3":
            err(f"{path.relative_to(ROOT)}: asset {key} href must be https, not s3 (use alternate)")
    # data-type specific
    dt_tabular = "table:columns" in obj and not any(
        "visual" in a.get("roles", []) for a in assets.values()
    )
    has_geom_asset = any("data" in a.get("roles", []) for a in assets.values())
    is_raster = any("collection-mirror" in a.get("roles", []) for a in assets.values())
    if not is_raster and not dt_tabular and has_geom_asset:
        # vector: needs visual + style + thumbnail + pmtiles link
        if not any("visual" in a.get("roles", []) for a in assets.values()):
            warn(f"{path.relative_to(ROOT)}: vector collection lacks a visual (PMTiles) asset")
        if not any("style" in a.get("roles", []) for a in assets.values()):
            err(f"{path.relative_to(ROOT)}: vector collection lacks a style asset")
        if not any("thumbnail" in a.get("roles", []) for a in assets.values()):
            err(f"{path.relative_to(ROOT)}: geospatial collection lacks a thumbnail asset")
        # pmtiles link + non-empty layers
        pm = [l for l in obj["links"] if l.get("rel") == "pmtiles"]
        if pm and not pm[0].get("pmtiles:layers"):
            err(f"{path.relative_to(ROOT)}: pmtiles link has empty pmtiles:layers")


def check_markdown_links():
    import re
    pattern = re.compile(r"\[[^\]]+\]\((\.[^)]+)\)")
    for md in ROOT.rglob("*.md"):
        if ".git" in md.parts or "/tmp" in str(md):
            continue
        for m in pattern.finditer(md.read_text()):
            href = m.group(1).split("#")[0]
            if not href:
                continue
            target = (md.parent / href).resolve()
            if not target.exists():
                err(f"{md.relative_to(ROOT)}: markdown link -> {href} does not resolve")


def main():
    n_cat = n_col = 0
    for path in sorted(ROOT.rglob("catalog.json")):
        obj = load(path)
        if obj is None:
            continue
        if obj.get("type") != "Catalog":
            err(f"{path.relative_to(ROOT)}: type must be Catalog")
        check_common(path, obj, False)
        n_cat += 1
    for path in sorted(ROOT.rglob("collection.json")):
        obj = load(path)
        if obj is None:
            continue
        if obj.get("type") != "Collection":
            err(f"{path.relative_to(ROOT)}: type must be Collection")
        check_collection(path, obj)
        n_col += 1

    check_markdown_links()

    print(f"Checked {n_cat} catalogs and {n_col} collections.")
    for w in warnings:
        print("WARN:", w)
    if errors:
        print(f"\n{len(errors)} ERROR(S):")
        for e in errors:
            print("  -", e)
        sys.exit(1)
    print(f"OK — no errors ({len(warnings)} warnings).")


if __name__ == "__main__":
    main()
