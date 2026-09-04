#!/usr/bin/env python3
"""Tiny HTTP server for the EDDD budget planner.

Behaves like `python3 -m http.server 8765`, but if a request for `/foo`
would 404 and `/foo.html` exists, rewrites the path first. Saves us from
the localhost:8765/eddd-budget-planner 404 trap when browser autocomplete
drops the .html extension.
"""
import os
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8765
ROOT = Path(__file__).resolve().parent


class HtmlFallbackHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        # Cost constants live in ES modules the browser will otherwise cache and
        # keep serving after an edit, so the planner silently shows old money.
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
