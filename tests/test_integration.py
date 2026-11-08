import mongomock

from pdf_search import engine
from pdf_search.storage import MongoStorage


def prepare_search(tmp_path):
    folder = tmp_path / "pdfs"
    folder.mkdir()

    config = tmp_path / "config.yml"
    config.write_text(
        "directories:\n  - pdfs\n",
        encoding="utf-8",
    )

    storage = MongoStorage(client=mongomock.MongoClient())

    return folder, config, storage


def test_index_saved_to_mongodb(tmp_path, monkeypatch):
    folder, config, storage = prepare_search(tmp_path)
    filename = folder / "first.pdf"
    filename.write_bytes(b"PDF")

    monkeypatch.setattr(
        engine,
        "extract_pdf_text",
        lambda path: "охрана труда",
    )

    search = engine.PDFSearch(config, storage=storage)

    assert search.search("охрана") == [
        {"file": "first.pdf"}
    ]

    saved = storage.load()
    assert saved[str(filename.resolve())]["text"] == "охрана труда"


def test_index_loaded_from_mongodb(tmp_path, monkeypatch):
    folder, config, storage = prepare_search(tmp_path)
    (folder / "first.pdf").write_bytes(b"PDF")

    monkeypatch.setattr(
        engine,
        "extract_pdf_text",
        lambda path: "охрана труда",
    )

    engine.PDFSearch(config, storage=storage)

    def fail_if_called(path):
        raise AssertionError("PDF не должен читаться повторно")

    monkeypatch.setattr(
        engine,
        "extract_pdf_text",
        fail_if_called,
    )

    search = engine.PDFSearch(config, storage=storage)

    assert search.search("охрана") == [
        {"file": "first.pdf"}
    ]


def test_deleted_pdf_removed_from_mongodb(tmp_path, monkeypatch):
    folder, config, storage = prepare_search(tmp_path)

    first = folder / "first.pdf"
    second = folder / "second.pdf"

    first.write_bytes(b"PDF")
    second.write_bytes(b"PDF")

    monkeypatch.setattr(
        engine,
        "extract_pdf_text",
        lambda path: path.stem,
    )

    search = engine.PDFSearch(config, storage=storage)

    first.unlink()
    search.update_index()

    assert search.search("first") == []
    assert search.search("second") == [
        {"file": "second.pdf"}
    ]
    assert str(first.resolve()) not in storage.load()
