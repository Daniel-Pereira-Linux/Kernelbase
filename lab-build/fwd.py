# proxy HTTP local -> busca o mesmo caminho via HTTPS (com verificação de certificado)
import http.server, socketserver, urllib.request, ssl, sys, shutil
ctx = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")
opener = urllib.request.build_opener(urllib.request.ProxyHandler({"https": __import__("os").environ["HTTPS_PROXY"]}),
                                     urllib.request.HTTPSHandler(context=ctx))
class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self, head=False):
        url = self.path
        if url.startswith("http://"):
            url = "https://" + url[len("http://"):]
        try:
            req = urllib.request.Request(url, method="HEAD" if head else "GET", headers={"User-Agent": "kb-builder"})
            with opener.open(req, timeout=120) as r:
                self.send_response(r.status)
                for k, v in r.getheaders():
                    if k.lower() in ("content-length", "content-type", "last-modified", "etag", "date"):
                        self.send_header(k, v)
                self.end_headers()
                if not head:
                    shutil.copyfileobj(r, self.wfile, 256 * 1024)
        except urllib.error.HTTPError as e:
            self.send_response(e.code); self.send_header("Content-Length", "0"); self.end_headers()
        except Exception as e:
            self.send_response(502); self.send_header("Content-Length", "0"); self.end_headers()
            sys.stderr.write("erro %s %s\n" % (url, e))
    def do_HEAD(self): self.do_GET(head=True)
    def log_message(self, *a): pass
class S(socketserver.ThreadingMixIn, http.server.HTTPServer): daemon_threads = True
S(("127.0.0.1", 8081), H).serve_forever()
