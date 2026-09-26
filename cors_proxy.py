#!/usr/bin/env python3
"""
CORS Proxy server for parquet files
Serves parquet files from GitHub Pages with proper CORS headers
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import urllib.request
import urllib.error
import json

class CORSProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        # Parse query parameter
        parsed_path = urlparse(self.path)
        query = parse_qs(parsed_path.query)
        
        if 'file' not in query:
            self.send_response(400)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Missing 'file' parameter"}).encode())
            return
        
        target_url = query['file'][0]
        
        # Validate URL (must be from github.com)
        if 'github.com' not in target_url and 'mlanini.github.io' not in target_url:
            self.send_response(403)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "URL not allowed"}).encode())
            return
        
        try:
            # Fetch the file from GitHub
            response = urllib.request.urlopen(target_url, timeout=30)
            content = response.read()
            
            # Send response with CORS headers
            self.send_response(200)
            self.send_header('Content-Type', response.headers.get('Content-Type', 'application/octet-stream'))
            self.send_header('Content-Length', len(content))
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type, Range')
            self.send_header('Access-Control-Expose-Headers', 'Content-Range, Content-Length')
            self.send_header('Accept-Ranges', 'bytes')
            self.end_headers()
            
            self.wfile.write(content)
            
        except urllib.error.URLError as e:
            self.send_response(502)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps({"error": f"Failed to fetch: {str(e)}"}).encode())
    
    def do_OPTIONS(self):
        # Handle CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Range')
        self.send_header('Access-Control-Expose-Headers', 'Content-Range, Content-Length')
        self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress logging
        pass

if __name__ == '__main__':
    server = HTTPServer(('0.0.0.0', 8000), CORSProxyHandler)
    print("CORS Proxy running on http://localhost:8000")
    print("Usage: http://localhost:8000/?file=https://mlanini.github.io/portolan-geodata-ch/...")
    server.serve_forever()
