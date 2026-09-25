from __future__ import annotations

import json
import os
import re
import ssl
import subprocess
import urllib.request
import zipfile
from pathlib import Path

ssl._create_default_https_context = ssl._create_unverified_context

ROOT = Path(__file__).resolve().parent
SELECTION_FILE = ROOT / "selected-datasets.json"
INSPECT_FILE = ROOT / "candidate-archives.json"
LOG_FILE = ROOT / "logs" / "run-summary.json"
OGR2OGR = Path(r"C:\Program Files\QGIS 3.40.7\bin\ogr2ogr.exe")
OGRINFO = Path(r"C:\Program Files\QGIS 3.40.7\bin\ogrinfo.exe")
PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
USER_AGENT = "portolan-grill-me/1.0"


def build_http_opener() -> urllib.request.OpenerDirector:
    handlers = []
    if PROXY:
        handlers.append(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))

    # Corporate proxy injects TLS certificates not trusted by this Python runtime.
    ssl_context = ssl._create_unverified_context()
    handlers.append(urllib.request.HTTPSHandler(context=ssl_context))
    return urllib.request.build_opener(*handlers)


def fetch_html(url: str) -> str:
    opener = build_http_opener()
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with opener.open(req, timeout=120) as response:
        return response.read().decode("utf-8", errors="replace")


def download_file(url: str, destination: Path) -> None:
    opener = build_http_opener()
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with opener.open(req, timeout=300) as response:
        destination.write_bytes(response.read())


def direct_download_url(asset_page_url: str) -> str | None:
    html = fetch_html(asset_page_url)
    match = re.search(r'<a href="([^"]+)" class="btn btn-primary">Download</a>', html)
    if not match:
        return None
    relative = match.group(1).lstrip("/")
    return f"https://data.geo.ti.ch/{relative}"


def extract_archive(zip_path: Path, output_dir: Path) -> list[Path]:
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(output_dir)
    return [path for path in output_dir.rglob("*") if path.is_file()]


def choose_source_vector(files: list[Path]) -> Path | None:
    priorities = [".gpkg", ".shp", ".xtf", ".itf", ".gml", ".geojson"]
    for suffix in priorities:
        for path in files:
            if path.suffix.lower() == suffix:
                return path
    return None


def layer_name_to_filename(layer_name: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", layer_name.strip())
    return safe.strip("_.-") or "layer"


def list_layers(source: Path) -> list[str]:
    command = [str(OGRINFO), "-ro", str(source)]
    process = subprocess.run(command, capture_output=True, text=True)

    layers: list[str] = []
    text = (process.stdout or "") + "\n" + (process.stderr or "")
    for line in text.splitlines():
        match = re.match(r"\s*\d+:\s+(.+?)\s*$", line)
        if match:
            layers.append(match.group(1).strip())
    return layers


def run_ogr_to_parquet(source: Path, target: Path, layer_name: str) -> tuple[bool, str]:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()
    command = [
        str(OGR2OGR),
        "-f",
        "Parquet",
        str(target),
        str(source),
        layer_name,
        "-lco",
        "COMPRESSION=ZSTD",
        "-lco",
        "GEOMETRY_ENCODING=WKB",
        "-overwrite",
    ]
    process = subprocess.run(command, capture_output=True, text=True)
    message = (process.stdout or "") + (process.stderr or "")
    return process.returncode == 0, message.strip()


def main() -> int:
    if not OGR2OGR.exists():
        raise FileNotFoundError(f"ogr2ogr non trovato: {OGR2OGR}")
    if not OGRINFO.exists():
        raise FileNotFoundError(f"ogrinfo non trovato: {OGRINFO}")

    datasets = json.loads(SELECTION_FILE.read_text(encoding="utf-8"))
    inspect_by_code: dict[str, str] = {}
    if INSPECT_FILE.exists():
        inspect_data = json.loads(INSPECT_FILE.read_text(encoding="utf-8"))
        for entry in inspect_data:
            code = entry.get("code")
            download_url = entry.get("download_url")
            if isinstance(code, str) and isinstance(download_url, str) and download_url:
                inspect_by_code[code] = download_url

    summary: list[dict[str, object]] = []

    for dataset in datasets:
        code = dataset["code"]
        slug = code.lower().replace("-", "_").replace(".", "_")
        row: dict[str, object] = {"code": code, "collection": dataset["collection"]}

        try:
            download_url = inspect_by_code.get(code) or direct_download_url(dataset["asset_page"])
            row["download_url"] = download_url
            if not download_url:
                row["status"] = "failed"
                row["error"] = "Download URL non trovata nella pagina archivio"
                summary.append(row)
                continue

            zip_path = ROOT / "downloads" / f"{slug}.zip"
            work_dir = ROOT / "extract" / slug
            if work_dir.exists():
                for old_file in sorted(work_dir.rglob("*"), reverse=True):
                    if old_file.is_file():
                        old_file.unlink()
                    elif old_file.is_dir():
                        old_file.rmdir()
            work_dir.mkdir(parents=True, exist_ok=True)

            download_file(download_url, zip_path)
            files = extract_archive(zip_path, work_dir)
            source = choose_source_vector(files)
            if not source:
                row["status"] = "failed"
                row["error"] = "Nessun file vettoriale supportato trovato nell'archivio"
                row["archive_files"] = [str(path.relative_to(work_dir)) for path in files]
                summary.append(row)
                continue

            row["source"] = str(source)

            layers = list_layers(source)
            if not layers:
                row["status"] = "failed"
                row["error"] = "Impossibile leggere le layer dal dataset sorgente"
                summary.append(row)
                continue

            outputs: list[str] = []
            layer_failures: list[dict[str, str]] = []
            for layer_name in layers:
                target = ROOT / "parquet" / code.lower().replace("-", "_").replace(".", "_") / f"{layer_name_to_filename(layer_name)}.parquet"
                ok, message = run_ogr_to_parquet(source, target, layer_name)
                if ok:
                    outputs.append(str(target))
                else:
                    layer_failures.append({"layer": layer_name, "message": message})

            row["outputs"] = outputs
            if layer_failures:
                row["layer_failures"] = layer_failures
            row["status"] = "ok" if outputs else "failed"
            row["generated_count"] = len(outputs)
        except Exception as exc:
            row["status"] = "failed"
            row["error"] = str(exc)

        summary.append(row)

    LOG_FILE.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    ok_count = sum(1 for entry in summary if entry.get("status") == "ok")
    fail_count = len(summary) - ok_count
    print(f"GeoParquet generati: {ok_count}")
    print(f"Falliti: {fail_count}")
    print(f"Report: {LOG_FILE}")
    return 0 if fail_count == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
