"""Loopback operator server. Token roles are server-side, never supplied by clients."""
import argparse
import hmac
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from .core import Store

STATIC = Path(__file__).parent / 'static'


def handler(store, credentials):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Do not log tokens or user-supplied content.

        def send(self, status, value, content_type='application/json'):
            body = json.dumps(value, ensure_ascii=False).encode() if content_type == 'application/json' else value
            self.send_response(status)
            self.send_header('Content-Type', content_type + '; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; object-src 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(body)

        def identity(self):
            token = self.headers.get('Authorization', '').removeprefix('Bearer ')
            for role, secret in credentials.items():
                if secret and hmac.compare_digest(token, secret):
                    return role, role
            raise PermissionError('valid Bearer token required')

        def do_GET(self):
            self.dispatch(False)

        def do_POST(self):
            self.dispatch(True)

        def dispatch(self, write):
            try:
                path = urlparse(self.path).path
                if not write and path in ('/', '/app.js', '/style.css'):
                    name = {'/': 'index.html', '/app.js': 'app.js', '/style.css': 'style.css'}[path]
                    content_type = {'/': 'text/html', '/app.js': 'text/javascript', '/style.css': 'text/css'}[path]
                    return self.send(200, (STATIC / name).read_bytes(), content_type)
                if not write and path == '/health':
                    return self.send(200, {'status': 'ok'})
                actor, role = self.identity()
                parts = path.strip('/').split('/')
                if write:
                    length = int(self.headers.get('Content-Length', '0'))
                    if not 0 < length <= 1000000:
                        return self.send(413, {'error': 'body must be 1–1000000 bytes'})
                    data = json.loads(self.rfile.read(length))
                    if not isinstance(data, dict):
                        raise ValueError('JSON object required')
                    if parts == ['api', 'claims']:
                        c = store.create(data.get('statement'), data.get('provenance'), actor, role, data.get('critical', False))
                        return self.send(201, c)
                    if len(parts) == 4 and parts[:2] == ['api', 'claims']:
                        if parts[3] == 'transition':
                            result = store.transition(parts[2], data.get('target'), actor, role)
                            return self.send(200 if result['accepted'] else 409, result)
                        if parts[3] == 'attacks':
                            from .operators import run_attacks
                            return self.send(200, run_attacks(store, parts[2], actor, role))
                        result = store.mutate(parts[2], parts[3], data, actor, role)
                        return self.send(200, result)
                else:
                    if parts == ['api', 'claims']:
                        return self.send(200, [{'claim': c, 'metrics': store.metrics(c)} for c in store.claims()])
                    if parts == ['api', 'ledger']:
                        return self.send(200, {'valid': store.verify_ledger(), 'entries': store.ledger()})
                    if len(parts) in (3, 4) and parts[:2] == ['api', 'claims']:
                        if len(parts) == 3:
                            return self.send(200, store.get(parts[2]))
                        if parts[3] == 'assurance':
                            return self.send(200, store.assurance(parts[2]))
                self.send(404, {'error': 'route not found'})
            except PermissionError as error:
                self.send(403, {'error': str(error)})
            except KeyError:
                self.send(404, {'error': 'claim not found'})
            except (ValueError, TypeError) as error:
                self.send(400, {'error': str(error)})
            except Exception:
                self.send(500, {'error': 'internal server error'})
    return Handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--db', default='researchos.db')
    parser.add_argument('--port', type=int, default=8080)
    args = parser.parse_args()
    credentials = {role: os.environ.get('RESEARCHOS_' + role.upper() + '_TOKEN') for role in ('researcher', 'reviewer', 'admin')}
    tokens = [x for x in credentials.values() if x]
    if not tokens or len(tokens) != len(set(tokens)):
        parser.error('Set at least one RESEARCHOS_<ROLE>_TOKEN; configured tokens must be distinct')
    store = Store(args.db)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), handler(store, credentials))
    print(f'ResearchOS listening at http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        store.close()


if __name__ == '__main__':
    main()
