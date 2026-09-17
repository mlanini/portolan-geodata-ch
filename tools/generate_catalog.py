#!/usr/bin/env python3
"""Generate the geodata.ch Portolan catalog from the manifest.

Reads tools/manifest/catalog.yaml and tools/manifest/datasets.yaml and writes the
whole STAC tree at the repository root: catalog.json, one intermediate catalog per
theme, one collection per dataset, and a README.md + AGENTS.md beside every JSON
(plus a MapLibre style for vector collections).

Documentation and machine metadata are generated together from the one manifest so
they cannot drift (see specs/best-practices/documentation.md in portolan-spec).

Usage:
    python tools/generate_catalog.py            # write the tree
    python tools/generate_catalog.py --check    # fail if the tree is out of date
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
MANIFEST = ROOT / "tools" / "manifest"

PRODUCERS = {
    "swisstopo": {
        "name": "Federal Office of Topography swisstopo",
        "roles": ["producer", "licensor"],
        "url": "https://www.swisstopo.admin.ch",
    },
    "bfs": {
        "name": "Swiss Federal Statistical Office (FSO/BFS)",
        "roles": ["producer", "licensor"],
        "url": "https://www.bfs.admin.ch",
    },
}

MT_JSON = "application/json"
MT_MD = "text/markdown"
MT_HTML = "text/html"
MT_PARQUET = "application/vnd.apache.parquet"
MT_PMTILES = "application/vnd.pmtiles"
MT_STYLE = "application/vnd.mapbox.style+json"
MT_PNG = "image/png"
MT_COG = "image/tiff; application=geotiff; profile=cloud-optimized"


def load_manifest():
    cat = yaml.safe_load((MANIFEST / "catalog.yaml").read_text())["catalog"]
    subs = yaml.safe_load((MANIFEST / "catalog.yaml").read_text())["subcatalogs"]
    ds = yaml.safe_load((MANIFEST / "datasets.yaml").read_text())["datasets"]
    return cat, subs, ds


def providers_for(cat, ds):
    return [PRODUCERS[ds["producer"]], cat["host_provider"]]


def leaf(ds_id: str) -> str:
    return ds_id.split("/")[-1]


def asset_href(cat, ds_id, filename):
    return f"{cat['base_url']}/{ds_id}/{filename}"


def s3_alt(cat, ds_id, filename):
    return {"s3": {"href": f"{cat['s3_base']}/{ds_id}/{filename}", "title": "Direct S3 access"}}


def stac_extensions(cat, ds):
    exts = [cat["portolan_ext"]]
    if ds["data_type"] == "vector" and ds.get("pmtiles_layers"):
        exts.append(cat["extensions"]["web_map_links"])
    if ds.get("table_columns"):
        exts.append(cat["extensions"]["table"])
    if ds["data_type"] in ("vector", "tabular"):
        exts.append(cat["extensions"]["alternate"])
    return exts


def build_assets(cat, ds):
    ds_id = ds["id"]
    lf = leaf(ds_id)
    assets = {}
    dt = ds["data_type"]

    if dt == "vector":
        pq = f"{lf}.parquet"
        assets["data"] = {
            "href": asset_href(cat, ds_id, pq),
            "type": MT_PARQUET,
            "title": f"{ds['title']} (GeoParquet)",
            "description": "GeoParquet 1.1, zstd-compressed, spatially ordered, with a bbox covering column and per-row-group statistics. Produced by the geodata.ch build pipeline.",
            "roles": ["data"],
            "alternate": s3_alt(cat, ds_id, pq),
        }
        if ds.get("pmtiles_layers"):
            pmt = f"{lf}.pmtiles"
            assets["visual"] = {
                "href": asset_href(cat, ds_id, pmt),
                "type": MT_PMTILES,
                "title": f"{ds['title']} (PMTiles)",
                "roles": ["visual"],
                "alternate": s3_alt(cat, ds_id, pmt),
            }
            assets["style-default"] = {
                "href": "./styles/default.json",
                "type": MT_STYLE,
                "title": "Default MapLibre style",
                "roles": ["style", "default"],
            }
        assets["thumbnail"] = {
            "href": "./thumbnail.png",
            "type": MT_PNG,
            "title": "Preview rendered with the default style",
            "roles": ["thumbnail"],
        }

    elif dt == "tabular":
        pq = f"{lf}.parquet"
        assets["data"] = {
            "href": asset_href(cat, ds_id, pq),
            "type": MT_PARQUET,
            "title": f"{ds['title']} (Parquet)",
            "description": "Non-geospatial Parquet table produced by the geodata.ch build pipeline.",
            "roles": ["data"],
            "alternate": s3_alt(cat, ds_id, pq),
        }

    elif dt == "raster":
        assets["item-mirror"] = {
            "href": asset_href(cat, ds_id, "items.parquet"),
            "type": MT_PARQUET,
            "title": "STAC-GeoParquet item mirror",
            "description": "Spatially ordered STAC-GeoParquet copy of every scene item, so all tiles can be queried in one range request. Produced by the pipeline.",
            "roles": ["collection-mirror"],
        }
        assets["thumbnail"] = {
            "href": "./thumbnail.png",
            "type": MT_PNG,
            "title": "Preview mosaic",
            "roles": ["thumbnail"],
        }

    # Provenance assets shared by every collection.
    assets["source"] = {
        "href": ds["product_page"],
        "type": MT_HTML,
        "title": "Authoritative source and original downloads (FileGDB / GeoPackage / INTERLIS XTF / CSV)",
        "roles": ["source"],
    }
    if ds.get("source_stac"):
        assets["metadata-stac"] = {
            "href": f"{cat['bgdi_stac_root']}/collections/{ds['source_stac']}",
            "type": MT_JSON,
            "title": "Source STAC collection (BGDI, machine metadata)",
            "roles": ["metadata"],
        }
    return assets


def build_links(cat, ds):
    ds_id = ds["id"]
    depth = ds_id.count("/")  # collections sit at depth 1 (theme/leaf)
    up = "../" * (depth + 1)
    links = [
        {"rel": "root", "href": f"{up}catalog.json", "type": MT_JSON},
        {"rel": "parent", "href": "../catalog.json", "type": MT_JSON},
    ]
    if ds["data_type"] == "vector" and ds.get("pmtiles_layers"):
        links.append({
            "rel": "pmtiles",
            "href": asset_href(cat, ds_id, f"{leaf(ds_id)}.pmtiles"),
            "type": MT_PMTILES,
            "title": "Web map tiles",
            "pmtiles:layers": ds["pmtiles_layers"],
        })
    links.append({
        "rel": "via",
        "href": ds["product_page"],
        "type": MT_HTML,
        "title": f"Authoritative source ({PRODUCERS[ds['producer']]['name']})",
    })
    if ds.get("source_stac"):
        links.append({
            "rel": "canonical",
            "href": f"{cat['bgdi_stac_root']}/collections/{ds['source_stac']}",
            "type": MT_JSON,
            "title": "Source STAC collection",
        })
    links.append({
        "rel": "license",
        "href": cat["license_href"],
        "type": MT_HTML,
        "title": cat["license_title"],
    })
    links.append({"rel": "agents", "href": "./AGENTS.md", "type": MT_MD, "title": "Guidance for AI agents"})
    links.append({"rel": "describedby", "href": "./README.md", "type": MT_MD, "title": "Human-readable documentation"})
    return links


def build_collection(cat, ds):
    bbox = ds.get("bbox") or cat["extent_ch"]
    col = {
        "type": "Collection",
        "stac_version": "1.1.0",
        "stac_extensions": stac_extensions(cat, ds),
        "id": ds["id"],
        "title": ds["title"],
        "description": ds["description"].strip(),
        "license": cat["license"],
        "keywords": ds.get("keywords", []),
        "updated": cat["updated"],
        "providers": providers_for(cat, ds),
        "extent": {
            "spatial": {"bbox": [bbox]},
            "temporal": {"interval": [ds["temporal"]]},
        },
    }
    if ds.get("table_columns"):
        col["table:columns"] = ds["table_columns"]
    col["assets"] = build_assets(cat, ds)
    col["links"] = build_links(cat, ds)
    return col


def build_subcatalog(cat, sub, datasets):
    children = [d for d in datasets if d["subcatalog"] == sub["id"]]
    links = [
        {"rel": "root", "href": "../catalog.json", "type": MT_JSON},
        {"rel": "parent", "href": "../catalog.json", "type": MT_JSON},
    ]
    for d in children:
        links.append({
            "rel": "child",
            "href": f"./{leaf(d['id'])}/collection.json",
            "type": MT_JSON,
            "title": d["title"],
        })
    links.append({"rel": "agents", "href": "./AGENTS.md", "type": MT_MD, "title": "Guidance for AI agents"})
    links.append({"rel": "describedby", "href": "./README.md", "type": MT_MD, "title": "Human-readable documentation"})
    return {
        "type": "Catalog",
        "stac_version": "1.1.0",
        "stac_extensions": [cat["portolan_ext"]],
        "id": f"geodata-ch-{sub['id']}",
        "title": sub["title"],
        "description": sub["description"].strip(),
        "updated": cat["updated"],
        "links": links,
    }, children


def build_root(cat, subs):
    links = [
        {"rel": "root", "href": "./catalog.json", "type": MT_JSON},
        {"rel": "self", "href": f"{cat['base_url']}/catalog.json", "type": MT_JSON},
    ]
    for sub in subs:
        links.append({
            "rel": "child",
            "href": f"./{sub['id']}/catalog.json",
            "type": MT_JSON,
            "title": sub["title"],
        })
    links.append({"rel": "agents", "href": "./AGENTS.md", "type": MT_MD, "title": "Guidance for AI agents"})
    links.append({"rel": "describedby", "href": "./README.md", "type": MT_MD, "title": "Human-readable documentation"})
    return {
        "type": "Catalog",
        "stac_version": "1.1.0",
        "stac_extensions": [cat["portolan_ext"]],
        "id": cat["id"],
        "title": cat["title"],
        "description": cat["description"].strip(),
        "updated": cat["updated"],
        "links": links,
    }


# --------------------------------------------------------------------------- style
def build_style(ds):
    lf = leaf(ds["id"])
    layers = []
    for name in ds.get("pmtiles_layers", []):
        layers.append({
            "id": name,
            "type": "line",
            "source": "data",
            "source-layer": name,
            "paint": {"line-color": "#d52b1e", "line-width": 1.0},
        })
    return {
        "version": 8,
        "name": f"{ds['title']} — geodata.ch default",
        "sources": {"data": {"type": "vector", "url": f"pmtiles://../{lf}.pmtiles"}},
        "layers": [{"id": "background", "type": "background", "paint": {"background-color": "#f8f8f6"}}] + layers,
    }


# ----------------------------------------------------------------------- markdown
def md_list(items, prefix="- "):
    return "\n".join(f"{prefix}{i}" for i in items)


def schema_table(cols):
    if not cols:
        return "_No columns documented._"
    rows = ["| Column | Type | Description |", "| --- | --- | --- |"]
    for c in cols:
        rows.append(f"| `{c['name']}` | {c['type']} | {c['description']} |")
    return "\n".join(rows)


def originals_table(ds):
    rows = ["| Format | Media type | Title |", "| --- | --- | --- |"]
    for o in ds["originals"]:
        rows.append(f"| {o['format']} | `{o['media_type']}` | {o['title']} |")
    return "\n".join(rows)


def collection_readme(cat, ds):
    lf = leaf(ds["id"])
    rd = ds["readme"]
    dt = ds["data_type"]
    quickstart = ""
    if dt in ("vector", "tabular"):
        quickstart = (
            "```python\n"
            "import duckdb\n"
            "con = duckdb.connect()\n"
            "con.sql(\"INSTALL spatial; LOAD spatial;\")\n"
            f"df = con.sql(\"SELECT * FROM read_parquet('{asset_href(cat, ds['id'], lf + '.parquet')}') LIMIT 100\").df()\n"
            "```"
        )
    else:
        quickstart = (
            "```python\n"
            "# Query every scene from the STAC-GeoParquet item mirror, then open a tile.\n"
            "import duckdb, rioxarray as rxr\n"
            "con = duckdb.connect(); con.sql('INSTALL spatial; LOAD spatial;')\n"
            f"items = con.sql(\"SELECT id, assets FROM read_parquet('{asset_href(cat, ds['id'], 'items.parquet')}') LIMIT 10\").df()\n"
            "# da = rxr.open_rasterio(<cog url from items.assets>)\n"
            "```"
        )
    parts = [
        f"# {ds['title']}",
        "",
        f"> Part of the [geodata.ch](../../README.md) cloud-native catalog of Swiss federal geodata. "
        f"Agents: see [AGENTS.md](./AGENTS.md).",
        "",
        ds["description"].strip(),
        "",
        f"**Coverage.** {rd['numbers']}",
        "",
        f"**Source.** Produced by {PRODUCERS[ds['producer']]['name']} and mirrored here in cloud-native form. "
        f"The authoritative copy and the original downloads live at the [source product page]({ds['product_page']})"
        + (f"; its machine metadata is the [source STAC collection]({cat['bgdi_stac_root']}/collections/{ds['source_stac']})." if ds.get("source_stac") else "."),
        "",
        f"**License.** `{cat['license']}` — [{cat['license_title']}]({cat['license_href']}).",
        "",
        "## Quick start",
        "",
        quickstart,
        "",
        "## Original source formats",
        "",
        "geodata.ch mirrors this dataset from the authoritative swisstopo/BFS downloads. "
        "The originals remain the reference copy:",
        "",
        originals_table(ds),
        "",
        f"Concrete per-release download URLs are resolved from the source STAC by the "
        f"[build pipeline](../../tools/README.md); see also [docs/data-sources.md](../../docs/data-sources.md).",
        "",
    ]
    if ds.get("table_columns"):
        parts += ["## Schema", "", schema_table(ds["table_columns"]), ""]
    parts += [
        "## Coordinate reference system",
        "",
        f"- Source CRS: {ds['crs_source']}",
        f"- Published CRS: {ds['crs_published']}",
        "",
        "## Suggested uses",
        "",
        md_list(rd["suggested_uses"]),
        "",
        "## Limitations and inappropriate uses",
        "",
        md_list(rd["limitations"]),
        "",
    ]
    if rd.get("definitions"):
        parts += ["## Definitions", "", md_list(rd["definitions"]), ""]
    parts += [
        "## Temporal note",
        "",
        ds.get("temporal_note", "See the source for the authoritative update cadence."),
        "",
        "---",
        "",
        "_This page is generated from `tools/manifest/datasets.yaml`. Edit the manifest, not this file._",
        "",
    ]
    return "\n".join(parts)


def collection_agents(cat, ds):
    lf = leaf(ds["id"])
    ag = ds["agents"]
    data_url = asset_href(cat, ds["id"], lf + ".parquet")
    glob_url = f"{cat['base_url']}/{ds['id']}/**/*.parquet"
    parts = [
        f"# AGENTS.md — {ds['title']}",
        "",
        "## What this is and how it connects",
        "",
        ag["context"],
        "",
        f"**Keys.** {ag['key_columns']}",
        "",
        "## Access",
        "",
        f"- Base URL: `{cat['base_url']}/{ds['id']}/`",
        f"- S3: `{cat['s3_base']}/{ds['id']}/`",
        f"- CRS: {ds['crs_published']} (source {ds['crs_source']}).",
        "",
        "## Runnable access patterns",
        "",
    ]
    if ds["data_type"] in ("vector", "tabular"):
        parts += [
            "```python",
            "import duckdb",
            "con = duckdb.connect(); con.sql('INSTALL spatial; LOAD spatial;')",
            f"con.sql(\"SELECT count(*) FROM read_parquet('{data_url}')\").show()",
            "```",
            "",
        ]
    for r in ag.get("recipes", []):
        title = r["title"]
        if "sql" in r:
            body = r["sql"].replace("{data}", data_url).replace("{glob}", glob_url)
            parts += [f"**{title}**", "", "```sql", body, "```", ""]
        elif "code" in r:
            parts += [f"**{title}**", "", "```python", r["code"], "```", ""]
    parts += ["## Quirks and caveats", "", md_list(ag.get("quirks", [])), ""]
    if ds.get("join_note"):
        parts += ["## Join note", "", ds["join_note"], ""]
    if ag.get("related"):
        parts += [
            "## Related collections",
            "",
            md_list([f"`{r}`" for r in ag["related"]]),
            "",
        ]
    parts += [
        "## Provenance",
        "",
        f"Mirror of {PRODUCERS[ds['producer']]['name']} data. Source: {ds['product_page']} . "
        + (f"Source STAC: {cat['bgdi_stac_root']}/collections/{ds['source_stac']} ." if ds.get("source_stac") else "No upstream STAC; see the source page."),
        "",
        "_Generated from `tools/manifest/datasets.yaml`._",
        "",
    ]
    return "\n".join(parts)


def collections_toc(cat, datasets):
    rows = ["| Collection | Type | Geometry | Description |", "| --- | --- | --- | --- |"]
    for d in datasets:
        link = f"[{d['title']}](./{'/'.join(d['id'].split('/')[1:])}/README.md)"
        rows.append(f"| {link} | {d['data_type']} | {d.get('geometry') or '—'} | {d['description'].strip().split('.')[0]}. |")
    return "\n".join(rows)


def subcatalog_readme(cat, sub, children):
    rows = ["| Collection | Type | Description |", "| --- | --- | --- |"]
    for d in children:
        rows.append(f"| [{d['title']}](./{leaf(d['id'])}/README.md) | {d['data_type']} | {d['description'].strip().split('.')[0]}. |")
    return "\n".join([
        f"# {sub['title']}",
        "",
        f"> Part of the [geodata.ch](../README.md) catalog. Agents: [AGENTS.md](./AGENTS.md).",
        "",
        sub["description"].strip(),
        "",
        "## Collections",
        "",
        "\n".join(rows),
        "",
        "_Generated from the manifest under `tools/manifest/`._",
        "",
    ])


def subcatalog_agents(cat, sub, children):
    return "\n".join([
        f"# AGENTS.md — {sub['title']}",
        "",
        sub["description"].strip(),
        "",
        "## Collections in this catalog",
        "",
        md_list([f"`{d['id']}` — {d['title']}" for d in children]),
        "",
        f"All assets live under `{cat['base_url']}/<collection-id>/` (S3: `{cat['s3_base']}/<collection-id>/`).",
        "",
        "See each collection's AGENTS.md for keys, quirks, and query recipes.",
        "",
    ])


def root_readme(cat, subs, datasets):
    return "\n".join([
        f"# {cat['title']}",
        "",
        f"> Agents: start with [AGENTS.md](./AGENTS.md).",
        "",
        cat["description"].strip(),
        "",
        "geodata.ch is a **mirror**: the datasets are produced by swisstopo and the "
        "Federal Statistical Office and republished here in cloud-native formats "
        "(GeoParquet, PMTiles, Cloud-Optimized GeoTIFF). Every collection links back "
        "to its authoritative source and original downloads.",
        "",
        f"- **Storage:** `{cat['s3_base']}` (`{cat['s3_arn']}`), served over HTTPS at `{cat['base_url']}`.",
        f"- **License:** all data under `{cat['license']}` — [{cat['license_title']}]({cat['license_href']}).",
        f"- **Spec:** Portolan `{cat['portolan_ext']}` (STAC 1.1.0).",
        "",
        "## Catalog contents",
        "",
        collections_toc(cat, datasets),
        "",
        "## Where the data comes from",
        "",
        "The datasets originate in the Swiss Federal Spatial Data Infrastructure "
        f"(BGDI). Their authoritative STAC API is at {cat['bgdi_stac_root']} . "
        "Original FileGDB, GeoPackage, and INTERLIS (XTF) downloads, plus ISO 19115 "
        "metadata from geocat.ch, are enumerated per collection and in "
        "[docs/data-sources.md](./docs/data-sources.md).",
        "",
        "## Building and updating",
        "",
        "The catalog metadata is generated from a single manifest and the data assets "
        "are produced by a repeatable pipeline. See [tools/README.md](./tools/README.md). "
        "Integration of cantonal data via geodienste.ch is assessed in "
        "[docs/geodienste-integration.md](./docs/geodienste-integration.md).",
        "",
        "_This page is generated from `tools/manifest/`. Edit the manifest, not this file._",
        "",
    ])


def root_agents(cat, subs, datasets):
    join_lines = [
        "- **`bfs_nummer`** (integer) is the national municipality key. It joins "
        "`boundaries/swissboundaries3d`, `boundaries/municipality-register`, and "
        "`boundaries/ortschaftenverzeichnis-plz`, and reaches almost all Swiss "
        "federal statistics.",
        "- **`egid`** joins `topography/swissbuildings3d` to the federal building & "
        "dwelling register.",
        "- **`plz`** (+`zusatzziffer`) keys postal localities in "
        "`boundaries/ortschaftenverzeichnis-plz`.",
    ]
    return "\n".join([
        "# AGENTS.md — geodata.ch",
        "",
        "Cloud-native mirror of Swiss federal geodata. Query the data directly from "
        "object storage; there is no server.",
        "",
        "## Access",
        "",
        f"- HTTPS base: `{cat['base_url']}`",
        f"- S3 base: `{cat['s3_base']}`",
        f"- Root STAC: `{cat['base_url']}/catalog.json`",
        "- Vector and tabular data are GeoParquet/Parquet (query with DuckDB spatial "
        "or GeoPandas over HTTP range requests). Raster is Cloud-Optimized GeoTIFF "
        "with a STAC-GeoParquet item mirror per collection.",
        "",
        "## Collections",
        "",
        md_list([f"`{d['id']}` — {d['title']} ({d['data_type']})" for d in datasets]),
        "",
        "## Cross-dataset join keys",
        "",
        "\n".join(join_lines),
        "",
        "## Coordinate systems",
        "",
        "Vector/tabular data is published in EPSG:4326 (WGS84). The Swiss source CRS "
        "is EPSG:2056 (CH1903+/LV95), in metres. For area or length, transform to "
        "EPSG:2056 first — `ST_Area` on WGS84 degrees is meaningless. Raster tiles "
        "are kept in EPSG:2056.",
        "",
        "## Example: query one collection",
        "",
        "```python",
        "import duckdb",
        "con = duckdb.connect(); con.sql('INSTALL spatial; LOAD spatial;')",
        f"con.sql(\"SELECT count(*) FROM read_parquet('{cat['base_url']}/boundaries/swissboundaries3d/swissboundaries3d.parquet')\").show()",
        "```",
        "",
        "_Generated from `tools/manifest/`._",
        "",
    ])


# --------------------------------------------------------------------------- write
def write(path: Path, content: str, files: dict):
    files[str(path.relative_to(ROOT))] = content


def write_json(path: Path, obj, files: dict):
    write(path, json.dumps(obj, indent=2, ensure_ascii=False) + "\n", files)


def generate(files: dict):
    cat, subs, datasets = load_manifest()

    write_json(ROOT / "catalog.json", build_root(cat, subs), files)
    write(ROOT / "README.md", root_readme(cat, subs, datasets), files)
    write(ROOT / "AGENTS.md", root_agents(cat, subs, datasets), files)

    for sub in subs:
        subdir = ROOT / sub["id"]
        node, children = build_subcatalog(cat, sub, datasets)
        write_json(subdir / "catalog.json", node, files)
        write(subdir / "README.md", subcatalog_readme(cat, sub, children), files)
        write(subdir / "AGENTS.md", subcatalog_agents(cat, sub, children), files)

    for ds in datasets:
        cdir = ROOT / ds["id"]
        write_json(cdir / "collection.json", build_collection(cat, ds), files)
        write(cdir / "README.md", collection_readme(cat, ds), files)
        write(cdir / "AGENTS.md", collection_agents(cat, ds), files)
        if ds["data_type"] == "vector" and ds.get("pmtiles_layers"):
            write_json(cdir / "styles" / "default.json", build_style(ds), files)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="fail if the tree is stale")
    args = ap.parse_args()

    files: dict[str, str] = {}
    generate(files)

    if args.check:
        stale = []
        for rel, content in files.items():
            p = ROOT / rel
            if not p.exists() or p.read_text() != content:
                stale.append(rel)
        if stale:
            print("Stale or missing generated files:", *stale, sep="\n  ")
            sys.exit(1)
        print(f"OK: {len(files)} generated files are up to date.")
        return

    for rel, content in files.items():
        p = ROOT / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content)
    print(f"Wrote {len(files)} files.")


if __name__ == "__main__":
    main()
