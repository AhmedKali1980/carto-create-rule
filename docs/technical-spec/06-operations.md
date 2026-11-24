# Operations, replay and troubleshooting

## Development and deployment prerequisites

Use the existing checkout; no worktree is needed for normal tasks. Run from the repository root with Python 3.12 (validated here), pandas and openpyxl. Bash, awk, tee, mktemp and core file utilities are used; `timeout` enables wrapper attempt limits. Workloader and its YAML configuration are deployment prerequisites. Do not copy credentials into repository examples.

This checkout is incomplete for live extraction: root scripts `workloader_label.sh`, `workloader_labelgroup.sh`, `workloader_wkld_m.sh`, `workloader_wkld_u.sh`, `workloader_process_bulk.sh`, `workloader_process.sh`, `workloader_ruleset.sh`, `workloader_rule_enabled.sh` and `workloader_dupecheck.sh` are referenced but absent. `modules/recertify_rules.py` and `modules/propose_rules_for_app.py` are also absent. Some similarly named scripts in the DNA subproject have different invocation contracts and are not drop-in replacements.

Confirm deployed script revision, wrappers, executable/config paths and PCE permissions before running a production cartography. No dependency manifest or CI/test suite is supplied by the application baseline. Local validation does not prove live API compatibility.

## Typical cartography command

```bash
source .venv/bin/activate
python3 carto_ng_orchestrator.py \
  --days 30 --app APMA_SAMPLE --env PRD --role DB.ORA.GEN1 \
  --strategy-intra-app allow \
  --strategy-ingress finegrained --strategy-egress finegrained \
  --excel-stream-update --skip-pce-fqdn-enrichment
```

This is a template requiring deployment prerequisites, not a claim that live execution works here. It uses the default CreateNew branch. Do not add `--FlowRuleReview` on this baseline: its conflict with default CreateNew aborts the run. The skip flag prevents the temporary-IPList enrichment phase; the normal run still performs extraction. Email requires explicit `--mail-to` and valid SMTP settings.

## DEV-STUB is per-export replay

Provide readable files for each source to avoid unexpected Workloader calls. Use all of: `--dev-stub-label`, `--dev-stub-labelgroup`, `--dev-stub-iplists`, `--dev-stub-wkld-m`, `--dev-stub-wkld-u`, `--dev-stub-processes` (or bulk alternative), `--dev-stub-ruleset`, `--dev-stub-rules-enabled`, `--dev-stub-dupecheck`. Supply `--dev-flow-stub` together with `--dev-flow-stub-out` and `--dev-flow-stub-in`. Also skip PCE FQDN enrichment and omit email when replaying offline.

Executable and YAML existence checks still run. A failed `dev_copy` logs a warning and returns false; callers commonly continue without forcing a fresh export or aborting. Missing process stubs explicitly cause a live process export attempt. Validate every copy before trusting downstream output.

A historical flow source is copied to a filename using the replay's newly calculated date window. Consequently timestamps in names/Summary can differ from the dataset's actual dates. Record original dates, source run, exact CLI, config and input checksums with the replay. Use a dedicated run directory and avoid stale `derived/scope.params.txt` or zone files.

For a controlled module-only replay with explicit original dates:

```bash
python3 modules/propose_rule_for_scope.py \
  --input-raw /path/to/run/raw --derived-dir /path/to/run/derived \
  --start 2026-10-08 --end 2026-11-07 --conf carto.conf \
  --excel /path/to/copied-workbook.xlsx --scope-role DB.ORA.GEN1 \
  --strategy-intra-app allow --strategy-ingress finegrained \
  --strategy-egress finegrained
```

The module reloads applicability using the per-run scope file. Use a workbook copy: append operations replace sheets, and partial writes can survive an error. Module-only invocation does not perform all orchestrator cleanup/finalisation steps.

## Failure diagnosis

| Symptom | Interpretation and next evidence |
| --- | --- |
| DEV-STUB Permission denied on flows | Check source owner/group, `stat`, parent directory traversal, `id` and `getfacl`. New merged CSVs are `0640`; existing files need a separate owner/admin permissions change |
| `flow-rule-review: rc=-9` | Python reports SIGKILL, not a handled rule-generation exception. Check authorised system/cgroup OOM evidence, memory limits and external termination; OOM is a hypothesis until confirmed |
| `Wrote N Proposed rules1 rows` then failure | V1 save has completed, but legend, Action Plan and formatting still run. Earlier XLSX may exist; open a preserved copy and inspect every required tab |
| Workbook exists but incomplete | A module may warn and continue, CreateNew removes two exact titles, or case-colliding proposals may replace each other. Compare the worksheet catalogue and log |
| Empty Workloads or misleading counts | Inspect dupecheck schema/reasons and href grammar, scope columns, managed export and role filters |
| Empty or surprising matches | Check selected scope file, enabled-rule flags, separators, expanded groups, exact labels, election priorities and which date/zone files were selected |
| Catalogue differs from Flow-Rule Match | Catalogue uses raw flows; matching may use zone files and a later role filter; count meanings also differ |
| Long apparent pause | Wrappers deliberately sleep 60 seconds; API queries and repeated full-workbook loads/saves are also costly |
| FQDN lookup leaves a PCE IPList | If href discovery failed after create, cleanup was not armed. Use logs and exact temporary name to identify it; do not delete unrelated objects |

Streaming defers large flow tabs until after proposal processing, reducing intermediate workbook load costs. It does not eliminate all memory pressure: source sheets are loaded normally, aggregation keeps dictionaries, formatting revisits sheets, and final enrichment/IP summary functions reopen the full workbook. Excel limits are not automatically split into multiple sheets; oversized datasets require a separately designed workflow.

## Completion evidence

Check command status, all child statuses and warnings, final `[SUCCESS]` path, workbook readability, expected sheet names AND schemas, input/output row counts, proposal placements and sample selectors. Summary end/duration describes the initial workbook phase, not necessarily the whole operation. Keep logs and original exports for reproducibility. Do not infer production readiness from a generated file alone.
