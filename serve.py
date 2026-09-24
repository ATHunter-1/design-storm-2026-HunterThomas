#!/usr/bin/env python3
"""Tiny HTTP server for the pages in this repository.

The 3D map fetches JSON, so opening it as a file:// URL fails; serve it instead:

    python3 serve.py
    open http://localhost:8765/design-storm-water-system-3d

Behaves like `python3 -m http.server 8765`, but if a request for `/foo`
would 404 and `/foo.html` exists, rewrites the path first, so a URL without
the .html extension still resolves.
"""
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
ROOT = Path(__file__).resolve().parent


class HtmlFallbackHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Generated JSON is edited in place during development; without this the
        # browser keeps serving a cached copy and the map silently shows old data.
        self.send_header("Cache-Control", "no-store, must-revalidate")
        super().end_headers()

    def send_head(self):
        path_part, _, query = self.path.partition("?")
        rel = path_part.lstrip("/")
        if rel and not rel.endswith("/"):
            candidate = ROOT / rel
            if not candidate.exists():
                html_candidate = candidate.parent / (candidate.name + ".html")
                if html_candidate.is_file():
                    self.path = "/" + html_candidate.relative_to(ROOT).as_posix()
                    if query:
                        self.path += "?" + query
        return super().send_head()


if __name__ == "__main__":
    os.chdir(ROOT)
    with ThreadingHTTPServer(("", PORT), HtmlFallbackHandler) as httpd:
        print(f"Serving {ROOT} at http://localhost:{PORT}/ (with .html fallback)")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
