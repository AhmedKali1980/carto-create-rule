
# -*- coding: utf-8 -*-
"""
flows_to_rules.py — Carto NG (v2.3.5-min)
- Tolère les arguments hérités de l'orchestrateur (ex. --ruleset-name-contains) pour éviter tout crash,
  mais ne les utilise PAS (on ne filtre jamais par ruleset_name).
- Écrit derived/scope.params.txt (app/env/role) depuis les arguments explicites de scope
  (si fournis), sinon fallback en récupérant les labels depuis le nom de l'Excel
  export_dupecheck.final_<app>-<env>-<role>_<ts>.xlsx (ordre: app, env, role). [orchestrateur]
- Appelle scope_rules_applicability.get_applicable_rules() qui filtre uniquement par ruleset_scope exact.
- Ajoute l’onglet "Scope Applicable Rules" dans l’Excel.
"""
import argparse
import csv
import logging
from pathlib import Path
from typing import List, Optional

import os
import sys
from openpyxl import load_workbook, Workbook

# >>> Import module (indépendant) — robuste
try:
    from modules.scope_rules_applicability import (
        get_applicable_rules,
        append_scope_rules_sheet
    )
except ModuleNotFoundError:
    # Cas 2 : exécution directe (python modules/flows_to_rules.py ...)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    from scope_rules_applicability import (
        get_applicable_rules,
        append_scope_rules_sheet
    )

__version__ = "2.3.5-min"

# --------------------------- logging -----------------------------------------
logger = logging.getLogger("flows_to_rules")

def setup_logging(level: str = "INFO") -> None:
    lvl = getattr(logging, level.upper(), logging.INFO)
    logger.setLevel(lvl)
    fmt = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
    ch = logging.StreamHandler()
    ch.setFormatter(fmt)
    for h in list(logger.handlers):
        logger.removeHandler(h)
    logger.addHandler(ch)

# --------------------------- csv utils ---------------------------------------
def pick(cols: List[str], *cands: str) -> str:
    low = {c.lower(): c for c in (cols or [])}
    for c in cands:
        if c.lower() in low:
            return low[c.lower()]
    return ''

def iter_csv_rows(path: Path):
    if (not path.exists()) or path.stat().st_size == 0:
        class _Empty:
            fieldnames_list: List[str] = []
            def __iter__(self):
                if False:  # pragma: no cover
                    yield {}
        return _Empty()
    fh = path.open(newline='', encoding='utf-8')
    reader = csv.DictReader(fh)
    class _Wrap:
        fieldnames_list = reader.fieldnames or []
        def __iter__(self):
            try:
                for row in reader:
                    yield {k: (v or '').strip() for k, v in row.items()}
            finally:
                try: fh.close()
                except Exception: pass
    return _Wrap()

# ----------------------- ensure selected scope file --------------------------
def _split_scope_tokens(base_scope: str) -> tuple[str, str, str]:
    """
    Split a scope string formatted as "<app>-<env>-<role>".

    App labels may contain '-' (UUID-like values). We therefore split from the right:
      - if 2 tokens => app, env
      - if >=3 tokens => app='-'.join(all but last two), env=penultimate, role=last
    """
    tokens = [t for t in (base_scope or "").split("-") if t]
    if len(tokens) < 2:
        return ("", "", "")
    if len(tokens) == 2:
        return (tokens[0], tokens[1], "")
    return ("-".join(tokens[:-2]), tokens[-2], tokens[-1])


