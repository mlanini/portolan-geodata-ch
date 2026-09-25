from __future__ import annotations

import argparse
import html
import json
import os
import re
import subprocess
import sys
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode


PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or "http://proxy-bvcol.admin.ch:8080"
SITE_URL = "https://data.geo.ti.ch/"
GEOPORTALE_URL = "https://www4.ti.ch/dt/sg/sai/ugeo/temi/geoportale-ticino/home"
MAP_URL = "https://map.geo.ti.ch/"
WMS_SERVICE_URL = "https://wms.geo.ti.ch/service"
WMS_CAPABILITIES_URL = f"{WMS_SERVICE_URL}?service=WMS&version=1.3.0&REQUEST=GetCapabilities"
CONDITIONS_URL = "https://www4.ti.ch/dt/sg/sai/ugeo/temi/geoportale-ticino/geoportale/condizioni-utilizzo"


def agents_link(href: str) -> dict[str, str]:
    return {"rel": "agents", "href": href, "type": "text/markdown", "title": "Repository guidance"}


def external_readme_url() -> str:
    try:
        remote = subprocess.check_output(
            ["git", "config", "--get", "remote.origin.url"],
            cwd=repo_root(),
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        remote = ""

    match = re.search(r"github\.com[:/](?P<slug>[^/]+/[^/.]+?)(?:\.git)?$", remote)
    if match:
        return f'https://raw.githubusercontent.com/{match.group("slug")}/main/README.md'

    return "https://raw.githubusercontent.com/mlanini/portolan-geodata-ch/main/README.md"


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def fetch_html(url: str) -> str:
    handlers = []
    if PROXY:
        handlers.append(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    opener = urllib.request.build_opener(*handlers)
    request = urllib.request.Request(url, headers={"User-Agent": "portolan-catalog-generator/1.0"})
    with opener.open(request, timeout=120) as response:
        return response.read().decode("utf-8", errors="replace")


def convert_to_slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower())
    return slug.strip("-")


def get_category_folder(code: str) -> str:
    if code == "CH-mu":
        return "ch-base"
    if code.startswith("CH-041.6") or code.startswith("CH-041.7"):
        return "ch-raster"
    if code.startswith("CH-"):
        return "ch-base"
    if code.startswith("TI-"):
        return "ti-base"
    if code.startswith("AC-"):
        return "ac"
    raise ValueError(f"Unsupported dataset code: {code}")


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def html_decode(value: str) -> str:
    return html.unescape(value).strip()


def asset_key_from_filename(filename: str, existing_keys: set[str]) -> str:
    stem = Path(filename).stem
    key = convert_to_slug(stem).replace("-", "_") or "data"
    candidate = key
    index = 2
    while candidate in existing_keys:
        candidate = f"{key}_{index}"
        index += 1
    return candidate


def asset_media_type(href: str) -> str:
    lowered = href.lower()
    if lowered.endswith(".tif") or lowered.endswith(".tiff"):
        if "/cog/" in lowered:
            return "image/tiff; application=geotiff; profile=cloud-optimized"
        return "image/tiff; application=geotiff"
    if lowered.endswith(".zip"):
        return "application/zip"
    if lowered.endswith(".xtf"):
        return "application/interlis"
    return "application/octet-stream"


def preview_dimensions(bbox: tuple[float, float, float, float]) -> tuple[int, int]:
    minx, miny, maxx, maxy = bbox
    width_span = max(maxx - minx, 0.0)
    height_span = max(maxy - miny, 0.0)
    if width_span == 0 or height_span == 0:
        return 384, 384

    max_side = 384
    if width_span >= height_span:
        width = max_side
        height = max(256, round(max_side * height_span / width_span))
    else:
        height = max_side
        width = max(256, round(max_side * width_span / height_span))
    return width, height


def parse_wms_layers(capabilities_xml: str) -> dict[str, dict[str, object]]:
    namespaces = {"wms": "http://www.opengis.net/wms"}
    root = ET.fromstring(capabilities_xml)
    layer_map: dict[str, dict[str, object]] = {}

    for layer in root.findall("./wms:Capability/wms:Layer/wms:Layer", namespaces):
        title = layer.findtext("wms:Title", default="", namespaces=namespaces)
        name = layer.findtext("wms:Name", default="", namespaces=namespaces)
        match = re.match(r"\[(?P<code>[^\]]+?)\s*\]\s*", title)
        bbox_node = layer.find("wms:BoundingBox[@CRS='EPSG:2056']", namespaces)
        if not match or not name or bbox_node is None:
            continue

        try:
            bbox = (
                float(bbox_node.attrib["minx"]),
                float(bbox_node.attrib["miny"]),
                float(bbox_node.attrib["maxx"]),
                float(bbox_node.attrib["maxy"]),
            )
        except (KeyError, ValueError):
            continue

        layer_map.setdefault(
            match.group("code").strip(),
            {
                "name": name,
                "title": title,
                "bbox": bbox,
            },
        )

    return layer_map


def build_preview_asset(item: dict[str, str], wms_layers: dict[str, dict[str, object]]) -> dict[str, object] | None:
    layer = wms_layers.get(item["code"])
    if not layer:
        return None

    bbox = layer["bbox"]
    if not isinstance(bbox, tuple):
        return None

    width, height = preview_dimensions(bbox)
    href = f"{WMS_SERVICE_URL}?{urlencode({
        'service': 'WMS',
        'version': '1.3.0',
        'request': 'GetMap',
        'layers': str(layer['name']),
        'styles': '',
        'crs': 'EPSG:2056',
        'bbox': ','.join(str(value) for value in bbox),
        'width': str(width),
        'height': str(height),
        'format': 'image/png',
        'transparent': 'true',
    })}"
    return {
        "href": href,
        "type": "image/png",
        "title": f'Anteprima WMS - {item["title"]}',
        "roles": ["thumbnail"],
    }


