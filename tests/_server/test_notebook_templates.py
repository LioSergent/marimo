# Copyright 2026 Marimo. All rights reserved.
from __future__ import annotations

import sys
from pathlib import Path
from textwrap import dedent
from typing import Any

import pytest

from marimo._server.notebook_templates import (
    get_template_directories,
    list_templates,
    read_template,
)
from marimo._utils.http import HTTPException, HTTPStatus

TEMPLATE = dedent(
    '''
    """{docstring}"""

    import marimo

    app = marimo.App()


    @app.cell
    def _():
        x = 1
        return (x,)


    if __name__ == "__main__":
        app.run()
    '''
)


def write_template(path: Path, docstring: str = "A template.") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(TEMPLATE.format(docstring=docstring))
    return path


def test_get_template_directories(tmp_path: Path) -> None:
    config = {"templates": {"directories": [str(tmp_path), "~/templates"]}}
    assert get_template_directories(config) == [  # type: ignore[arg-type]
        tmp_path,
        Path("~/templates").expanduser(),
    ]


@pytest.mark.parametrize(
    "config",
    [{}, {"templates": {}}, {"templates": {"directories": "not_a_list"}}],
)
def test_get_template_directories_not_configured(
    config: dict[str, Any],
) -> None:
    assert get_template_directories(config) == []  # type: ignore[arg-type]


def test_list_templates(tmp_path: Path) -> None:
    write_template(tmp_path / "beta.py", docstring="Beta.\n\nMore details.")
    write_template(tmp_path / "Alpha.py")
    # Not listed: not a marimo notebook, not a .py file, or in a subdirectory
    (tmp_path / "helpers.py").write_text("def helper(): ...\n")
    write_template(tmp_path / "notes.txt")
    write_template(tmp_path / "nested" / "gamma.py")

    templates = list_templates([tmp_path])

    assert [t.display_name for t in templates] == ["Alpha", "beta"]
    assert templates[0].name == "Alpha.py"
    assert templates[0].path == str(tmp_path / "Alpha.py")
    assert templates[0].description == "A template."
    # Only the first line of the docstring is used
    assert templates[1].description == "Beta."


def test_list_templates_without_docstring(tmp_path: Path) -> None:
    (tmp_path / "plain.py").write_text("import marimo\n\napp = marimo.App()\n")
    [template] = list_templates([tmp_path])
    assert template.description is None


def test_list_templates_multiple_directories(tmp_path: Path) -> None:
    write_template(tmp_path / "a" / "one.py")
    write_template(tmp_path / "b" / "two.py")

    templates = list_templates(
        [tmp_path / "a", tmp_path / "missing", tmp_path / "b", tmp_path / "a"]
    )

    assert [t.display_name for t in templates] == ["one", "two"]


def test_read_template(tmp_path: Path) -> None:
    template = write_template(tmp_path / "template.py")
    assert read_template(str(template), [tmp_path]) == template.read_text()


@pytest.mark.parametrize(
    "path",
    [
        "/etc/passwd",
        "{tmp}/../outside.py",
        "{tmp}/nested/template.py",
        "{tmp}/template.txt",
    ],
)
def test_read_template_forbidden(tmp_path: Path, path: str) -> None:
    write_template(tmp_path.parent / "outside.py")
    write_template(tmp_path / "nested" / "template.py")
    write_template(tmp_path / "template.txt")

    with pytest.raises(HTTPException) as e:
        read_template(path.format(tmp=tmp_path), [tmp_path])
    assert e.value.status_code == HTTPStatus.FORBIDDEN


def test_read_template_not_found(tmp_path: Path) -> None:
    with pytest.raises(HTTPException) as e:
        read_template(str(tmp_path / "missing.py"), [tmp_path])
    assert e.value.status_code == HTTPStatus.NOT_FOUND


def test_read_template_invalid(tmp_path: Path) -> None:
    template = tmp_path / "invalid.py"
    template.write_text("import marimo\n\nprint('not a notebook')\n")

    with pytest.raises(HTTPException) as e:
        read_template(str(template), [tmp_path])
    assert e.value.status_code == HTTPStatus.BAD_REQUEST


@pytest.mark.skipif(
    sys.platform == "win32", reason="Symlinks require admin on Windows"
)
def test_symlinked_template_directory(tmp_path: Path) -> None:
    write_template(tmp_path / "real" / "template.py")
    link = tmp_path / "link"
    link.symlink_to(tmp_path / "real")

    [template] = list_templates([link])
    assert template.path == str(link / "template.py")
    assert "x = 1" in read_template(template.path, [link])
