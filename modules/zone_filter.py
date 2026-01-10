#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
modules/zone_filter.py — Carto NG

Purpose
-------
When --network-zone is enabled, we can optionally pre-filter the raw flow extracts to keep only
"EAST-WEST" flows strictly inside a network zone defined by an IPList.

Inputs (from RUNS/<run_id>/raw):
- export_iplists.csv (must contain the zone IPList and its complement)
- flows_out_<start>_<end>.csv
- flows_in_<start>_<end>.csv

Outputs (to RUNS/<run_id>/derived):
- flows_out.zone.csv
- flows_in.zone.csv

Notes
-----
- The zone IPList is expected to contain positive CIDRs (may include Illumio tags like "#GEN1").
- The complement IPList must exist: "ZNOT_<zone>". It may contain "!" negations; we do not parse it here.
- This script is intentionally standalone (no dependency on propose_rule_for_scope.py) to keep it lightweight.
"""

from __future__ import annotations

import argparse
import csv
import ipaddress
import os
import re
import sys
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple


def _log(msg: str) -> None:
    print(f"[zone-filter] {msg}")


def _norm(s: str) -> str:
    return (s or "").strip().strip('"').strip("'").strip().lower()


def _pick_col(cols: List[str], *cands: str) -> str:
    low = {c.lower(): c for c in cols}
    for c in cands:
        if c.lower() in low:
            return low[c.lower()]
    return ""


_SPLIT_RE = re.compile(r"[;\t,\|]+")


def _extract_networks_from_include(include_value: str) -> List[ipaddress._BaseNetwork]:
    """
    Parse export_iplists.csv 'include' content into ip_network objects.

    Supports tokens like:
      - 171.84.192.0/21#GEN1;171.84.0.0/16#GEN2
      - 10.0.0.1 (treated as /32)
    Ignores tokens starting with "!" (negation).
    """
    s = (include_value or "").strip()
    if not s:
        return []

    nets: List[ipaddress._BaseNetwork] = []
    # Split on common separators; also split on whitespace as fallback
    parts: List[str] = []
    for p in _SPLIT_RE.split(s):
        p = p.strip()
        if not p:
            continue
        # further split on whitespace to be safe
        for q in p.split():
            q = q.strip()
            if q:
                parts.append(q)

    for tok in parts:
        t = tok.strip()
        if not t:
            continue
        if t.startswith("!"):
            # Negations are expected in ZNOT_* but not in the positive zone list.
            continue
        # Remove Illumio tags like "#GEN1"
        if "#" in t:
            t = t.split("#", 1)[0].strip()
        # Remove trailing inline comments (rare)
        if t.startswith("#"):
            continue

        try:
            if "/" in t:
                nets.append(ipaddress.ip_network(t, strict=False))
            else:
                ip = ipaddress.ip_address(t)
                suffix = "/32" if ip.version == 4 else "/128"
                nets.append(ipaddress.ip_network(f"{t}{suffix}", strict=False))
        except Exception:
            # Ignore non-network tokens silently; we'll fail later if nothing valid is found.
            continue

    # Deduplicate while keeping a stable order (IPv4 then IPv6, broader to narrower)
    uniq: Dict[Tuple[int, int, str], ipaddress._BaseNetwork] = {}
    for n in nets:
        key = (n.version, n.prefixlen, str(n))
        uniq[key] = n
    out = list(uniq.values())
    out.sort(key=lambda n: (n.version, -n.prefixlen, str(n)))
    return out


_IPV4_RE = re.compile(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b")


def _extract_first_ip_token(value: str) -> str:
    s = (value or "").strip()
    if not s:
        return ""
    # Quick IPv4
    m = _IPV4_RE.search(s)
    if m:
        return m.group(1)

    # IPv6 best-effort: split by common separators and try parse
    for tok in re.split(r"[\s,;|]+", s):
        t = tok.strip()
        if not t:
            continue
        # strip ports like [2001:db8::1]:443 or 2001:db8::1:443 (ambiguous)
        t = t.strip("[]")
        # If it looks like IPv6, try parse
        if ":" in t:
            # remove trailing :port if clearly present (only if last chunk is all digits AND there are 2+ colons)
            if t.count(":") >= 2:
                last = t.rsplit(":", 1)[-1]
                if last.isdigit():
                    t = t.rsplit(":", 1)[0]
            try:
                ipaddress.ip_address(t)
                return t
            except Exception:
                continue
    return ""


def _ip_in_nets(ip_s: str, nets_v4: List[ipaddress.IPv4Network], nets_v6: List[ipaddress.IPv6Network]) -> bool:
    if not ip_s:
        return False
    try:
        ip = ipaddress.ip_address(ip_s)
    except Exception:
        return False
    if ip.version == 4:
        return any(ip in n for n in nets_v4)
    return any(ip in n for n in nets_v6)


def _find_flow_pair(raw_dir: Path, start: str, end: str) -> Tuple[Path, Path]:
    # 1) exact names
    out_exact = raw_dir / f"flows_out_{start}_{end}.csv"
    in_exact  = raw_dir / f"flows_in_{start}_{end}.csv"
    if out_exact.exists() and in_exact.exists():
        return out_exact, in_exact

    # 2) fallback: latest matching pair
    outs = sorted(raw_dir.glob("flows_out_*.csv"))
    ins  = sorted(raw_dir.glob("flows_in_*.csv"))
    if not outs or not ins:
        raise FileNotFoundError(f"Could not find flows_{'out'}/flows_{'in'} CSVs in {raw_dir}")

    return outs[-1], ins[-1]


def _load_zone_networks(raw_dir: Path, zone_name: str) -> Tuple[str, str, List[ipaddress._BaseNetwork]]:
    ipl_csv = raw_dir / "export_iplists.csv"
    if not ipl_csv.exists():
        raise FileNotFoundError(f"{ipl_csv} not found (required for --network-zone)")

    with ipl_csv.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        cols = reader.fieldnames or []
        if not cols:
            raise ValueError(f"{ipl_csv} has no header (required for --network-zone)")

        c_name = _pick_col(cols, "name", "iplist_name")
        c_inc = _pick_col(cols, "include", "includes", "ip_ranges", "cidrs")
        if not (c_name and c_inc):
            raise ValueError(f"{ipl_csv} missing required columns for --network-zone (need name/include)")

        zone_key = _norm(zone_name)
        znot_name = f"ZNOT_{zone_name.strip()}"
        znot_key = _norm(znot_name)

        zone_row: Optional[Dict[str, str]] = None
        znot_found = False

        for r in reader:
            n = _norm(r.get(c_name, ""))
            if n == zone_key:
                zone_row = r
            elif n == znot_key:
                znot_found = True

        if zone_row is None:
            raise ValueError(f"IPList '{zone_name}' not found in {ipl_csv.name} (looked in column '{c_name}')")
        if not znot_found:
            raise ValueError(f"Complement IPList '{znot_name}' not found in {ipl_csv.name} (required)")

        nets = _extract_networks_from_include(zone_row.get(c_inc, "") or "")
        if not nets:
            sample = (zone_row.get(c_inc, "") or "")[:120]
            raise ValueError(
                f"IPList '{zone_name}' has no parsable CIDRs in column '{c_inc}'. "
                f"Example include='{sample}...'"
            )

        return zone_name.strip(), znot_name, nets


def _filter_one_file(in_path: Path, out_path: Path, nets: List[ipaddress._BaseNetwork]) -> Tuple[int, int]:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    nets_v4 = [n for n in nets if isinstance(n, ipaddress.IPv4Network)]
    nets_v6 = [n for n in nets if isinstance(n, ipaddress.IPv6Network)]

    kept = 0
    total = 0

    with in_path.open("r", encoding="utf-8-sig", newline="") as fin:
        reader = csv.DictReader(fin)
        fieldnames = reader.fieldnames or []
        if not fieldnames:
            raise ValueError(f"{in_path.name} has no header")

        # find IP columns (best effort)
        src_col = ""
        dst_col = ""
        for c in fieldnames:
            lc = (c or "").lower()
            if not src_col and ("source ip" in lc or "src ip" in lc):
                src_col = c
            if not dst_col and ("destination ip" in lc or "dst ip" in lc):
                dst_col = c

        if not (src_col and dst_col):
            raise ValueError(f"{in_path.name} missing Source IP / Destination IP columns")

        with out_path.open("w", encoding="utf-8", newline="") as fout:
            writer = csv.DictWriter(fout, fieldnames=fieldnames)
            writer.writeheader()

            for row in reader:
                total += 1
                src_ip = _extract_first_ip_token(row.get(src_col, "") or "")
                dst_ip = _extract_first_ip_token(row.get(dst_col, "") or "")
                if _ip_in_nets(src_ip, nets_v4, nets_v6) and _ip_in_nets(dst_ip, nets_v4, nets_v6):
                    kept += 1
                    writer.writerow(row)

    return kept, total


def main() -> int:
    ap = argparse.ArgumentParser("zone_filter")
    ap.add_argument("--input-raw", required=True, help="RUN/raw directory")
    ap.add_argument("--derived-dir", required=True, help="RUN/derived directory")
    ap.add_argument("--zone-iplist", required=True, help="Zone IPList name (must exist in export_iplists.csv)")
    ap.add_argument("--start", required=True, help="YYYY-MM-DD start date (used to locate raw flow files)")
    ap.add_argument("--end", required=True, help="YYYY-MM-DD end date (used to locate raw flow files)")
    ap.add_argument("--debug", action="store_true", default=False)
    args = ap.parse_args()

    t0 = time.perf_counter()
    raw_dir = Path(args.input_raw)
    der_dir = Path(args.derived_dir)

    try:
        zone_name, znot_name, nets = _load_zone_networks(raw_dir, args.zone_iplist)
        _log(f"network-zone: zone='{zone_name}' znot='{znot_name}' nets={len(nets)}")
        out_in, in_in = _find_flow_pair(raw_dir, args.start, args.end)

        out_out = der_dir / "flows_out.zone.csv"
        in_out = der_dir / "flows_in.zone.csv"

        kept_out, total_out = _filter_one_file(out_in, out_out, nets)
        kept_in, total_in = _filter_one_file(in_in, in_out, nets)

        dt = time.perf_counter() - t0
        _log(f"flows kept: out={kept_out}/{total_out} in={kept_in}/{total_in} -> written {out_out.name} / {in_out.name} ({dt:.2f}s)")
        return 0
    except Exception as e:
        _log(f"ERROR: {e}")
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