def build_geoparquet_asset(item: dict[str, str]) -> dict[str, object] | None:
    geoparquet_slug = item["code"].lower().replace("-", "_").replace(".", "_")
    geoparquet_dir = repo_root() / "cloud-optimized" / "parquet" / geoparquet_slug
    if not geoparquet_dir.exists():
        return None

    collection_dir = Path(item["collectionPath"]).parent
    href = os.path.relpath(
        geoparquet_dir,
        start=collection_dir,
    ).replace(os.sep, "/")
    if not href.endswith("/"):
        href += "/"

    return {
        "href": href,
        "title": "GeoParquet selezionato",
        "roles": ["data"],
    }


def parse_dataset_assets(page: str, page_html: str) -> dict[str, dict[str, object]]:
    assets: dict[str, dict[str, object]] = {}

    zip_pattern = re.compile(
        r'<td width="30%"><a href="\?p=[^"]+(?:&|&amp;)f=([^"]+)">([^<]+)</a></td>',
        re.IGNORECASE,
    )
    for match in zip_pattern.finditer(page_html):
        filename = html_decode(match.group(2))
        href = f"{SITE_URL}?{urlencode({'p': page, 'f': html_decode(match.group(1))})}"
        key = asset_key_from_filename(filename, set(assets.keys()))
        assets[key] = {
            "href": href,
            "type": asset_media_type(href),
            "title": filename,
            "roles": ["data"],
        }

    direct_pattern = re.compile(
        r'<td width="30%">([^<]+)</td>.*?<span id="link-\d+"[^>]*>(https://[^<]+)</span>',
        re.IGNORECASE | re.DOTALL,
    )
    for match in direct_pattern.finditer(page_html):
        filename = html_decode(match.group(1))
        href = html_decode(match.group(2))
        key = asset_key_from_filename(filename, set(assets.keys()))
        assets[key] = {
            "href": href,
            "type": asset_media_type(href),
            "title": filename,
            "roles": ["data"],
        }

    return assets


def merge_assets(existing: dict[str, object] | None, generated: dict[str, dict[str, object]]) -> dict[str, object]:
    merged: dict[str, object] = dict(existing or {})
    href_to_key = {
        value.get("href"): key
        for key, value in merged.items()
        if isinstance(value, dict) and value.get("href")
    }

    for key, asset in generated.items():
        href = asset.get("href")
        if href in href_to_key:
            continue
        candidate = key
        suffix = 2
        while candidate in merged:
            candidate = f"{key}_{suffix}"
            suffix += 1
        merged[candidate] = asset

    return merged


def merge_collection(existing: dict[str, object], generated: dict[str, object]) -> dict[str, object]:
    merged = dict(existing)
    generated_assets = generated.get("assets")
    if isinstance(generated_assets, dict) and generated_assets:
        merged["assets"] = merge_assets(merged.get("assets") if isinstance(merged.get("assets"), dict) else None, generated_assets)
    return merged


