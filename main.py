import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from pdf_search.engine import PDFSearch


class SearchHandler(BaseHTTPRequestHandler):
    engine = None

    def do_GET(self):
        request = urlsplit(self.path)

        if request.path != "/documents":
            self.send_error(404)
            return

        params = parse_qs(request.query, keep_blank_values=True)
        query = params.get("q", [""])[0]

        try:
            results = self.engine.search(query)
        except ValueError as error:
            self.send_json(400, {"error": str(error)})
            return

        self.send_json(200, results)

    def send_json(self, status, data):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")

        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


if __name__ == "__main__":
    config = Path(__file__).resolve().parent / "config.yml"
    SearchHandler.engine = PDFSearch(config)

    server = HTTPServer(("localhost", 8008), SearchHandler)
    print("Сервер запущен: http://localhost:8008")
    server.serve_forever()
