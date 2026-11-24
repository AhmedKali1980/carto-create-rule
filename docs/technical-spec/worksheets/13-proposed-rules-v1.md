# Proposed rules1 — V1 strategy table

## Inputs and trigger

Source: `propose_rule_for_scope.main`, `build_intra_app_proposed_rules`, `build_ingress_proposed_rules_v1`, `build_egress_proposed_rules_v1`, `_group_pr1_ingress_finegrained_by_src_dst`, `append_excel_simple_table`. Created only when V1 rows are nonempty. It is retained by default CreateNew.

## Construction

1. Initialise optional North/South default rows. Rebuild intra-app rows using active strategy and role constraints. Normalise blacklist exception placement and write exception/default labels in Comment.
2. Build ingress IPList and label recommendations. Group IPLists by significant prefix; derive managed-family source selectors with role, other-family selectors without role; place labels in Extrascope.
3. Build egress IPList recommendations centred on one destination; aggregate source roles and services. Build label-peer recommendations with managed remote ruleset placement or local OUTBOUND2 family placement. Preserve configured sensitive services and blacklist exceptions as separate rows.
4. Group compatible ingress finegrained rows with identical selectors, section, ruleset and comment, unless they contain a configured single-port service.
5. Add port-list membership comments. If enabled, scan `BOUQUETS_` rulesets for referenced apps/IPLists, mark intersecting selectors as `Remote (App label/iplist) used in Bouquets` and sort those rows first.
6. Normalise counters: former row-count sum becomes `num_aggregated_rows`; internal true count becomes `sum_num_flows`, with row-count fallback if no true counter exists. Generated defaults do not represent observed traffic; some grouping paths use fallbacks rather than exact accounting.
7. Add `East-West (Y/N)` before Rule Section when zone mode is active; North/South defaults show N, ordinary rows default Y.
8. Write Direction, Strategy, Source, Destination, Services, both counters, optional zone flag, Rule Section, Comment, Ruleset. Red investigation highlighting overrides orange bouquet-reference marking; blacklist defaults are bold. Save, then log `Wrote N Proposed rules1 rows`.

## Interpretation and checks

The log occurs after this table save but before legend, Action Plan and final formatting. It does not prove overall success. Recommendations require policy review; their naming-derived placement is not verified by ruleset API lookup. Verify APMA/CSM/APA examples, role retention, OUTBOUND2 spelling, sensitive ports and both counter meanings.

Check the actual headers: this title can also contain the stable table due to the [case collision](README.md). No recommendations are automatically installed by this writer.
