#!/usr/bin/env python3
"""Check GeoParquet metadata in detail"""

import pyarrow.parquet as pq
import json

parquet_file = r"C:\Temp\portolan-geodata-ch\cloud-optimized\parquet\ti_009_1\ti_009_1_v1_0_circondari_settori_forestali_circondari.parquet"

table = pq.read_table(parquet_file)

print("=== Schema Metadata ===")
schema = table.schema
if schema.metadata:
    for key, value in schema.metadata.items():
        key_str = key.decode() if isinstance(key, bytes) else key
        val_str = value.decode() if isinstance(value, bytes) else value
        
        if key_str == 'geo':
            print(f"\n{key_str} (GeoParquet):")
            try:
                geo_meta = json.loads(val_str)
                print(json.dumps(geo_meta, indent=2)[:1000])
            except:
                print(val_str[:500])
        else:
            print(f"{key_str}: {val_str[:150]}")
else:
    print("No metadata found!")

print("\n=== Table Info ===")
print(f"Rows: {table.num_rows}")
print(f"Columns: {table.num_columns}")
print(f"Column names: {table.column_names}")

print("\n=== Geometry Column ===")
if 'geometry' in table.column_names:
    geom_col = table['geometry']
    print(f"Type: {geom_col.type}")
    print(f"Non-null count: {geom_col.null_count < geom_col.length()}")
