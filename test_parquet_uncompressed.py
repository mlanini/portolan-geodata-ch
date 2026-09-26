#!/usr/bin/env python3
"""Generate uncompressed parquet for ti_009_1 to test Portolan compatibility"""

import os
import subprocess
import ssl
from pathlib import Path

ssl._create_default_https_context = ssl._create_unverified_context

ROOT = Path(__file__).resolve().parent
OGR2OGR = Path(r"C:\Program Files\QGIS 3.40.7\bin\ogr2ogr.exe")
PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("HTTP_PROXY")
WFS_URL = "https://wfs.geo.ti.ch/service"

# Test dataset: TI-009.1
layers = [
    "ti_009_1_v1_0_circondari_settori_forestali_circondari",
    "ti_009_1_v1_0_circondari_settori_forestali_settori",
]

for layer_name in layers:
    output_dir = ROOT / "cloud-optimized" / "parquet" / "ti_009_1"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Sanitize filename
    import re
    safe_name = re.sub(r"[^a-zA-Z0-9._-]+", "_", layer_name.strip()).strip("_.-") or "layer"
    target = output_dir / f"{safe_name}.parquet"
    
    if target.exists():
        target.unlink()
    
    print(f"Generating {layer_name} -> {target.name}")
    
    command = [
        str(OGR2OGR),
        "-f", "Parquet",
        str(target),
        f"WFS:{WFS_URL}",
        layer_name,
        "-nln", layer_name,
        "-lco", "COMPRESSION=UNCOMPRESSED",
        "-lco", "GEOMETRY_ENCODING=WKB",
        "--config", "OGR_WFS_PAGING_ALLOWED", "YES",
        "-overwrite",
    ]
    
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            print(f"✓ Success: {target.name}")
        else:
            print(f"✗ Failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        print(f"✗ Timeout")
        if target.exists():
            target.unlink()

print("Done!")