def parse_datasets(page_html: str) -> list[dict[str, str]]:
    pattern = re.compile(
        r'<tr>\s*<td width="30%"><a href="\?p=([^"]+)">([^<]+)</a></td>\s*'
        r'<td width="30%">([^<]+)</td>\s*<td width="40%">([^<]+)</td>\s*</tr>',
        re.IGNORECASE | re.DOTALL,
    )
    datasets: list[dict[str, str]] = []
    for match in pattern.finditer(page_html):
        page = html_decode(match.group(1))
        code = html_decode(match.group(2))
        version = html_decode(match.group(3))
        title = html_decode(match.group(4))
        datasets.append(
            {
                "code": code,
                "version": version,
                "title": title,
                "page": page,
                "categoryFolder": get_category_folder(code),
            }
        )
    datasets.sort(key=lambda item: (item["categoryFolder"], item["code"]))
    return datasets


def build_dataset_records(datasets: list[dict[str, str]]) -> list[dict[str, str]]:
    path_overrides = {
        "CH-063.1": "ch-base/ch-063-1-suddivisioni-amministrative",
        "CH-181.1": "ch-base/ch-181-1-cap-localita",
        "TI-028b.1": "ti-base/ti-028b-1-piani-regolatori",
        "TI-034.1": "ti-base/ti-034-1-carta-pericoli-gradi",
        "AC-009.1": "ac/ac-009-1-piano-direttore-cantonale",
        "AC-077.1": "ac/ac-077-1-repertorio-toponomastico-ticinese",
        "CH-041.6": "ch-raster/ch-041-6r-swissalti3d",
        "CH-041.7": "ch-raster/ch-041-7r-swisssurface3d",
        "CH-041.6R": "ch-raster/ch-041-6r-swissaltiregio",
    }

    records: list[dict[str, str]] = []
    for dataset in datasets:
        relative_path = path_overrides.get(dataset["code"], f'{dataset["categoryFolder"]}/{convert_to_slug(dataset["code"])}')
        collection_path = repo_root() / relative_path
        records.append(
            {
                **dataset,
                "relativePath": relative_path,
                "collectionPath": str(collection_path),
            }
        )
    return records


def category_definitions() -> dict[str, dict[str, str]]:
    return {
        "ch-base": {
            "title": "CH - Geodati di base di diritto federale, competenza cantonale",
            "description": "Catalogo dei geodati CH pubblicati da data.geo.ti.ch.",
        },
        "ti-base": {
            "title": "TI - Geodati di base di diritto cantonale",
            "description": "Catalogo dei geodati TI pubblicati da data.geo.ti.ch.",
        },
        "ac": {
            "title": "AC - Geodati dell'Amministrazione cantonale",
            "description": "Catalogo dei geodati AC pubblicati da data.geo.ti.ch.",
        },
        "ch-raster": {
            "title": "CH - Geodati raster (Cloud Optimized GeoTIFF)",
            "description": "Catalogo dei geodati raster CH pubblicati da data.geo.ti.ch.",
        },
    }


def build_category_catalog(category: str, items: list[dict[str, str]], definitions: dict[str, dict[str, str]]) -> dict[str, object]:
    links: list[dict[str, str]] = [
        {"rel": "root", "href": "../catalog.json", "type": "application/json"},
        {"rel": "parent", "href": "../catalog.json", "type": "application/json"},
        {"rel": "self", "href": "./catalog.json", "type": "application/json"},
        agents_link("../AGENTS.md"),
    ]

    for item in items:
        leaf = item["relativePath"].split("/", 1)[1]
        links.append(
            {
                "rel": "child",
                "href": f"./{leaf}/collection.json",
                "type": "application/json",
                "title": f'{item["code"]} - {item["title"]}',
            }
        )

    return {
        "type": "Catalog",
        "stac_version": "1.1.0",
        "id": category,
        "title": definitions[category]["title"],
        "description": definitions[category]["description"],
        "links": links,
    }


