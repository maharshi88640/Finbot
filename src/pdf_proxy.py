import threading
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs, unquote
import requests

class PDFProxyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path != '/pdf_proxy':
            self.send_error(404, 'Not Found')
            return

        qs = parse_qs(parsed.query)
        url = qs.get('url', [''])[0]
        url = unquote(url)
        if not url.startswith('http'):
            self.send_error(400, 'Invalid URL')
            return

        try:
            resp = requests.get(url, stream=True, timeout=20)
        except Exception as e:
            self.send_error(502, f'Upstream fetch error: {e}')
            return

        content_type = resp.headers.get('Content-Type', 'application/pdf')
        # Force inline disposition to try to open in browser
        filename = url.split('/')[-1].split('?')[0] or 'document.pdf'
        try:
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Disposition', f'inline; filename="{filename}"')
            self.end_headers()

            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    self.wfile.write(chunk)
        except BrokenPipeError:
            # Client closed connection
            return
        except Exception as e:
            # Log and ignore
            print(f"Error streaming proxy content: {e}")

def start_proxy_server(host='127.0.0.1', port=8765):
    server = ThreadingHTTPServer((host, port), PDFProxyHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    print(f"PDF proxy running at http://{host}:{port}/pdf_proxy?url=<url>")
    return server
