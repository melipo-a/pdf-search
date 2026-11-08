from pdf_search.engine import PDFSearch


def test_same_filenames_in_different_directories(
    tmp_path, monkeypatch
):
    folder_a = tmp_path / "a"
    folder_b = tmp_path / "b"
    folder_a.mkdir()
    folder_b.mkdir()

    (folder_a / "good.pdf").write_bytes(b"pdf a")
    (folder_b / "good.pdf").write_bytes(b"pdf b")

    config = tmp_path / "config.yml"
    config.write_text(
        "directories:\n  - a\n  - b\n",
        encoding="utf-8",
    )

    def fake_extract(filename):
        if filename.parent.name == "a":
            return "alpha"
        return "bravo"

    monkeypatch.setattr(
        "pdf_search.engine.extract_pdf_text",
        fake_extract,
    )

    search = PDFSearch(config)
    results = search.search("alpha bravo")

    assert len(results) == 2
    assert {item["file"] for item in results} == {
        "a/good.pdf",
        "b/good.pdf",
    }


def test_single_directory_keeps_short_filename(
    tmp_path, monkeypatch
):
    folder = tmp_path / "pdfs"
    folder.mkdir()
    (folder / "safety.pdf").write_bytes(b"pdf")

    config = tmp_path / "config.yml"
    config.write_text(
        "directories:\n  - pdfs\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "pdf_search.engine.extract_pdf_text",
        lambda filename: "охрана труда",
    )

    search = PDFSearch(config)

    assert search.search("охрана труда") == [
        {"file": "safety.pdf"}
    ]
