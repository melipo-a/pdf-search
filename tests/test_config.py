import pytest

from pdf_search.engine import load_directories


@pytest.mark.parametrize(
    "content",
    [
        "directories:\n  - pdfs\n  - docs\n",
        "directories: [pdfs, docs]\n",
        'directories: ["pdfs", "docs"]\n',
        "directories:\n  - pdfs # основной каталог\n  - docs\n",
    ],
)
def test_load_directories(tmp_path, content):
    config = tmp_path / "config.yml"
    config.write_text(content, encoding="utf-8")

    result = load_directories(config)

    assert result == [
        (tmp_path / "pdfs").resolve(),
        (tmp_path / "docs").resolve(),
    ]


def test_paths_relative_to_config(tmp_path):
    folder = tmp_path / "project"
    folder.mkdir()

    config = folder / "config.yml"
    config.write_text(
        "directories:\n  - pdfs\n",
        encoding="utf-8",
    )

    assert load_directories(config) == [
        (folder / "pdfs").resolve()
    ]


@pytest.mark.parametrize(
    "content",
    [
        "directories: []\n",
        "directories:\n",
        "directories: invalid\n",
        "unknown:\n  - pdfs\n",
    ],
)
def test_invalid_config(tmp_path, content):
    config = tmp_path / "config.yml"
    config.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError):
        load_directories(config)
