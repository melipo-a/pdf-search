import json
from http.server import HTTPServer
from threading import Thread
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import urlopen

import pytest

from main import SearchHandler


class FakeSearch:
    def search(self, query):
        if not query.strip():
            raise ValueError("Укажите поисковый запрос")

        if query.lower() == "охрана":
            return [{"file": "manual.pdf"}]

        return []


@pytest.fixture
def api(monkeypatch):
    monkeypatch.setattr(SearchHandler, "engine", FakeSearch())

    server = HTTPServer(("127.0.0.1", 0), SearchHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def test_search_response(api):
    query = urlencode({"q": "охрана"})

    with urlopen(f"{api}/documents?{query}") as response:
        assert response.status == 200
        assert response.headers["Content-Type"].startswith(
            "application/json"
        )
        assert json.load(response) == [{"file": "manual.pdf"}]


def test_no_results(api):
    query = urlencode({"q": "математика"})

    with urlopen(f"{api}/documents?{query}") as response:
        assert response.status == 200
        assert json.load(response) == []


@pytest.mark.parametrize("query", ["", "?q=", "?q=+"])
def test_invalid_query(api, query):
    with pytest.raises(HTTPError) as error:
        urlopen(f"{api}/documents{query}")

    assert error.value.code == 400
    assert json.load(error.value) == {
        "error": "Укажите поисковый запрос"
    }


def test_unknown_path(api):
    with pytest.raises(HTTPError) as error:
        urlopen(f"{api}/unknown")

    assert error.value.code == 404
