#!/usr/bin/env python3
"""Test if GitHub Pages supports range requests for parquet files"""

import urllib.request
import urllib.error
import os

url = "https://mlanini.github.io/portolan-geodata-ch/cloud-optimized/parquet/ti_009_1/ti_009_1_v1_0_circondari_settori_forestali_circondari.parquet"
proxy_url = "http://proxy-bvcol.admin.ch:8080"

# Set proxy
proxy_handler = urllib.request.ProxyHandler({
    'http': proxy_url,
    'https': proxy_url,
})
opener = urllib.request.build_opener(proxy_handler)
urllib.request.install_opener(opener)

print("=== Testing GitHub Pages Range Request Support ===\n")

# First, get file info
try:
    request = urllib.request.Request(url, method='HEAD')
    response = urllib.request.urlopen(request)
    
    print("HEAD Response Headers:")
    print(f"  Content-Length: {response.headers.get('Content-Length', 'N/A')}")
    print(f"  Accept-Ranges: {response.headers.get('Accept-Ranges', 'N/A')}")
    print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")
    print(f"  Status: {response.status}")
    print()
    
except Exception as e:
    print(f"Error: {e}\n")

# Test range request for last 8 bytes (footer)
print("Testing Range Request (last 8 bytes)...")
try:
    request = urllib.request.Request(url)
    request.add_header('Range', 'bytes=-8')
    response = urllib.request.urlopen(request)
    
    content = response.read()
    print(f"  Status: {response.status}")
    print(f"  Content-Length: {len(content)} bytes")
    print(f"  Content-Range: {response.headers.get('Content-Range', 'N/A')}")
    print(f"  Footer bytes: {content.hex()}")
    
    if content[-4:] == b'PAR1':
        print("  ✓ Range request works! File footer is valid (PAR1)")
    else:
        print(f"  ✗ Invalid footer: {content[-4:]}")
    
except urllib.error.HTTPError as e:
    print(f"  ✗ HTTP Error: {e.code} - {e.reason}")
    if e.code == 416:
        print("    (416 = Range Not Satisfiable - server doesn't support ranges)")
except Exception as e:
    print(f"  ✗ Error: {e}")

print("\n=== Full File Download Test ===")
try:
    response = urllib.request.urlopen(url)
    content = response.read()
    print(f"Downloaded {len(content)} bytes")
    print(f"First 4 bytes: {content[:4]}")
    print(f"Last 4 bytes: {content[-4:]}")
    
    if content[:4] == b'PAR1' and content[-4:] == b'PAR1':
        print("✓ File appears valid locally!")
    else:
        print("✗ File header/footer mismatch")
        
except Exception as e:
    print(f"✗ Error downloading: {e}")
