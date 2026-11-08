import pytest

from pdf_search.engine import load_directories


@pytest.mark.parametrize(
    "content, folder",
    [
        (
            "directories:\n  - pdfs#backup\n",
            "pdfs#backup",
        ),
        (
            "directories:\n  - my  docs\n",
            "my  docs",
        ),
        (
            "directories:\n  - O'Brien\n",
            "O'Brien",
        ),
        (
            "directories: [pdfs] # files [2026]\n",
            "pdfs",
        ),
    ],
)
def test_yaml_path_regressions(tmp_path, content, folder):
    config = tmp_path / "config.yml"
    config.write_text(content, encoding="utf-8")

    assert load_directories(config) == [
        (tmp_path / folder).resolve()
    ]
