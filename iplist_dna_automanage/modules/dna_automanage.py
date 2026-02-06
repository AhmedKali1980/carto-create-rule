#!/usr/bin/env python3
"""DNA IPList auto-management orchestrator.

This script exports data from PCE with workloader, discovers required DNS IPLists,
creates/updates only DNA_* IPLists, and sends an execution report by email.
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import html
import logging
import os
import re
import subprocess
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Set, Tuple

from email_utils import parse_recipients, send_carto_notification


@dataclass
class StepResult:
    name: str
    started_at: dt.datetime
    ended_at: dt.datetime
    rc: int
    details: str = ""


def read_conf(path: Path) -> Dict[str, str]:
    conf: Dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        s = line.strip()
        if not s or s.startswith("#") or "=" not in s:
            continue
        k, v = s.split("=", 1)
        conf[k.strip()] = v.strip()
    return conf


def run_step(name: str, cmd: List[str], cwd: Path, logger: logging.Logger) -> StepResult:
    started = dt.datetime.now()
    proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    ended = dt.datetime.now()
    details = (proc.stdout or "") + ("\n" + proc.stderr if proc.stderr else "")
    logger.info("%s rc=%s", name, proc.returncode)
    if proc.returncode != 0:
        logger.error("%s failed: %s", name, details)
    return StepResult(name=name, started_at=started, ended_at=ended, rc=proc.returncode, details=details.strip())


def csv_rows(path: Path) -> List[Dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def choose(row: Dict[str, str], *keys: str, default: str = "") -> str:
    for k in keys:
        if k in row and row[k] is not None:
            return row[k].strip()
    return default


def sanitize_name(fqdn: str) -> str:
    safe = re.sub(r"[^A-Za-z0-9-]", ".", fqdn)
    return f"DNA_{safe}-IPL"


def parse_last_seen(desc: str) -> dt.date | None:
    m = re.search(r"Last seen at\s*:\s*(\d{4}-\d{2}-\d{2})", desc or "")
    if not m:
        return None
    return dt.date.fromisoformat(m.group(1))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    conf_path = Path(args.config).resolve()
    conf = read_conf(conf_path)

    now = dt.datetime.now()
    run_dir = (root / conf.get("EXPORT_ROOT", "./RUNS") / now.strftime(conf.get("DATE_FMT", "%Y%m%d-%H%M%S"))).resolve()
    run_dir.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        handlers=[logging.FileHandler(run_dir / "execution.log", encoding="utf-8"), logging.StreamHandler()],
    )
    logger = logging.getLogger("dna_automanage")

    steps: List[StepResult] = []
    bin_dir = root / "bin"

    export_ipl = run_dir / "export_iplists.csv"
    export_wkld = run_dir / "export_wkld.m.csv"
    export_label = run_dir / "export_label.csv"

    for name, cmd in [
        ("export_iplists", [str(bin_dir / "workloader_ipl_export.sh"), str(export_ipl)]),
        ("export_managed_workloads", [str(bin_dir / "workloader_wkld_m_export.sh"), str(export_wkld)]),
        ("export_labels", [str(bin_dir / "workloader_label_export.sh"), str(export_label)]),
    ]:
        step = run_step(name, cmd, root, logger)
        steps.append(step)
        if step.rc != 0:
            return 1

    labels_rows = csv_rows(export_label)
    wkld_rows = csv_rows(export_wkld)

    excluded_prefixes = [p for p in conf.get("EXCLUDED_LABEL_PREFIXES", "").split(";") if p]
    wkld_apps: Set[str] = set()
    for r in wkld_rows:
        app_value = choose(r, "app", "App", "APP", default="")
        if not app_value:
            vals = list(r.values())
            if len(vals) > 7:
                app_value = (vals[7] or "").strip()
        if app_value and not any(app_value.startswith(p) for p in excluded_prefixes):
            wkld_apps.add(app_value)

    label_href_by_value = {choose(r, "value", "Value"): choose(r, "href", "Href") for r in labels_rows}
    href_labels_wkld = sorted({label_href_by_value[v] for v in wkld_apps if v in label_href_by_value and label_href_by_value[v]})

    href_labels_app = sorted({choose(r, "href", "Href") for r in labels_rows if choose(r, "key", "Key") == "app" and choose(r, "href", "Href")})

    (run_dir / "href_labels.wkld.m.csv").write_text("href\n" + "\n".join(href_labels_wkld) + "\n", encoding="utf-8")
    (run_dir / "href_labels.app.csv").write_text("href\n" + "\n".join(href_labels_app) + "\n", encoding="utf-8")
    (run_dir / "service.exlude.csv").write_text("PortNumber,NumericIANA\n0,1\n0,58\n", encoding="utf-8")

    days = int(conf.get("NUMBER_OF_DAYS_AGO", "7"))
    start_date = (now.date() - dt.timedelta(days=days)).isoformat()
    end_date = now.date().isoformat()
    flow_file = run_dir / f"flow-out-fqdn-{now.strftime('%Y%m%d-%H%M%S')}.csv"

    step = run_step(
        "export_traffic",
        [
            str(bin_dir / "workloader_traffic_out.sh"),
            str(run_dir / "href_labels.wkld.m.csv"),
            str(run_dir / "href_labels.app.csv"),
            str(run_dir / "service.exlude.csv"),
            start_date,
            end_date,
            str(flow_file),
        ],
        root,
        logger,
    )
    steps.append(step)
    if step.rc != 0:
        return 1

    flow_rows = csv_rows(flow_file)
    filtered_flow: List[Dict[str, str]] = []
    ip_pattern = re.compile(r"^(?:IP-)?\d{1,3}(?:-\d{1,3}){3}(?:\..*)?$")
    for r in flow_rows:
        vals = list(r.values())
        fqdn = choose(r, "Destination FQDN", "destination_fqdn", default=vals[25].strip() if len(vals) > 25 else "")
        if not fqdn or ".compute." in fqdn or ip_pattern.match(fqdn):
            continue
        filtered_flow.append(r)

    with (run_dir / flow_file.name).open("w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=flow_rows[0].keys())
        wr.writeheader()
        wr.writerows(filtered_flow)

    ipl_rows = csv_rows(export_ipl)
    dna_prefix = conf.get("DNA_IPLIST_PREFIX", "DNA_")
    existing: Dict[str, Dict[str, str]] = {}
    for r in ipl_rows:
        name = choose(r, "name", "Name")
        if not name.startswith(dna_prefix):
            continue
        fqdn = choose(r, "fqdns", "FQDNS", "fqdn")
        existing[fqdn] = {
            "name": name,
            "description": choose(r, "description", "Description"),
            "include": choose(r, "include", "Include"),
            "fqdns": fqdn,
            "href": choose(r, "href", "Href"),
        }

    new_map: Dict[str, Set[str]] = defaultdict(set)
    for r in filtered_flow:
        vals = list(r.values())
        fqdn = choose(r, "Destination FQDN", default=vals[25].strip() if len(vals) > 25 else "")
        ip = choose(r, "Destination IP", default=vals[14].strip() if len(vals) > 14 else "")
        if fqdn and ip:
            new_map[fqdn].add(ip)

    today = now.date().isoformat()
    create_rows, update_rows = [], []
    created_for_report, updated_for_report = [], []
    for fqdn, ips in sorted(new_map.items()):
        include = ";".join(sorted(ips))
        description = f"Last seen at : {today}"
        if fqdn in existing:
            old_ips = set(filter(None, existing[fqdn]["include"].split(";")))
            update_rows.append({"href": existing[fqdn]["href"], "description": description, "include": include})
            updated_for_report.append((fqdn, sorted(old_ips), sorted(ips)))
        else:
            create_rows.append({"name": sanitize_name(fqdn), "description": description, "include": include, "fqdns": fqdn})
            created_for_report.append((fqdn, sorted(ips)))

    create_csv = run_dir / "new.iplist.new.fqdns.csv"
    update_csv = run_dir / "update.iplist.existing.fqdns.csv"
    with create_csv.open("w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=["name", "description", "include", "fqdns"])
        wr.writeheader(); wr.writerows(create_rows)
    with update_csv.open("w", encoding="utf-8", newline="") as f:
        wr = csv.DictWriter(f, fieldnames=["href", "description", "include"])
        wr.writeheader(); wr.writerows(update_rows)

    for name, path in [("import_new_iplists", create_csv), ("update_existing_iplists", update_csv)]:
        if sum(1 for _ in path.open("r", encoding="utf-8")) > 1:
            steps.append(run_step(name, [str(bin_dir / "workloader_ipl_import.sh"), str(path)], root, logger))

    stale_threshold = int(conf.get("STALE_LAST_SEEN_DAYS", "21"))
    stale = []
    for v in existing.values():
        d = parse_last_seen(v["description"])
        if d and (now.date() - d).days > stale_threshold:
            stale.append((v["name"], v["fqdns"], v["description"], v["href"]))

    ip_to_lists: Dict[str, Set[str]] = defaultdict(set)
    for v in existing.values():
        for ip in filter(None, v["include"].split(";")):
            ip_to_lists[ip].add(v["name"])
    duplicate_ips = {ip: sorted(names) for ip, names in ip_to_lists.items() if len(names) > 1}

    report = run_dir / "report.txt"
    with report.open("w", encoding="utf-8") as f:
        f.write("DNA IPList Auto-Manage Report\n\n")
        f.write("Section 1 - Execution log\n")
        for s in steps:
            f.write(f"- {s.name}: rc={s.rc}; started={s.started_at}; ended={s.ended_at}\n")
        f.write("\nNew IPLists created:\n")
        for fqdn, ips in created_for_report:
            f.write(f"  * {fqdn} -> {','.join(ips)}\n")
        f.write("\nUpdated IPLists:\n")
        for fqdn, old_ips, new_ips in updated_for_report:
            add = sorted(set(new_ips) - set(old_ips))
            rem = sorted(set(old_ips) - set(new_ips))
            f.write(f"  * {fqdn}\n")
            f.write(f"      + added: {','.join(add) if add else '-'}\n")
            f.write(f"      - removed: {','.join(rem) if rem else '-'}\n")

        f.write("\nSection 2 - Deletion candidates (>3 weeks)\n")
        for name, fqdn, desc, href in stale:
            f.write(f"  * {name} | {fqdn} | {desc} | {href}\n")

        f.write("\nSection 3 - IP addresses present in multiple DNA IPLists\n")
        for ip, names in duplicate_ips.items():
            f.write(f"  * {ip}: {','.join(names)}\n")

    recipients = parse_recipients(conf.get("MAIL_TO", ""))
    if recipients and conf.get("SMTP_SERVER", "").strip():
        body_text = report.read_text(encoding="utf-8")
        body_html = f"<pre>{html.escape(body_text)}</pre>"
        send_carto_notification(
            conf=conf,
            recipients=recipients,
            subject=f"DNA IPList Auto-Manage report - {now.strftime('%Y-%m-%d %H:%M:%S')}",
            body_text=body_text,
            body_html=body_html,
            attachment_path=report,
            logger=logger,
        )
    else:
        logger.warning("Email not sent (MAIL_TO/SMTP_SERVER not configured).")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
