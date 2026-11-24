# End-to-end execution

Source: [carto_ng_orchestrator.py](../../carto_ng_orchestrator.py), especially `main`, `run_step`, `build_final_excel`, `rename_final_excel`.

## 1. Parse arguments and initialise the run

1. The operator starts `python3 carto_ng_orchestrator.py` from the directory containing `carto.conf`. The script uses relative configuration and working-directory paths, even though module paths are derived from `__file__`.
2. `argparse` reads `--days` (required), scope labels (`app`, `env`, `role`, `loc`, `OS`), strategies, stubs, Excel streaming and investigation flags. Roles support a comma-separated inclusion list or whole-filter exclusion using `!` or `not:`; `--exclude-role` is the shell-safe exclusion alternative.
3. Email recipients initialise `MAIL_CONTEXT`. The mutually exclusive mode guard runs before reading configuration. In this baseline `CreateNew=True` by default, so supplying `--FlowRuleReview` also makes both modes true and aborts immediately. There is no CLI disable switch for `CreateNew`.
4. Load `carto.conf` using a simple line-oriented `KEY=VALUE` parser. Verify that `EXECUTABLE` exists and is executable and that `EXECUTABLE_CONFIG_FILE` exists. These checks also apply to a fully stubbed run.
5. Compute start as host-local today minus `days`, end as host-local today; only dates are passed to Workloader. A replay recomputes these dates, independently of the data's original extraction dates.
6. Create `EXPORT_ROOT/<timestamp>_<sanitised-app-env-role>/raw`, `derived`, `excel` and `log`. Configure Python logging and optional stdout/stderr capture through `tee`. A finalisation hook sends notification when requested.
7. Child environments start with process variables, then `.env` key/value entries, then explicit Workloader and retry values derived from `carto.conf`. Python code that reads `carto.conf` directly does not automatically receive equivalent overrides from `.env`.

## 2. Extract or replay the source datasets

The order is intentional. Every stub replaces one export, not the whole pipeline.

| Order | Action | Main dependency / artifact |
| --- | --- | --- |
| 1 | Export labels | `raw/export_label.csv`; requires `href,key,value` |
| 2 | Resolve scope labels to hrefs | `derived/include_labels_semicolon.csv`; role is deliberately omitted from traffic extraction filters |
| 3 | Export outgoing traffic | `raw/flows_out_<start>_<end>.csv` |
| 4 | Export label groups | `raw/export_labelgroup.csv` |
| 5 | Export IPLists | `raw/export_iplists.csv` |
| 6 | Build configured Qualys source exclusions and export incoming traffic | labels/IPLists from `HREF_LABEL_QUALYS` and `HREF_IPLISTS_QUALYS`; `raw/flows_in_<start>_<end>.csv` |
| 7 | Export managed workloads | `raw/export_wkld.m.csv` |
| 8 | Resolve managed scope hrefs; export processes | bulk export first; fall back to single export; finally write an empty header if unavailable |
| 9 | Export unmanaged workloads | `raw/export_wkld.u.csv` |
| 10 | Export rulesets and collect enabled ruleset hrefs | `raw/export_ruleset.csv`, `derived/list_href.ruleset.enabled.csv` |
| 11 | Export rules of enabled rulesets | `raw/export_rules.enabled.csv` |
| 12 | Optional network-zone preprocessing | exact zone and `ZNOT_<zone>` must exist; create `derived/flows_out.zone.csv` and `flows_in.zone.csv` |
| 13 | Export duplicate-workload analysis | `raw/export_dupecheck.csv` |

The traffic wrappers run two queries per direction: one excludes allowed traffic; the other excludes potentially-blocked, blocked and unknown traffic. They merge both CSVs, keeping one header. They do not deduplicate data rows. Query semantics are delegated to Workloader. The common helper retries with backoff/jitter, applies a per-attempt timeout when available, verifies output unless explicitly skipped, and pauses 60 seconds after attempts. The merge writes through a temporary file, sets `0640`, then renames it to the final CSV.

## 3. Reconcile workloads and build the initial workbook

1. Detect dupecheck schema: already-final rows, exploded `href_managed` rows, or raw `reason` rows. Raw reasons are split, workload hrefs extracted and duplicate pairs deduplicated.
2. Enrich managed attributes and normalise hrefs. Determine managed scope from workload labels. Final-like stubs can supply a fallback scope when managed scope is empty.
3. Filter duplicate rows to managed scope unless debugging disables this step. The filter is applied only when the scope href set is nonempty.
4. Add managed workloads absent from duplicate matches as `Not Active in CMDB`. Add unmanaged workloads sharing a role/app/env/loc tuple with a duplicate row as `Missing Agent`. These are implemented heuristics, not fresh CMDB or agent health probes.
5. Write `derived/export_dupecheck.final.csv`. Resolve label-group inclusions for the effective scope and normalise process export column aliases.
6. `build_final_excel` creates Summary, Workloads, the optional unmanaged-app rule audit, Processes when nonempty, and normal Flow-in/out sheets when not streaming. Its execution-end timestamp is captured here, before subsequent analysis and enrichment.

## 4. Append analysis and proposed policy

1. Run `export_services.py` when enabled or when a main analysis mode is active. It uses raw dated flows, even if a zone filter exists.
2. For `CreateNew` or `FlowRuleReview`, run `flows_to_rules.py`: create/reuse `derived/scope.params.txt`, determine applicable rules and write Scope Applicable Rules and Ruleset Effectiveness.
3. Run `propose_rule_for_scope.py`: select flow pair, aggregate records, classify matches, apply anchor-role filter, write the flow-match CSV and worksheet, then construct strategy proposal tables and Action Plan.
4. With `CreateNew`, remove exact worksheet titles `Proposed Rules` and `Action Plan`. The implementation still computes proposals first; the lower-case proposal/V1 naming behaviour is described in the [worksheet catalogue](worksheets/README.md).
5. Optional legacy CreateRules/RecertifyRules call separate modules that are absent from this checkout. FlowRuleHits calls the scope applicability wrapper again; it is not a separate verified hit-analysis engine here.

## 5. Complete the deliverable

1. Build To investigate directly from normal flow sheets, or rebuild the workbook with streamed raw CSV flow sheets and build the investigation table while streaming.
2. Unless skipped, find unknown outgoing IPv4 addresses, create and provision a temporary PCE IPList, export its href, query destination traffic for FQDNs, update the investigation sheet, and attempt IPList deletion in `finally`. This phase changes PCE state. Cleanup only starts after a usable href file exists.
3. Derive Egress IP to investigate and Ingress IP to investigate from To investigate. These summary sheets use one row per first-seen IPv4 address.
4. Print duration summaries, rename the workbook to `carto_<app>-<env>_<timestamp>.xlsx` (numeric collision suffix if needed) and mark email context SUCCESS. Final file names omit role; the run directory retains it.
5. At exit, optional notification sends the execution summary and available log content. A successful initial XLSX or an intermediate proposal count is not evidence that this final phase completed.

## Failure boundaries

`run_step` records the child exit status and elapsed time; it imposes no Python subprocess timeout itself. Many export failures are logged and tolerated; missing files may become empty datasets. Scope-analysis, flow-review and streaming failures explicitly return 2 from the orchestrator. Other modules catch and warn about workbook errors; a zero child exit code can therefore coexist with a missing worksheet. Validate final workbook contents, not just the process return code.
