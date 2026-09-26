#!/usr/bin/env python3
"""Diagnose parquet file structure"""

import sys
from pathlib import Path

# Test with pyarrow
try:
    import pyarrow.parquet as pq
    
    parquet_file = r"C:\Temp\portolan-geodata-ch\cloud-optimized\parquet\ti_009_1\ti_009_1_v1_0_circondari_settori_forestali_circondari.parquet"
    
    print(f"Testing: {parquet_file}")
    print(f"File size: {Path(parquet_file).stat().st_size} bytes")
    print()
    
    # Try to read the file
    try:
        pf = pq.read_table(parquet_file)
        print("✓ File readable by PyArrow")
        print(f"  Rows: {pf.num_rows}")
        print(f"  Columns: {pf.num_columns}")
        print(f"  Schema: {pf.schema}")
    except Exception as e:
        print(f"✗ Error reading: {type(e).__name__}: {e}")
        
except ImportError:
    print("PyArrow not installed, trying with fastparquet...")
    try:
        import fastparquet
        pf = fastparquet.ParquetFile(parquet_file)
        print(f"✓ File readable by fastparquet")
        print(f"  Statistics: {pf.statistics}")
    except Exception as e:
        print(f"✗ Error: {e}")
