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


@pytest.mark.parametrize(
    "content, expected",
    [
        (
            "directories:\n  - 'O''Brien'\n",
            ["O'Brien"],
        ),
        (
            """directories: ['O''Brien', "my, docs"]\n""",
            ["O'Brien", "my, docs"],
        ),
        (
            'directories:\n  - "my # docs" # комментарий\n',
            ["my # docs"],
        ),
        (
            'directories: ["a, b", "docs #2"] # files [2026]\n',
            ["a, b", "docs #2"],
        ),
        (
            'directories:\n  - "quote\\"inside"\n',
            ['quote"inside'],
        ),
    ],
)
def test_quoted_yaml_paths(tmp_path, content, expected):
    config = tmp_path / "config.yml"
    config.write_text(content, encoding="utf-8")

    assert load_directories(config) == [
        (tmp_path / folder).resolve()
        for folder in expected
    ]


@pytest.mark.parametrize(
    "content",
    [
        'directories:\n  - "unfinished\n',
        "directories:\n  - 'unfinished\n",
        "directories:\n  - 'O'Brian'\n",
        'directories:\n  - ""\n',
        'directories:\n  - "one" trailing\n',
        'directories: ["unfinished]\n',
        "directories: [pdfs,]\n",
    ],
)
def test_invalid_yaml_paths(tmp_path, content):
    config = tmp_path / "config.yml"
    config.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError):
        load_directories(config)
