# Copyright 2026 Marimo. All rights reserved.
"""User-defined notebook templates.

A template is a marimo notebook stored in one of the directories listed under
`templates.directories` in the marimo config. Opening a template creates a
new, untitled notebook seeded with the template's code; the template file
itself is never modified.
"""

from __future__ import annotations

import ast
import os
from pathlib import Path
from typing import TYPE_CHECKING

from marimo import _loggers
from marimo._ast.load import load_app_from_contents
from marimo._server.files.directory_scanner import is_marimo_app
from marimo._server.models.home import TemplateFile
from marimo._utils.http import HTTPException, HTTPStatus

if TYPE_CHECKING:
    from marimo._config.config import MarimoConfig

LOGGER = _loggers.marimo_logger()


def get_template_directories(config: MarimoConfig) -> list[Path]:
    """Return the configured template directories as absolute paths."""
    directories = config.get("templates", {}).get("directories", [])
    if not isinstance(directories, list):
        return []
    return [_absolute(Path(d).expanduser()) for d in directories]


def list_templates(directories: list[Path]) -> list[TemplateFile]:
    """List the marimo notebooks directly inside `directories`.

    Missing directories and non-marimo Python files are skipped. Templates
    are sorted by display name.
    """
    seen: set[Path] = set()
    templates: list[TemplateFile] = []
    for directory in directories:
        if not directory.is_dir():
            LOGGER.warning(
                "Templates directory %s not found - ignoring", directory
            )
            continue
        for path in directory.glob("*.py"):
            if path in seen or not is_marimo_app(str(path)):
                continue
            seen.add(path)
            templates.append(
                TemplateFile(
                    name=path.name,
                    path=str(path),
                    display_name=path.stem,
                    description=_read_description(path),
                )
            )
    return sorted(templates, key=lambda t: t.display_name.lower())


def read_template(path: str, directories: list[Path]) -> str:
    """Read the source code of the template at `path`.

    Raises:
        HTTPException: If `path` is not a template in one of `directories`
            (403), does not exist (404), or is not a valid marimo
            notebook (400).
    """
    template = _absolute(Path(path))
    if template.suffix != ".py" or template.parent not in directories:
        raise HTTPException(
            status_code=HTTPStatus.FORBIDDEN,
            detail="Template is not in a configured templates directory.",
        )
    if not template.is_file():
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND,
            detail=f"Template not found: {template.name}",
        )

    contents = template.read_text(encoding="utf-8")
    try:
        load_app_from_contents(contents, template)
    except Exception as e:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail=f"Template {template.name} is not a valid marimo notebook.",
        ) from e
    return contents


def _absolute(path: Path) -> Path:
    # Normalize `..` without resolving symlinks, so that a template directory
    # may itself be (or contain) a symlink.
    return Path(os.path.abspath(path))


def _read_description(path: Path) -> str | None:
    """The first line of the template's module docstring, if any."""
    try:
        docstring = ast.get_docstring(
            ast.parse(path.read_text(encoding="utf-8"))
        )
    except (OSError, SyntaxError, ValueError):
        return None
    if not docstring:
        return None
    return docstring.strip().splitlines()[0]
