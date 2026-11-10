"""Serve the dashboard and its published CSV on the local machine."""

import argparse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


HOST = "127.0.0.1"
ROOT = Path(__file__).resolve().parent.parent
ROUTES = {
    "/app/": ("app/index.html", "text/html"),
    "/app/index.html": ("app/index.html", "text/html"),
    "/app/styles.css": ("app/styles.css", "text/css"),
    "/app/dashboard.mjs": ("app/dashboard.mjs", "text/javascript"),
    "/app/data.mjs": ("app/data.mjs", "text/javascript"),
    "/outputs/final_dataset.csv": ("outputs/final_dataset.csv", "text/csv"),
}


class PreviewHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        super().end_headers()

    def do_GET(self):
        self._serve(include_body=True)

    def do_HEAD(self):
        self._serve(include_body=False)

    def _serve(self, include_body):
        # Match the original request target exactly, apart from any query string.
        path = self.requestline.split()[1].partition("?")[0]
        if path == "/":
            self.send_response(302)
            self.send_header("Location", "/app/")
            self.send_header("Content-Length", "0")
            self.end_headers()
            return

        route = ROUTES.get(path)
        if route is None:
            self.send_error(404)
            return

        relative_path, mime_type = route
        file_path = ROOT / relative_path
        try:
            # A symlink at an allowed path must not expose a different file.
            if file_path.resolve() != file_path or not file_path.is_file():
                self.send_error(404)
                return
            body = file_path.read_bytes()
        except (OSError, RuntimeError):
            self.send_error(404)
            return

        self.send_response(200)
        self.send_header("Content-Type", f"{mime_type}; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        if include_body:
            self.wfile.write(body)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765, help="local port (default: 8765)")
    args = parser.parse_args()
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")

    try:
        with ThreadingHTTPServer((HOST, args.port), PreviewHandler) as server:
            print(f"Open http://{HOST}:{args.port}/app/ (Ctrl+C to stop)", flush=True)
            server.serve_forever()
    except KeyboardInterrupt:
        pass
    except OSError as exc:
        parser.exit(1, f"Could not start dashboard preview on {HOST}:{args.port}: {exc}\n")


if __name__ == "__main__":
    main()
