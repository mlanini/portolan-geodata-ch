from __future__ import annotations

import json
import os
import re
import ssl
import subprocess
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ssl._create_default_https_context = ssl._create_unverified_context

ROOT = Path(__file__).resolve().parent
SELECTION_FILE = ROOT / "selected-datasets.json"
LOG_FILE = ROOT / "logs" / "run-summary.json"
OGR2OGR = Path(r"C:\Program Files\QGIS 3.40.7\bin\ogr2ogr.exe")
OGRINFO = Path(r"C:\Program Files\QGIS 3.40.7\bin\ogrinfo.exe")
PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
USER_AGENT = "portolan-grill-me/1.0"
WFS_URL = "https://wfs.geo.ti.ch/service"
WFS_CAPABILITIES_URL = (
    "https://wfs.geo.ti.ch/service"
    "?service=WFS&request=GetCapabilities&version=1.1.0"
)
OGRINFO_TIMEOUT_SECONDS = 30
OGR2OGR_TIMEOUT_SECONDS = 60


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


def layer_name_to_filename(layer_name: str) -> str:
    safe = re.sub(r"[^a-zA-Z0-9._-]+", "_", layer_name.strip())
    return safe.strip("_.-") or "layer"


def feature_types_by_code() -> dict[str, list[str]]:
    capabilities = fetch_html(WFS_CAPABILITIES_URL)
    root = ET.fromstring(capabilities)

    by_code: dict[str, list[str]] = {}
    for feature_type in root.findall(".//{http://www.opengis.net/wfs}FeatureType"):
        name = feature_type.findtext("{http://www.opengis.net/wfs}Name", default="").strip()
        title = feature_type.findtext("{http://www.opengis.net/wfs}Title", default="").strip()
        code_match = re.search(r"\[(?P<code>[A-Z]{2}-\d+[a-zA-Z]?\.\d+)\]", title)
        if not code_match or not name:
            continue
        code = code_match.group("code")
        by_code.setdefault(code, []).append(name)

    return by_code


def layer_has_geometry(layer_name: str) -> bool:
    command = [str(OGRINFO), "-ro", "-so", f"WFS:{WFS_URL}", layer_name]
    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=OGRINFO_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return False
    if process.returncode != 0:
        return False
    text = (process.stdout or "") + "\n" + (process.stderr or "")
    match = re.search(r"Geometry:\s*(.+)", text)
    if not match:
        return False
    geometry_type = match.group(1).strip().lower()
    return geometry_type not in {"none", "unknown (any)"}


def run_wfs_layer_to_parquet(layer_name: str, target: Path) -> tuple[bool, str]:
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        target.unlink()
    command = [
        str(OGR2OGR),
        "-f",
        "Parquet",
        str(target),
        f"WFS:{WFS_URL}",
        layer_name,
        "-nln",
        layer_name,
        "-lco",
        "COMPRESSION=UNCOMPRESSED",
        "-lco",
        "GEOMETRY_ENCODING=WKB",
        "--config",
        "OGR_WFS_PAGING_ALLOWED",
        "YES",
        "-overwrite",
    ]
    try:
        process = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=OGR2OGR_TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        if target.exists():
            target.unlink()
        return False, f"Timeout dopo {OGR2OGR_TIMEOUT_SECONDS}s"
    message = (process.stdout or "") + (process.stderr or "")
    if process.returncode != 0 and target.exists():
        target.unlink()
    return process.returncode == 0, message.strip()


def main() -> int:
    if not OGR2OGR.exists():
        raise FileNotFoundError(f"ogr2ogr non trovato: {OGR2OGR}")
    if not OGRINFO.exists():
        raise FileNotFoundError(f"ogrinfo non trovato: {OGRINFO}")

    datasets = json.loads(SELECTION_FILE.read_text(encoding="utf-8"))
    wfs_by_code = feature_types_by_code()
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

    summary: list[dict[str, object]] = []

    for dataset in datasets:
        code = dataset["code"]
        slug = code.lower().replace("-", "_").replace(".", "_")
        row: dict[str, object] = {"code": code, "collection": dataset["collection"]}
        print(f"[{code}] avvio elaborazione", flush=True)

        try:
            layers = wfs_by_code.get(code, [])
            row["wfs_layers_total"] = len(layers)
            if not layers:
                row["status"] = "failed"
                row["error"] = "Nessun FeatureType WFS trovato per il codice dataset"
                summary.append(row)
                print(f"[{code}] nessun layer WFS trovato", flush=True)
                continue

            outputs: list[str] = []
            layer_failures: list[dict[str, str]] = []
            no_geometry_layers: list[str] = []
            for layer_name in layers:
                print(f"[{code}] layer {layer_name}", flush=True)
                if not layer_has_geometry(layer_name):
                    no_geometry_layers.append(layer_name)
                    print(f"[{code}] layer senza geometria, skip", flush=True)
                    continue

                target = ROOT / "parquet" / slug / f"{layer_name_to_filename(layer_name)}.parquet"
                ok, message = run_wfs_layer_to_parquet(layer_name, target)
                if ok:
                    outputs.append(str(target))
                    print(f"[{code}] parquet generato: {target.name}", flush=True)
                else:
                    layer_failures.append({"layer": layer_name, "message": message})
                    print(f"[{code}] errore layer {layer_name}", flush=True)

            row["outputs"] = outputs
            if no_geometry_layers:
                row["non_geometric_layers_skipped"] = no_geometry_layers
            if layer_failures:
                row["layer_failures"] = layer_failures
            row["status"] = "ok" if outputs else "failed"
            row["generated_count"] = len(outputs)
            print(
                f"[{code}] completato: generated={len(outputs)} failed={len(layer_failures)} skipped_no_geom={len(no_geometry_layers)}",
                flush=True,
            )
        except Exception as exc:
            row["status"] = "failed"
            row["error"] = str(exc)
            print(f"[{code}] eccezione: {exc}", flush=True)

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
