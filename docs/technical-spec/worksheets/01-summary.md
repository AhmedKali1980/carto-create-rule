# Summary

## Inputs and trigger

Created first by `carto_ng_orchestrator.build_final_excel`. Inputs are CLI scope, calculated start/end dates, execution start, raw-file paths, measured `DUR` values, enriched workload counts and scope label-group inclusions. It exists even when most tables are empty.

## Construction

1. Write title and key/value rows: scope, time window, execution start, execution end placeholder and total duration placeholder. Merge the value region for readability.
2. Section 1 lists ten raw exports: labels, groups, managed workloads, processes, unmanaged workloads, rulesets, enabled rules, dupecheck and both traffic directions. For each existing file, read its CSV to count data records, get size in bytes, and retrieve the associated export-stage duration. Missing files display zero rows/bytes. IPList export is not in this list.
3. Section 2 gathers distinct scope label values from managed workloads, ordered role/app/env/loc/OS. Find groups containing each value via direct or fully expanded members, then follow `member_label_groups` upward using a visited set. Display group names; the computed ancestry level is not printed in this summary table.
4. Section 3 writes managed-scope total, duplicate-row count, unmanaged-only Missing Agent count and managed-only Not Active in CMDB count from `enrich_workloads`.
5. Apply coloured headers, borders and widths. Fill execution end and duration before leaving the initial workbook builder. Later presentation/streaming passes can alter merges and styling.

## Interpretation and checks

Duplicate count is the number of enriched duplicate rows, not necessarily unique managed hosts. Zero exported rows may mean missing/failed data, not a confirmed empty PCE dataset. Scope-wide groups may include ancestor groups, whereas matching's group loader relies on direct/expanded member fields.

Execution end and duration precede service analysis, matching, proposals, streaming and PCE FQDN enrichment. They must not be presented as the full run completion time. Compare listed raw-file counts with the input dataset and the final success/log path.
