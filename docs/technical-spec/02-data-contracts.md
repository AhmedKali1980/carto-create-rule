# Data and configuration contracts

Sources: `carto_ng_orchestrator.load_csv`, `load_conf`, `load_env_file`; `modules/common_io.py`; loaders in `scope_rules_applicability` and `propose_rule_for_scope`.

## Dataset interfaces

| Dataset under raw/ | Fields consumed by the pipeline | Downstream use |
| --- | --- | --- |
| `export_label.csv` | `href,key,value` | Map scope label values to API hrefs |
| `export_labelgroup.csv` | `name,key,member_labels,member_label_groups,fully_expanded_members` | Summary ancestry; matching uses direct/expanded members |
| `export_iplists.csv` | `name,href,include` | Zone lookup, eligible network index, temporary IPList href resolution |
| `export_wkld.m.csv` | `href,hostname,role,app,env,loc,OS,interfaces,managed,enforcement` | Scope, managed enrichment, roles and workbook audit |
| `export_wkld.u.csv` | `href,hostname,name,role,app,env,loc,OS,interfaces` | Duplicate enrichment and missing-agent heuristic |
| `export_processes.csv` | `hostname,process_path,service_name,port,proto,role,app,env,loc,OS,href` | Processes sheet; aliases supported by the orchestrator |
| `export_ruleset.csv` | `href,enabled` | Select enabled rulesets for export |
| `export_rules.enabled.csv` | `rule_href,rule_enabled,rule_description,ruleset_name,ruleset_scope,ruleset_enabled,rule_type,services` plus `src_`/`dst_` selectors | Applicability, matching, unmanaged-label audit, bouquet annotations |
| `export_dupecheck.csv` | raw: `href,reason` plus unmanaged attributes; or exploded/final managed/unmanaged columns | Workloads reconciliation |
| `flows_out_<start>_<end>.csv` and incoming equivalent | Source/Destination IP, IPList, Application, Environment, Role, Location, OS, Name, Hostname; Protocol, Port, Num Flows, Transmission, First/Last Detected | All traffic-based worksheets |

Rule selector fields include `src_all_workloads`, `dst_all_workloads`, labels, label exclusions, label groups, group exclusions and IPLists. The scope loader supports `consumer_`/`provider_` aliases. The unmanaged-label audit and bouquet reference scanner expect particular raw `src_`/`dst_` names; an alias accepted by one consumer may not be accepted everywhere.

Headers are usually selected case-insensitively, but downstream flow formatting uses specific display names and some loaders read exact keys. Preserve the exported schema and test every consumer when changing Workloader versions. The code also uses substring matching for some flow fields: ambiguous extra headers can change which field is selected.

## Encodings and delimiters

The orchestrator, scope loader and service catalogue generally read UTF-8 comma-delimited CSVs. Proposal and streaming readers are more tolerant (including BOM and delimiter detection). Do not conclude that semicolon CSV or a BOM is supported end to end because one module accepts it.

Nested values use their own separators: semicolons for href lists, label-group members, IPList tokens and exported label expressions; `|` between compact `key=value` selectors; newlines in redundant-rule display cells. The frozen scope parser accepts `:` or `=` within tokens and commas/semicolons between tokens. The proposal wrapper additionally normalises `|`. Naming values containing these separators are not escaped consistently.

Workload hrefs are normalised from full URLs to `/orgs/.../workloads/...`. Duplicate reason extraction expects hexadecimal/hyphen workload identifiers. A changed reason grammar or href shape can silently remove matches.

## Artifact contracts

Keep raw input, derived outputs and the workbook from the same run together. Significant derived files include include/exclude href lists, `list_href.managed.csv`, `list_href.ruleset.enabled.csv`, `export_dupecheck.final.csv`, `scope.params.txt`, `services_catalog.csv`, `flow_rule_match_<start>_<end>.csv` and zone CSVs. A root-level `scope.params.txt` is not the same as the per-run `derived/scope.params.txt` consumed by applicability.

`num_flows` in the matching table counts CSV records aggregated, not the sum of raw `Num Flows`. Internally `num_flows_true` tracks the latter. V1 proposals attempt to expose both via `num_aggregated_rows` and `sum_num_flows`; some generated/default/grouped paths use fallbacks, so these columns are not universal accounting totals. Rows seen from both extraction directions can count more than once.

## Configuration actually consumed

| Configuration | Consumer and effect |
| --- | --- |
| `EXECUTABLE`, `EXECUTABLE_CONFIG_FILE`, `PCE_NAME` | Orchestrator preflight and wrapper environment (`CFG` for the YAML path) |
| `EXPORT_ROOT`, `DATE_FMT` | Run directory location and timestamp |
| `RETRY_BASE_SLEEP`, `RETRY_BACKOFF_FACTOR`, `RETRY_MAX_SLEEP`, `RETRY_JITTER_PCT`, `TIMEOUT_SEC`, `MAX_ATTEMPTS` | Common wrapper retry/timeout controls; root retry limit uses `MAX_ATTEMPTS`, not `RETRY_MAX_ATTEMPTS` |
| `HREF_LABEL_QUALYS`, `HREF_IPLISTS_QUALYS` | Exclude sources only in incoming traffic extraction |
| `IPLIST_ALLOWED_PREFIXES`, `IPLIST_NAME_PRIORITY` | Election; separate copies in normal Excel, streaming Excel and proposal code |
| `PORTS_TO_CONTROL`, `PORTS_TO_ERADICATE`, `PORTS_ADMIN`, `ALLOWED_PORTS` | Catalogue classification, finegrained service isolation, proposal comments and named blacklist sources |
| `AVOID_LABEL_PAIRS` | App values whose peer labels should be replaced by IPList/IP selectors when enabled |
| `ENABLE_SERVICES_CATALOG` | Catalogue hook; main analysis modes also force this hook |
| `SMTP_*` | Optional notification transport; never store passwords in handover documents |

Port lists use `TCP/22;UDP/53;TCP/1000-1010;ICMP` syntax. Blacklist CLI arguments identify configuration list names, separated by comma/semicolon, rather than directly supplying those port expressions.

The root line parser does not remove inline comments or surrounding quotes. Other readers (notably proposal port-list parsing) are more permissive. Keep values unquoted and place comments on separate lines unless the specific consumer documents otherwise.

## Historical keys and misleading switches

The root config contains `ENABLE_SCOPE_RULES`, `ENABLE_BLOCKED_DIFF`, `ENABLE_UNKNOWN_IPS`, `SCOPE_RULES_SHEET`, `BLOCKED_DIFF_SHEET`, `UNKNOWN_IPS_SHEET`, `SERVICES_CATALOG_SHEET` and `BOUQUET_*` settings. Current root analysis does not use them to create or rename those advertised worksheets or tune bouquet semantics. `TOTAL_STEPS` is not an execution scheduler. Confirm key reads before using these entries as operational controls.

`--dev-stub-dupecheck-final` is parsed but not used. Several `store_true` arguments already default to true (CreateNew, elected IPList column, unmanaged-app audit, To investigate, avoid-label pairs); they have no corresponding negative switch. The comment claiming avoidance is disabled by default does not describe the orchestrator's actual default. `--no-mark-potential-core-service` does disable the bouquet-reference annotation.

The optional FlowRuleHits path also has argument drift: the orchestrator can pass `--filter-direction`, `--filter-proto`, `--filter-port`, `--prefer-raw`, `--limit-flows` or debug flags not accepted by the current scope wrapper. This can produce an argparse failure rather than hit analysis. Accepted legacy ruleset-name flags are ignored; do not rely on them to restrict policy.
