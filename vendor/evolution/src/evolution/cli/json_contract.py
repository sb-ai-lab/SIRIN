"""Small, stable JSON envelope for machine-readable CLI commands."""

from __future__ import annotations

import json
from typing import Any, NoReturn

import typer


def emit_json(data: Any) -> None:
    typer.echo(json.dumps({"schema_version": 1, "ok": True, "data": data}, default=str))


def fail_json(kind: str, message: str, code: int = 1) -> NoReturn:
    typer.echo(message, err=True)
    typer.echo(
        json.dumps(
            {
                "schema_version": 1,
                "ok": False,
                "error": {"kind": kind, "message": message},
            }
        )
    )
    raise typer.Exit(code)
