from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or "http://proxy-bvcol.admin.ch:8080"
SITE_URL = "https://data.geo.ti.ch/"
GEOPORTALE_URL = "https://www4.ti.ch/dt/sg/sai/ugeo/temi/geoportale-ticino/home"
MAP_URL = "https://map.geo.ti.ch/"
CONDITIONS_URL = "https://www4.ti.ch/dt/sg/sai/ugeo/temi/geoportale-ticino/geoportale/condizioni-utilizzo"


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


def build_collection(item: dict[str, str]) -> dict[str, object]:
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
        "links": [
            {"rel": "root", "href": "../../catalog.json", "type": "application/json"},
            {"rel": "parent", "href": "../catalog.json", "type": "application/json"},
            {"rel": "self", "href": "./collection.json", "type": "application/json"},
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

    for category in definitions:
        category_items = [item for item in records if item["categoryFolder"] == category]
        category_dir = root / category
        category_dir.mkdir(parents=True, exist_ok=True)
        write_json(category_dir / "catalog.json", build_category_catalog(category, category_items, definitions))

    write_json(root / "catalog.json", build_root_catalog(definitions))

    for item in records:
        collection_file = Path(item["collectionPath"]) / "collection.json"
        if item["code"] in {"CH-063.1", "CH-181.1", "TI-028b.1", "TI-034.1", "AC-009.1", "AC-077.1", "CH-041.6", "CH-041.7", "CH-041.6R"} and collection_file.exists() and not args.force:
            continue
        if collection_file.exists() and not args.force:
            continue
        write_json(collection_file, build_collection(item))

    print(f"Generated/updated catalog with {len(records)} datasets.")
    print(json.dumps({"totalDatasets": len(records), "categories": list(definitions.keys())}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())