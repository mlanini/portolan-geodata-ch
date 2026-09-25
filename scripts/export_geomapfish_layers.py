from __future__ import annotations

import argparse
import csv
import html
import json
import os
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any
from urllib.parse import urlencode, urljoin, urlparse


DEFAULT_PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY") or "http://proxy-bvcol.admin.ch:8080"
DEFAULT_BASE_URL = "https://map.geo.ti.ch/"
DEFAULT_INTERFACE = "desktop"
DEFAULT_JSON_OUTPUT = "cloud-optimized/logs/geomapfish-published-layers.json"
DEFAULT_CSV_OUTPUT = "cloud-optimized/logs/geomapfish-published-layers.csv"
USER_AGENT = "portolan-geomapfish-layer-exporter/1.0"


def repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


def build_opener(proxy: str | None) -> urllib.request.OpenerDirector:
    handlers: list[Any] = []
    if proxy:
        handlers.append(urllib.request.ProxyHandler({"http": proxy, "https": proxy}))
    return urllib.request.build_opener(*handlers)


def fetch_json(opener: urllib.request.OpenerDirector, url: str) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with opener.open(request, timeout=120) as response:
        payload = response.read().decode("utf-8", errors="replace")
    return json.loads(payload)


def fetch_text(opener: urllib.request.OpenerDirector, url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with opener.open(request, timeout=120) as response:
        return response.read().decode("utf-8", errors="replace")


def make_dynamic_url(base_url: str, interface: str) -> str:
    return urljoin(base_url, f"dynamic.json?{urlencode({'interface': interface})}")


def resolve_tree_url(base_url: str, tree_url: str) -> str:
    parsed = urlparse(tree_url)
    if parsed.scheme and parsed.netloc:
        return tree_url
    return urljoin(base_url, tree_url)


def json_compact(value: Any) -> str | None:
    if value is None:
        return None
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def layer_name_from_node(node: dict[str, Any]) -> str | None:
    for key in ("layer", "layers"):
        value = node.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def metadata_url_from_node(node: dict[str, Any]) -> str | None:
    metadata = node.get("metadata")
    if isinstance(metadata, dict):
        url = metadata.get("metadataUrl")
        if isinstance(url, str) and url.strip():
            return url.strip()
    return None


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def strip_tags(value: str) -> str:
    value = re.sub(r"<script\b[^>]*>.*?</script>", " ", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"<style\b[^>]*>.*?</style>", " ", value, flags=re.IGNORECASE | re.DOTALL)
    value = re.sub(r"<[^>]+>", " ", value)
    return normalize_text(html.unescape(value))


def extract_date_fields_from_html(page_html: str) -> dict[str, str | None]:
    html_text = page_html
    text = strip_tags(page_html)

    def find_by_table_label(label_pattern: str) -> str | None:
        pattern = re.compile(
            rf"<t[hd][^>]*>\s*{label_pattern}\s*</t[hd]>\s*<t[hd][^>]*>(.*?)</t[hd]>",
            flags=re.IGNORECASE | re.DOTALL,
        )
        match = pattern.search(html_text)
        if not match:
            return None
        value = strip_tags(match.group(1))
        return value or None

    def find_in_plain_text(label_pattern: str) -> str | None:
        pattern = re.compile(rf"{label_pattern}\s*[:\-]?\s*([^\n\r\|;]+)", flags=re.IGNORECASE)
        match = pattern.search(text)
        if not match:
            return None
        value = normalize_text(match.group(1))
        return value or None

    def find_value(*label_patterns: str) -> str | None:
        for label in label_patterns:
            value = find_by_table_label(label)
            if value:
                return value
        for label in label_patterns:
            value = find_in_plain_text(label)
            if value:
                return value
        return None

    return {
        "publication_date": find_value(r"Data\s+di\s+pubblicazione", r"Publication\s+date"),
        "last_update_date": find_value(
            r"Data\s+ultimo\s+aggiornamento",
            r"Ultimo\s+aggiornamento",
            r"Data\s+aggiornamento",
            r"Last\s+update",
        ),
        "revision": find_value(r"Revisione", r"Versione", r"Revision"),
    }


def enrich_rows_with_metadata_dates(opener: urllib.request.OpenerDirector, rows: list[dict[str, Any]]) -> None:
    cache: dict[str, dict[str, str | None]] = {}
    for row in rows:
        metadata_url = row.get("metadata_url")
        if not isinstance(metadata_url, str) or not metadata_url:
            row["publication_date"] = None
            row["last_update_date"] = None
            row["revision"] = None
            continue

        if metadata_url not in cache:
            try:
                page_html = fetch_text(opener, metadata_url)
                cache[metadata_url] = extract_date_fields_from_html(page_html)
            except Exception:
                cache[metadata_url] = {
                    "publication_date": None,
                    "last_update_date": None,
                    "revision": None,
                }

        row["publication_date"] = cache[metadata_url]["publication_date"]
        row["last_update_date"] = cache[metadata_url]["last_update_date"]
        row["revision"] = cache[metadata_url]["revision"]


def build_group_path(path_nodes: list[str]) -> str:
    return " > ".join(path_nodes)


def walk_theme_nodes(
    node: dict[str, Any],
    theme_name: str,
    path_nodes: list[str],
    rows: list[dict[str, Any]],
    inherited_metadata_url: str | None = None,
) -> None:
    node_name = node.get("name")
    current_path_nodes = path_nodes[:]
    if isinstance(node_name, str) and node_name.strip():
        current_path_nodes.append(node_name.strip())

    node_metadata_url = metadata_url_from_node(node)
    current_metadata_url = node_metadata_url or inherited_metadata_url

    layer_name = layer_name_from_node(node)
    if layer_name:
        row = {
            "theme": theme_name,
            "group_path": build_group_path(path_nodes),
            "display_name": node.get("name"),
            "layer_name": layer_name,
            "id": node.get("id"),
            "type": node.get("type"),
            "service_url": node.get("url"),
            "public": node.get("public"),
            "image_type": node.get("imageType"),
            "min_resolution_hint": node.get("minResolutionHint"),
            "max_resolution_hint": node.get("maxResolutionHint"),
            "queryable": node.get("queryable"),
            "ogc_server": node.get("ogcServer"),
            "metadata_url": current_metadata_url,
            "metadata_json": json_compact(node.get("metadata")),
            "dimensions_json": json_compact(node.get("dimensions")),
            "child_layers_json": json_compact(node.get("childLayers")),
        }
        rows.append(row)

    children = node.get("children")
    if isinstance(children, list):
        for child in children:
            if isinstance(child, dict):
                walk_theme_nodes(child, theme_name, current_path_nodes, rows, current_metadata_url)


def extract_rows(tree_payload: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    themes = tree_payload.get("themes")
    if not isinstance(themes, list):
        return rows

    for theme in themes:
        if not isinstance(theme, dict):
            continue
        theme_name = str(theme.get("name", "")).strip() or "<unnamed-theme>"
        walk_theme_nodes(theme, theme_name, [theme_name], rows)

    rows.sort(key=lambda item: (
        str(item.get("theme", "")),
        str(item.get("group_path", "")),
        str(item.get("display_name", "")),
        str(item.get("layer_name", "")),
    ))
    return rows


def write_json(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "theme",
        "group_path",
        "display_name",
        "layer_name",
        "id",
        "type",
        "service_url",
        "public",
        "image_type",
        "min_resolution_hint",
        "max_resolution_hint",
        "queryable",
        "ogc_server",
        "metadata_url",
        "publication_date",
        "last_update_date",
        "revision",
        "metadata_json",
        "dimensions_json",
        "child_layers_json",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export published layers from a GeoMapFish viewer to JSON and CSV."
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Base URL of GeoMapFish viewer (default: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--interface",
        default=DEFAULT_INTERFACE,
        help=f"GeoMapFish interface name (default: {DEFAULT_INTERFACE})",
    )
    parser.add_argument(
        "--proxy",
        default=DEFAULT_PROXY,
        help="HTTP/HTTPS proxy URL. Use empty string to disable proxy.",
    )
    parser.add_argument(
        "--json-output",
        default=DEFAULT_JSON_OUTPUT,
        help=f"Output JSON path, relative to repo root (default: {DEFAULT_JSON_OUTPUT})",
    )
    parser.add_argument(
        "--csv-output",
        default=DEFAULT_CSV_OUTPUT,
        help=f"Output CSV path, relative to repo root (default: {DEFAULT_CSV_OUTPUT})",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    base_url = args.base_url.rstrip("/") + "/"
    proxy = args.proxy.strip() or None

    opener = build_opener(proxy)

    dynamic_url = make_dynamic_url(base_url, args.interface)
    dynamic_payload = fetch_json(opener, dynamic_url)

    constants = dynamic_payload.get("constants")
    if not isinstance(constants, dict):
        print("Invalid dynamic.json payload: missing 'constants'.", file=sys.stderr)
        return 1

    tree_url = constants.get("gmfTreeUrl")
    if not isinstance(tree_url, str) or not tree_url.strip():
        print("Invalid dynamic.json payload: missing 'constants.gmfTreeUrl'.", file=sys.stderr)
        return 1

    resolved_tree_url = resolve_tree_url(base_url, tree_url)
    tree_payload = fetch_json(opener, resolved_tree_url)

    rows = extract_rows(tree_payload)
    enrich_rows_with_metadata_dates(opener, rows)

    root = repo_root()
    json_path = root / args.json_output
    csv_path = root / args.csv_output

    write_json(json_path, rows)
    write_csv(csv_path, rows)

    print(f"dynamic_url={dynamic_url}")
    print(f"tree_url={resolved_tree_url}")
    print(f"layers_exported={len(rows)}")
    print(f"json={json_path}")
    print(f"csv={csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
