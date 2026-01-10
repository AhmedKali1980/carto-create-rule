# -*- coding: utf-8 -*-
"""
Common IO helpers for Carto NG modules (standalone)
- CSV loader & column picker
- Flow files discovery (prefer zone-filtered, else raw)
"""
import csv
from pathlib import Path
from typing import Dict, List, Tuple, Optional

def load_csv(path: Path):
    if not path.exists() or path.stat().st_size == 0:
        return [], []
    with path.open(newline="", encoding="utf-8") as f:
        r = csv.DictReader(f)
        rows = [{k: (v or "").strip() for k, v in row.items()} for row in r]
        return rows, (r.fieldnames or [])

def pick(cols: List[str], *cands: str) -> str:
    low = {c.lower(): c for c in (cols or [])}
    for c in cands:
        if c.lower() in low:
            return low[c.lower()]
    return ""

def get_flow_paths(raw: Path, derived: Path, start: str, end: str):
    cand_in = [derived/"flows_in.zone.csv", raw/f"flows_in_{start}_{end}.csv"]
    cand_out = [derived/"flows_out.zone.csv", raw/f"flows_out_{start}_{end}.csv"]
    p_in = next((p for p in cand_in if p.exists() and p.stat().st_size > 0), None)
    p_out = next((p for p in cand_out if p.exists() and p.stat().st_size > 0), None)
    return p_in, p_out
