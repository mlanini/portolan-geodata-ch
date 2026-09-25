from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from pathlib import Path

TIMEOUT_SECONDS = 20
USER_AGENT = "portolan-mirror-link-check/1.0"


def iter_json_files(root: Path):
    for path in root.rglob("*.json"):
        yield path


def extract_http_hrefs(data: dict) -> list[str]:
    hrefs: list[str] = []

    for link in data.get("links", []):
        if isinstance(link, dict):
            href = link.get("href")
            if isinstance(href, str) and href.startswith(("http://", "https://")):
                hrefs.append(href)

    return hrefs


def check_url(url: str) -> tuple[bool, str]:
    headers = {"User-Agent": USER_AGENT}

    # Try HEAD first; if unsupported (405), fallback to GET.
    req = urllib.request.Request(url, method="HEAD", headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            code = resp.getcode()
            if 200 <= code < 400:
                return True, str(code)
            return False, str(code)
    except urllib.error.HTTPError as err:
        if err.code == 405:
            get_req = urllib.request.Request(url, method="GET", headers=headers)
            try:
                with urllib.request.urlopen(get_req, timeout=TIMEOUT_SECONDS) as resp:
                    code = resp.getcode()
                    if 200 <= code < 400:
                        return True, str(code)
                    return False, str(code)
            except Exception as get_exc:
                return False, str(get_exc)
        return False, f"HTTP {err.code}"
    except Exception as exc:
        return False, str(exc)


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    urls: dict[str, list[Path]] = {}

    for json_file in iter_json_files(root):
        try:
            data = json.loads(json_file.read_text(encoding="utf-8"))
        except Exception:
            continue

        if not isinstance(data, dict):
            continue

        for href in extract_http_hrefs(data):
            urls.setdefault(href, []).append(json_file)

    if not urls:
        print("No external HTTP(S) links found.")
        return 0

    failures: list[tuple[str, str]] = []

    for url in sorted(urls):
        ok, detail = check_url(url)
        if ok:
            print(f"OK   {url} ({detail})")
        else:
            failures.append((url, detail))
            print(f"FAIL {url} ({detail})")

    if failures:
        print("\nBroken external links:")
        for url, detail in failures:
            print(f"- {url}: {detail}")
        return 1

    print(f"\nChecked {len(urls)} unique external links successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