def _ensure_selected_scope_file(
    derived_dir: Path,
    excel_path: Optional[str],
    scope_app: str = "",
    scope_env: str = "",
    scope_role: str = "",
) -> None:
    """
    Crée derived/scope.params.txt si absent, en extrayant <app>-<env>-<role> du nom de l'Excel:
      export_dupecheck.final_<base>_<ts>.xlsx   où <base> = "app-env-role"
    (ordre fixé par l’orchestrateur: app, env, role).
    """
    scope_file = derived_dir / "scope.params.txt"
    if scope_file.exists() and scope_file.stat().st_size > 0:
        return

    app = (scope_app or "").strip()
    env = (scope_env or "").strip()
    role = (scope_role or "").strip()
    # 1) depuis excel path (préféré)
    if (not app or not env) and excel_path:
        try:
            base = Path(excel_path).name  # export_dupecheck.final_<base>_<ts>.xlsx
            if ".final_" in base and base.endswith(".xlsx"):
                after = base.split(".final_", 1)[1]
                mid = after[:-5]  # enlever ".xlsx"
                base_seg = mid.rsplit("_", 1)[0] if "_" in mid else mid
                a, e, r = _split_scope_tokens(base_seg)
                if a and not app: app = a
                if e and not env: env = e
                if r and not role: role = r
        except Exception:
            pass

    # 2) fallback: depuis le parent du derived_dir (run folder), qui inclut déjà le suffixe app-env-role
    if (not app or not env) and derived_dir.parent.exists():
        try:
            run_name = derived_dir.parent.name  # <timestamp>_<app>-<env>-<role>
            if "_" in run_name:
                suffix = run_name.split("_", 1)[1]
                a, e, r = _split_scope_tokens(suffix)
                if a and not app: app = a
                if e and not env: env = e
                if r and not role: role = r
        except Exception:
            pass

    # Écrire le fichier (même si role vide)
    lines: List[str] = []
    if app: lines.append(f"app={app}")
    if env: lines.append(f"env={env}")
    if role: lines.append(f"role={role}")

    scope_file.parent.mkdir(parents=True, exist_ok=True)
    scope_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

# --------------------------- main --------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser('flows_to_rules_min')
    ap.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    ap.add_argument('--input-raw', required=True)
    ap.add_argument('--derived-dir', required=True)
    ap.add_argument('--conf', default='carto.conf')
    ap.add_argument('--start', required=True)
    ap.add_argument('--end', required=True)
    ap.add_argument('--excel')  # utilisé pour extraire app/env/role (strict minimum)
    ap.add_argument('--scope-app', default='', help='Scope app label (prioritaire pour scope.params.txt)')
    ap.add_argument('--scope-env', default='', help='Scope env label (prioritaire pour scope.params.txt)')
    ap.add_argument('--scope-role', default='', help='Scope role label (prioritaire pour scope.params.txt)')
    ap.add_argument('--log-level', default='INFO')

    # >>> Compat héritée orchestrateur (ACCEPTÉS MAIS IGNORÉS)
    ap.add_argument('--ruleset-name-contains', default='', help='LEGACY: ignoré.')
    ap.add_argument('--exclude-all-workloads-rules', action='store_true', help='LEGACY: ignoré.')
    ap.add_argument('--frh-filter-direction', choices=['ingress', 'egress'], help='LEGACY alias ignoré.')
    ap.add_argument('--frh-filter-proto', choices=['TCP', 'UDP', 'ICMP'], help='LEGACY alias ignoré.')
    ap.add_argument('--frh-filter-port', type=int, help='LEGACY alias ignoré.')

    args = ap.parse_args()
    setup_logging(args.log_level)

    raw = Path(args.input_raw)
    der = Path(args.derived_dir)

    # 1) Assurer la présence des labels utilisateur (strict minimum)
    _ensure_selected_scope_file(
        der,
        args.excel,
        scope_app=args.scope_app,
        scope_env=args.scope_env,
        scope_role=args.scope_role,
    )

    # 2) Calculer Strictement les règles applicables (via ruleset_scope exact)
    rules_applicables, unmatched_rows, eff_rows = get_applicable_rules(raw, der)

    # 3) Ajouter l’onglet "Scope Applicable Rules" dans l’Excel (si fourni)
    if args.excel:
        try:
            ok = append_scope_rules_sheet(Path(args.excel), rules_applicables, eff_rows)
            if ok:
                logger.info("Excel updated: appended 'Scope Applicable Rules' (strict minimum)")
        except Exception as e:
            logger.warning("Excel append failed: %s", e)

    return 0

if __name__ == '__main__':
    sys.exit(main())
