# Notebook templates

marimo lets you keep a library of notebooks to use as starting points for new
notebooks, for example to share imports, data loading code, or plotting
styles across analyses.

When templates are configured, a **Templates** dropdown appears at the top
right of the home page (`marimo edit` on a directory). Choosing a template
opens a new, untitled notebook with a copy of the template's code; the
template itself is never modified.

## Configuration

List the directories that contain your templates in your
[user configuration](index.md#user-configuration-file) or in your project's
`pyproject.toml`:

```toml title="marimo.toml"
[templates]
directories = ["~/marimo-templates"]
```

```toml title="pyproject.toml"
[tool.marimo.templates]
directories = ["templates"]
```

In `marimo.toml`, use absolute paths or paths starting with `~`. In
`pyproject.toml`, relative paths are resolved from the directory containing
`pyproject.toml`.

!!! note
    When `directories` is set in `pyproject.toml`, it replaces the value from
    your user configuration rather than extending it.

## Writing a template

Any marimo notebook can serve as a template: put it directly inside one of
the configured directories. Python files that aren't marimo notebooks are
ignored.

- The template's name in the dropdown is its file name, without `.py`.
- The first line of the notebook's module docstring, if any, is shown as its
  description.

```python title="client_a_analysis.py"
"""Load client A's CSV export and remove outliers."""

import marimo

app = marimo.App(width="medium")

with app.setup:
    import marimo as mo
    import pandas as pd

    from myproject.data import remove_outliers


@app.cell(hide_code=True)
def _():
    mo.md(r"""# Load and filter""")
    return


@app.cell
def _():
    df_raw = pd.read_csv("data/client_a.csv", sep=";", decimal=",")
    df = remove_outliers(df_raw)
    return df, df_raw


if __name__ == "__main__":
    app.run()
```

App configuration (such as `width`) and script metadata (such as
[sandbox dependencies](../package_management/inlining_dependencies.md)) are
carried over to the new notebook.
