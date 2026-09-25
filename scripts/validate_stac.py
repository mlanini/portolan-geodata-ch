from __future__ import annotations

import json
import sys
from pathlib import Path

import pystac


def find_stac_json_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            continue

        if isinstance(data, dict) and "stac_version" in data and "type" in data:
            files.append(path)
    return files


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    stac_files = find_stac_json_files(root)

    if not stac_files:
        print("No STAC JSON files found.")
        return 1

    failures: list[tuple[Path, str]] = []

    for path in stac_files:
        rel = path.relative_to(root)
        try:
            obj = pystac.read_file(str(path))
            obj.validate()
            print(f"OK   {rel}")
        except Exception as exc:
            failures.append((rel, str(exc)))
            print(f"FAIL {rel}: {exc}")

    if failures:
        print("\nValidation failed on the following files:")
        for rel, err in failures:
            print(f"- {rel}: {err}")
        return 1

    print(f"\nValidated {len(stac_files)} STAC files successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
