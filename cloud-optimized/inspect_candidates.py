from __future__ import annotations

import json
import re
import ssl
import urllib.request
from html import unescape
from pathlib import Path

ssl._create_default_https_context = ssl._create_unverified_context

PROXY = "http://proxy-bvcol.admin.ch:8080"
USER_AGENT = "portolan-grill-me/1.0"
WORKDIR = Path(__file__).resolve().parent
ROOT = WORKDIR.parent
OUT = WORKDIR / "candidate-archives.json"

CANDIDATES = {
    "ch-base/ch-063-1-suddivisioni-amministrative/collection.json": "CH-063.1",
    "ch-base/ch-067-1/collection.json": "CH-067.1",
    "ch-base/ch-068-1/collection.json": "CH-068.1",
    "ch-base/ch-181-1-cap-localita/collection.json": "CH-181.1",
    "ch-base/ch-184-1/collection.json": "CH-184.1",
    "ti-base/ti-005-1/collection.json": "TI-005.1",
    "ti-base/ti-006-1/collection.json": "TI-006.1",
    "ti-base/ti-007-1/collection.json": "TI-007.1",
    "ti-base/ti-008-1/collection.json": "TI-008.1",
    "ti-base/ti-009-1/collection.json": "TI-009.1",
}


def fetch_html(url: str) -> str:
    # Corporate proxy injects TLS certificates not trusted by this Python runtime.
    ssl_context = ssl._create_unverified_context()
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}),
        urllib.request.HTTPSHandler(context=ssl_context),
    )
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with opener.open(req, timeout=120) as response:
        return response.read().decode("utf-8", errors="replace")


results = []
for rel_path, code in CANDIDATES.items():
    collection = json.loads((ROOT / rel_path).read_text(encoding="utf-8"))
    ticino_urls = [
        value["href"]
        for value in collection.get("assets", {}).values()
        if isinstance(value, dict)
        and isinstance(value.get("href"), str)
        and value["href"].endswith("_ticino.zip")
    ]
    if not ticino_urls:
        results.append({"code": code, "collection": rel_path, "status": "no_ticino_asset"})
        continue

    archive_page = ticino_urls[0]
    html = fetch_html(archive_page)
    files = [unescape(value).strip() for value in re.findall(r'<td width="20%">([^<\n]+)', html)]
    download = re.search(r'<a href="([^"]+)" class="btn btn-primary">Download</a>', html)
    results.append(
        {
            "code": code,
            "collection": rel_path,
            "archive_page": archive_page,
            "download_url": (
                "https://data.geo.ti.ch/" + download.group(1).lstrip("/")
                if download
                else None
            ),
            "files": files,
        }
    )

OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
print(OUT)
