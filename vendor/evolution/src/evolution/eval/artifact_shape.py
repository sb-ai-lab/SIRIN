"""Value-free structural shape of agent-produced files (counts/classes only; no labels/values)."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def _err(exc: Exception) -> dict[str, Any]:
    return {"parse_ok": False, "error": type(exc).__name__}


def _json_depth(obj: Any, _cap: int = 8) -> int:
    if _cap <= 0:
        return 0
    if isinstance(obj, dict):
        return 1 + max((_json_depth(v, _cap - 1) for v in obj.values()), default=0)
    if isinstance(obj, list):
        return 1 + max((_json_depth(v, _cap - 1) for v in obj), default=0)
    return 0


def shape_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except Exception as exc:
        return _err(exc)
    if isinstance(data, dict):
        return {"top_type": "object", "n_keys": len(data), "depth_ok": _json_depth(data) <= 8}
    if isinstance(data, list):
        return {"top_type": "array", "n_keys": None, "depth_ok": _json_depth(data) <= 8}
    return {"top_type": "scalar", "n_keys": None, "depth_ok": True}


def shape_csv(path: Path) -> dict[str, Any]:
    try:
        with Path(path).open("r", encoding="utf-8", newline="") as fh:
            reader = csv.reader(fh)
            rows = 0
            n_cols = 0
            for i, row in enumerate(reader):
                if i == 0:
                    n_cols = len(row)
                rows += 1
        return {"n_cols": n_cols, "n_rows": max(0, rows - 1), "has_header": rows > 0}
    except Exception as exc:
        return _err(exc)


def shape_xlsx(path: Path) -> dict[str, Any]:
    try:
        import openpyxl

        wb = openpyxl.load_workbook(Path(path), read_only=True, data_only=True)
        dims = [0, 0]
        for ws in wb.worksheets:
            dims[0] = max(dims[0], int(ws.max_row or 0))
            dims[1] = max(dims[1], int(ws.max_column or 0))
        n = len(wb.sheetnames)
        wb.close()
        return {"n_sheets": n, "dims": dims}
    except Exception as exc:
        return _err(exc)


def shape_for(path: Path) -> dict[str, Any] | None:
    p = Path(path)
    suf = p.suffix.lower()
    if suf == ".json":
        return shape_json(p)
    if suf in (".csv", ".tsv"):
        return shape_csv(p)
    if suf in (".xlsx", ".xls"):
        return shape_xlsx(p)
    return None
