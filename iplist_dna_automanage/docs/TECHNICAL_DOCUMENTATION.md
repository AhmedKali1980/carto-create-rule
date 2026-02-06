# Technical Documentation - iplist_dna_automanage

## 1. Objective
This repository automates lifecycle management of Illumio IPLists that **must start with `DNA_`**. It exports workloads, labels, and traffic, computes FQDN deltas, imports new/updated IPLists, and sends an English report by email.

## 2. Repository structure
- `bin/cron_job.sh`: cron entrypoint.
- `bin/workloader_common.sh`: shared retry/backoff + command assembly.
- `bin/workloader_ipl_export.sh`: exports IPLists.
- `bin/workloader_wkld_m_export.sh`: exports managed workloads.
- `bin/workloader_label_export.sh`: exports labels.
- `bin/workloader_traffic_out.sh`: exports outbound traffic with include/exclude files.
- `bin/workloader_ipl_import.sh`: imports/updates IPLists.
- `modules/dna_automanage.py`: orchestration and reporting logic.
- `modules/email_utils.py`: SMTP sender helper.
- `conf/global.conf`: global parameters.
- `RUNS/`: runtime output folders (`YYYYmmdd-HHMMSS`).

## 3. Implemented workflow
1. Export `export_iplists.csv`, `export_wkld.m.csv`, `export_label.csv`.
2. Parse managed workload `app` labels and build `href_labels.wkld.m.csv`.
3. Filter labels where `key=app` and build `href_labels.app.csv`.
4. Create `service.exlude.csv` excluding ICMP/ICMPv6.
5. Export outbound flows into `flow-out-fqdn-<timestamp>.csv`.
6. Purge flow rows where destination FQDN is empty, contains `.compute.`, or matches IP-style hostnames.
7. Parse existing DNA_* IPLists only (`name starts with DNA_`).
8. Build new FQDN/IP map from filtered flow.
9. Create:
   - `new.iplist.new.fqdns.csv` with `name,description,include,fqdns`.
   - `update.iplist.existing.fqdns.csv` with `href,description,include`.
10. Import create/update CSVs using `workloader_ipl_import.sh`.
11. Build report sections:
   - Execution status with response code and timestamps.
   - Created and updated DNA IPLists (added/removed IPs).
   - Deletion candidates with `Last seen at` older than 3 weeks.
   - IP addresses present in multiple DNA IPLists.
12. Send report by email using SMTP settings from `global.conf`.

## 4. Safety controls
- Strict scope: only `DNA_` prefixed IPLists are read/updated.
- Label exclusions by prefix are configurable (`EXCLUDED_LABEL_PREFIXES`).
- Flow query window is configurable (`NUMBER_OF_DAYS_AGO`).

## 5. Parameters to customize
Edit `conf/global.conf`:
- Workloader binary/config paths.
- SMTP and recipients (`MAIL_TO`).
- Retry policy.
- Prefix filters.
- Stale threshold days.

## 6. Outputs per run
Under `RUNS/<timestamp>/`:
- Raw exports (`export_*.csv`).
- Derived filters (`href_labels.*.csv`, `service.exlude.csv`).
- Filtered flows (`flow-out-fqdn-*.csv`).
- Import payloads (`new...csv`, `update...csv`).
- `execution.log` and `report.txt`.

## 7. DOCX generation
To avoid PR errors on platforms that reject binary files, the `.docx` is generated locally from the Markdown source:

```bash
python3 docs/build_docx.py
```

This command creates `docs/TECHNICAL_DOCUMENTATION.docx`.
