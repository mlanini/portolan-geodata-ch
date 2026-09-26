#!/usr/bin/env python3
"""
CORS Proxy server for parquet files with Range request support
Deployed on Vercel/Railway - serves files with proper CORS headers for DuckDB/geoparquet.info
"""

from flask import Flask, request, Response
from urllib.parse import urlparse, parse_qs
import requests
import os

app = Flask(__name__)

@app.route('/', methods=['GET', 'OPTIONS', 'HEAD'])
def proxy():
    """Handle CORS proxy requests"""
    
    # Handle preflight
    if request.method == 'OPTIONS':
        return '', 200, {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Range',
            'Access-Control-Expose-Headers': 'Content-Range, Content-Length, Accept-Ranges',
        }
    
    # Get target URL from query parameter
    target_url = request.args.get('file')
    if not target_url:
        return {'error': 'Missing "file" parameter'}, 400
    
    # Validate URL (only allow GitHub)
    if 'github.com' not in target_url and 'cdn.jsdelivr.net' not in target_url:
        return {'error': 'URL not allowed'}, 403
    
    try:
        # Forward Range header if present
        headers = {}
        if 'Range' in request.headers:
            headers['Range'] = request.headers['Range']
        
        # Fetch file with streaming
        resp = requests.get(target_url, headers=headers, timeout=30, stream=True)
        resp.raise_for_status()
        
        # Build response headers
        response_headers = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET, HEAD, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Range',
            'Access-Control-Expose-Headers': 'Content-Range, Content-Length, Accept-Ranges',
            'Accept-Ranges': 'bytes',
            'Cache-Control': 'public, max-age=86400',  # Cache for 24h
        }
        
        # Copy relevant headers from upstream
        if 'Content-Type' in resp.headers:
            response_headers['Content-Type'] = resp.headers['Content-Type']
        if 'Content-Length' in resp.headers:
            response_headers['Content-Length'] = resp.headers['Content-Length']
        if 'Content-Range' in resp.headers:
            response_headers['Content-Range'] = resp.headers['Content-Range']
        
        status_code = resp.status_code
        return Response(resp.iter_content(chunk_size=8192), status=status_code, headers=response_headers)
        
    except Exception as e:
        return {'error': f'Failed to fetch: {str(e)}'}, 502, {
            'Access-Control-Allow-Origin': '*',
        }

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=False)
    
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
