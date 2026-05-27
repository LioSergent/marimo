# Templates Configuration

marimo lets you maintain a library of reusable notebook templates. 
If templates are detected, a dropdown appears on the home screen (top right)
for quick access.


## Configuration

Configure template directories in the relevant configuration file for your setup:

```toml title="marimo.toml"
[templates]
directories = ["~/my-templates", "./project-templates"]  # absolute, ~, or relative paths
```

```toml title="pyproject.toml"
[tool.marimo.templates]
directories = ["./templates"]  # relative paths resolved from pyproject.toml location
```

!!! note
    When `directories` is set in `pyproject.toml`, it replaces the user-level value rather than extending it.

## Template format

A template is a regular marimo `.py` notebook file. Any notebook can serve as a
template — just place it in a configured directory.

- The item name in the dropdown is the file name (with `.py` stripped).
- The item description in the dropdown corresponds to the first 60 characters
of the **module-level docstring**.

Example template file:
```python title="Client A base.py"

"""Load CSV from client A + basic outlier removal"""

import marimo

app = marimo.App(width="medium")

with app.setup:
    import marimo as mo

    import matplotlib.pyplot as plt
    import pandas as pd

    from myproj.data import remove_outliers

    plt.style.use(["mystyle"])


@app.cell(hide_code=True)
def _():
    mo.md(r"""# 1) Load and filter""")
    return

@app.cell
def _():
    df_raw = pd.read_csv(r"/some/path/file.csv", sep=";", decimal=",")
    df = remove_outliers(df_raw)
    return (df_raw, df)

if __name__ == "__main__":
    app.run()
```