def build_root_catalog(definitions: dict[str, dict[str, str]]) -> dict[str, object]:
    return {
        "type": "Catalog",
        "stac_version": "1.1.0",
        "stac_extensions": ["https://schemas.portolan-sdi.org/portolan/v0.2.0/schema.json"],
        "id": "geodata-ch-ti-complete",
        "title": "Portolan Geodata CH/TI - catalogo completo data.geo.ti.ch",
        "description": "Catalogo STAC completo dei geodati del portale data.geo.ti.ch, ricavato dall'indice ufficiale e arricchito con riferimenti del Geoportale Ticino e di map.geo.ti.ch.",
        "updated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "links": [
            {"rel": "root", "href": "./catalog.json", "type": "application/json"},
            {"rel": "self", "href": "./catalog.json", "type": "application/json"},
            agents_link("./AGENTS.md"),
            {"rel": "child", "href": "./ch-base/catalog.json", "type": "application/json", "title": definitions["ch-base"]["title"]},
            {"rel": "child", "href": "./ti-base/catalog.json", "type": "application/json", "title": definitions["ti-base"]["title"]},
            {"rel": "child", "href": "./ac/catalog.json", "type": "application/json", "title": definitions["ac"]["title"]},
            {"rel": "child", "href": "./ch-raster/catalog.json", "type": "application/json", "title": definitions["ch-raster"]["title"]},
            {"rel": "related", "href": GEOPORTALE_URL, "type": "text/html", "title": "Geoportale Ticino"},
            {"rel": "related", "href": MAP_URL, "type": "text/html", "title": "Geoportale Ticino - Mappa"},
            {"rel": "related", "href": CONDITIONS_URL, "type": "text/html", "title": "Condizioni di utilizzo"},
            {"rel": "related", "href": SITE_URL, "type": "text/html", "title": "Portale per il download dei geodati"},
            {"rel": "describedby", "href": "./README.md", "type": "text/markdown", "title": "Human-readable documentation"},
        ],
    }


def build_collection(item: dict[str, str], page_html: str, wms_layers: dict[str, dict[str, object]]) -> dict[str, object]:
    describedby_url = external_readme_url()
    assets = parse_dataset_assets(item["page"], page_html)
    geoparquet_asset = build_geoparquet_asset(item)
    if geoparquet_asset:
        assets["geoparquet"] = geoparquet_asset
    preview_asset = build_preview_asset(item, wms_layers)
    if preview_asset:
        assets["thumbnail"] = preview_asset
    return {
        "type": "Collection",
        "stac_version": "1.1.0",
        "id": item["relativePath"],
        "title": f'{item["code"]} - {item["title"]}',
        "description": f'Geodato pubblicato su data.geo.ti.ch: {item["title"]}.',
        "license": "other",
        "extent": {
            "spatial": {"bbox": [[8.3, 45.8, 9.3, 46.7]]},
            "temporal": {"interval": [[None, None]]},
        },
        "keywords": [item["code"], item["title"], item["categoryFolder"]],
        "assets": assets,
        "links": [
            {"rel": "root", "href": "../../catalog.json", "type": "application/json"},
            {"rel": "parent", "href": "../catalog.json", "type": "application/json"},
            {"rel": "self", "href": "./collection.json", "type": "application/json"},
            agents_link("../../AGENTS.md"),
            {"rel": "describedby", "href": describedby_url, "type": "text/markdown", "title": "Human-readable documentation"},
            {"rel": "related", "href": GEOPORTALE_URL, "type": "text/html", "title": "Geoportale Ticino"},
            {"rel": "related", "href": MAP_URL, "type": "text/html", "title": "Geoportale Ticino - Mappa"},
            {"rel": "related", "href": CONDITIONS_URL, "type": "text/html", "title": "Condizioni di utilizzo"},
            {"rel": "via", "href": f'https://data.geo.ti.ch/?p={item["page"]}', "type": "text/html", "title": "Scheda dataset su data.geo.ti.ch"},
        ],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the Portolan catalog from data.geo.ti.ch")
    parser.add_argument("--force", action="store_true", help="Overwrite curated collection files as well")
    args = parser.parse_args(argv)

    root = repo_root()
    definitions = category_definitions()
    datasets = parse_datasets(fetch_html(SITE_URL))
    records = build_dataset_records(datasets)
    wms_layers = parse_wms_layers(fetch_html(WMS_CAPABILITIES_URL))

    for category in definitions:
        category_items = [item for item in records if item["categoryFolder"] == category]
        category_dir = root / category
        category_dir.mkdir(parents=True, exist_ok=True)
        write_json(category_dir / "catalog.json", build_category_catalog(category, category_items, definitions))

    write_json(root / "catalog.json", build_root_catalog(definitions))

    for item in records:
        collection_file = Path(item["collectionPath"]) / "collection.json"
        page_html = fetch_html(f'{SITE_URL}?{urlencode({"p": item["page"]})}')
        generated_collection = build_collection(item, page_html, wms_layers)
        if collection_file.exists() and not args.force:
            existing_collection = json.loads(collection_file.read_text(encoding="utf-8"))
            write_json(collection_file, merge_collection(existing_collection, generated_collection))
            continue
        write_json(collection_file, generated_collection)

    print(f"Generated/updated catalog with {len(records)} datasets.")
    print(json.dumps({"totalDatasets": len(records), "categories": list(definitions.keys())}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())