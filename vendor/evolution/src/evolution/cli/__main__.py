"""Enable ``python -m evolution.cli`` (the package has no console script when
the project is not pip-installed)."""

from __future__ import annotations

from evolution.cli.main import app

if __name__ == "__main__":
    app()
