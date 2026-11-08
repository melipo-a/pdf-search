import pytest

from pdf_search import engine


def create_search(tmp_path, monkeypatch, texts):
    folder = tmp_path / "pdfs"
    folder.mkdir()

    for filename in texts:
        (folder / filename).write_bytes(b"PDF")

    config = tmp_path / "config.yml"
    config.write_text("directories:\n  - pdfs\n", encoding="utf-8")

    monkeypatch.setattr(
        engine,
        "extract_pdf_text",
        lambda path: texts[path.name],
    )

    return engine.PDFSearch(config)


def test_search_without_case(tmp_path, monkeypatch):
    search = create_search(
        tmp_path,
        monkeypatch,
        {
            "first.pdf": "Охрана труда",
            "second.pdf": "Правила безопасности",
        },
    )

    assert search.search("ОХРАНА") == [{"file": "first.pdf"}]


def test_multiple_words_and_ranking(tmp_path, monkeypatch):
    search = create_search(
        tmp_path,
        monkeypatch,
        {
            "first.pdf": "охрана труда охрана",
            "second.pdf": "охрана",
            "third.pdf": "пожарная безопасность",
        },
    )

    result = search.search("охрана труда")

    assert result[0] == {"file": "first.pdf"}
    assert len(result) == 2


def test_no_results(tmp_path, monkeypatch):
    search = create_search(
        tmp_path,
        monkeypatch,
        {"first.pdf": "охрана труда"},
    )

    assert search.search("математика") == []


@pytest.mark.parametrize("query", ["", " ", "\n"])
def test_empty_query(tmp_path, monkeypatch, query):
    search = create_search(
        tmp_path,
        monkeypatch,
        {"first.pdf": "охрана труда"},
    )

    with pytest.raises(ValueError, match="Укажите поисковый запрос"):
        search.search(query)


def test_maximum_ten_results(tmp_path, monkeypatch):
    texts = {
        f"{number:02d}.pdf": "инструкция"
        for number in range(12)
    }

    search = create_search(tmp_path, monkeypatch, texts)

    assert len(search.search("инструкция")) == 10


def test_index_new_file(tmp_path, monkeypatch):
    texts = {"first.pdf": "охрана труда"}
    search = create_search(tmp_path, monkeypatch, texts)

    texts["second.pdf"] = "поисковая система"
    (tmp_path / "pdfs" / "second.pdf").write_bytes(b"PDF")

    search.update_index()

    assert search.search("поисковая") == [
        {"file": "second.pdf"}
    ]


def test_cached_documents(tmp_path, monkeypatch):
    search = create_search(
        tmp_path,
        monkeypatch,
        {"first.pdf": "охрана труда"},
    )

    def fail_if_called(path):
        pytest.fail("PDF не должен читаться повторно")

    monkeypatch.setattr(engine, "extract_pdf_text", fail_if_called)

    search.update_index()

    assert search.search("охрана") == [
        {"file": "first.pdf"}
    ]
