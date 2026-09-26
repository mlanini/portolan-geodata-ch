// Cloudflare Worker - CORS Proxy for parquet files
// Deploy this to https://dash.cloudflare.com/

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const targetUrl = url.searchParams.get('file');

    if (!targetUrl) {
      return new Response('Missing "file" parameter', { status: 400 });
    }

    // Only allow GitHub and mlanini.github.io
    if (!targetUrl.includes('github.com') && !targetUrl.includes('mlanini.github.io')) {
      return new Response('URL not allowed', { status: 403 });
    }

    try {
      const response = await fetch(targetUrl, {
        method: request.method,
        headers: request.headers,
      });

      const newResponse = new Response(response.body, response);
      
      // Add CORS headers
      newResponse.headers.set('Access-Control-Allow-Origin', '*');
      newResponse.headers.set('Access-Control-Allow-Methods', 'GET, HEAD, OPTIONS, POST');
      newResponse.headers.set('Access-Control-Allow-Headers', 'Content-Type, Range');
      newResponse.headers.set('Access-Control-Expose-Headers', 'Content-Range, Content-Length');
      
      return newResponse;
    } catch (error) {
      return new Response(`Error: ${error.message}`, { status: 502 });
    }
  },
};
