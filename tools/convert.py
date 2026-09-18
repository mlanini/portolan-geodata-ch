#!/usr/bin/env python3
"""Convert Swiss source geodata into the Portolan cloud-native formats.

Thin, documented wrappers over GDAL/OGR, tippecanoe, and rio-cogeo. These are the
exact commands the geodata.ch pipeline runs; each one is a normal CLI call so it
can be reviewed, reproduced, and run by hand. They require the tools on PATH
(gdal >= 3.8 for GeoParquet, tippecanoe, rio-cogeo) and are not executed in the
public sandbox.

Conversion defaults follow specs/best-practices/conversion-defaults.md in
portolan-spec: GeoParquet 1.1, zstd, Hilbert spatial ordering, bbox covering
column, row groups <= 150k; COG with internal tiling, overviews, and embedded
statistics.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

TARGET_CRS = "EPSG:4326"      # published CRS for vector/tabular
ROW_GROUP = 100_000           # <= 150k per Portolan formats.md


def run(cmd: list[str]) -> None:
    print("+", " ".join(cmd))
    subprocess.run(cmd, check=True)


def to_geoparquet(src: str, out: str, layer: str | None = None) -> None:
    """FileGDB / GeoPackage / XTF / Shapefile -> GeoParquet 1.1 (zstd, ordered)."""
    cmd = [
        "ogr2ogr", "-f", "Parquet", out, src,
        "-t_srs", TARGET_CRS,
        "-lco", "COMPRESSION=ZSTD",
        "-lco", "GEOMETRY_ENCODING=WKB",
        "-lco", "WRITE_COVERING_BBOX=YES",
        "-lco", f"ROW_GROUP_SIZE={ROW_GROUP}",
        "-lco", "SORT_BY_BBOX=YES",   # Hilbert-style spatial ordering (GDAL >= 3.9)
    ]
    if layer:
        cmd.append(layer)
    run(cmd)


def to_parquet_table(src: str, out: str) -> None:
    """Non-spatial CSV/XLSX -> plain Parquet (no geometry column)."""
    run(["ogr2ogr", "-f", "Parquet", out, src, "-lco", "COMPRESSION=ZSTD"])


def to_pmtiles(src_parquet: str, out: str, layer_name: str, maxzoom: int = 14) -> None:
    """GeoParquet -> GeoJSONSeq -> PMTiles via tippecanoe."""
    geojsonseq = out + ".geojsonl"
    run(["ogr2ogr", "-f", "GeoJSONSeq", geojsonseq, src_parquet])
    run([
        "tippecanoe", "-o", out, "--force",
        "-l", layer_name,
        "-zg", f"--maximum-zoom={maxzoom}",
        "--drop-densest-as-needed", "--extend-zooms-if-still-dropping",
        geojsonseq,
    ])
    Path(geojsonseq).unlink(missing_ok=True)


def to_cog(src_tif: str, out: str) -> None:
    """GeoTIFF -> Cloud-Optimized GeoTIFF with overviews and embedded statistics."""
    run([
        "gdal_translate", "-of", "COG", src_tif, out,
        "-co", "COMPRESS=DEFLATE",
        "-co", "BLOCKSIZE=512",
        "-co", "OVERVIEWS=AUTO",
        "-co", "STATISTICS=YES",   # embed min/max/mean/stddev in the header
    ])
    # Validate the result is a real COG with overviews.
    run(["rio", "cogeo", "validate", out])


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("vector"); p.add_argument("src"); p.add_argument("out"); p.add_argument("--layer")
    p = sub.add_parser("table"); p.add_argument("src"); p.add_argument("out")
    p = sub.add_parser("pmtiles"); p.add_argument("src"); p.add_argument("out"); p.add_argument("layer"); p.add_argument("--maxzoom", type=int, default=14)
    p = sub.add_parser("cog"); p.add_argument("src"); p.add_argument("out")

    args = ap.parse_args()
    try:
        if args.cmd == "vector":
            to_geoparquet(args.src, args.out, args.layer)
        elif args.cmd == "table":
            to_parquet_table(args.src, args.out)
        elif args.cmd == "pmtiles":
            to_pmtiles(args.src, args.out, args.layer, args.maxzoom)
        elif args.cmd == "cog":
            to_cog(args.src, args.out)
    except FileNotFoundError as e:
        print(f"Missing tool: {e}. Install GDAL/tippecanoe/rio-cogeo (see tools/README.md).", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
