# Scope selection and flow-to-rule matching

Sources: [scope_rules_applicability.py](../../modules/scope_rules_applicability.py), [propose_rule_for_scope.py](../../modules/propose_rule_for_scope.py), [flows_to_rules.py](../../modules/flows_to_rules.py).

## Scope is applied at different stages

Traffic export deliberately excludes the role filter from its include-label selection, preserving traffic for the selected non-role scope. Managed-workload selection uses role inclusion/exclusion. The proposal module later filters matching and action rows by `anchor_role`; intra-app rows must also satisfy the filter on a nonempty peer role. This explains why raw flow sheets and the catalogue can show more roles than the final rule proposals.

`flows_to_rules._ensure_selected_scope_file` reuses an existing nonempty `derived/scope.params.txt`. Otherwise it writes explicit app/env/role arguments and falls back to parsing the intermediate Excel filename or run folder. Parsing splits app/env/role from the right to tolerate UUID-like hyphens inside app. A stale scope file overrides new arguments; delimiters in role/environment can make filename fallback ambiguous.

The scope module reads each selected value as a literal set item. It does not implement the orchestrator's comma-list or exclusion syntax for roles. Its workload-derived label sets therefore need special validation for a multi-role or exclusion run. Case handling is not uniform: managed reconciliation often compares lower-case values, while policy scope membership uses exact trimmed values.

## Applicable-rule decision

Only rows whose `rule_enabled` is true/1/yes/y are loaded. The loader carries `ruleset_enabled` as metadata; the ordinary live pipeline already limited export to enabled rulesets. A hand-built stub must preserve that invariant itself.

The target for business rules consists only of selected app and env, not role/loc/OS.

1. With an empty ruleset scope, try bouquet applicability first. Either the complete source block or complete destination block must be valid.
2. A bouquet block must contain at least one recognised label constraint AND at least one label group. Every constrained label key must intersect the workload-derived scope values. Every listed group must touch the scope. Any intersecting label/group exclusion invalidates that block. The other block is checked independently; the implementation uses `src_ok or dst_ok`.
3. Otherwise business applicability requires either exact equality of ruleset scope keys/values with target app/env, OR source labels containing each target app/env value.
4. Applicable business rules with empty scope or scope containing the target app/env become `Business Rule in Scope`; otherwise `Business Rule in other Scope`.
5. Non-applicable rules produce internal unmatched rows, not a separate workbook tab. Applicable rules are summarised by ruleset name for the effectiveness table.

This is scope selection, not proof that a traffic record matches a service and both sides of a rule. Bouquet applicability does not inspect the `BOUQUETS_` name prefix; that prefix is used by a separate proposal annotation pass.

## Peer identity and aggregation

For each outgoing record the source is the anchor and destination the peer; incoming reverses those roles. The label keys are `app,env,role,loc,OS`. Protocol values are normalised and ports converted to integers.

Peer resolution normally prefers an elected IPList, then compact labels in label-grouping mode, then IP, hostname and name fallbacks. Avoid-label-pairs can override this: a configured peer app is replaced by a matching network IPList, otherwise its raw IP; peer labels are disabled for subsequent matching. The network resolver uses eligible lists, longest prefix first, and configured priority for equal networks.

Group by raw direction, five anchor labels, peer type/value, protocol and port. Same-app and same-env label peers are displayed as `intra-app`, but raw direction remains in the aggregation key and rule-side mapping. Thus incoming/outgoing observations are not globally deduplicated. Track row count, real Num Flows sum and first/last timestamps. Apply `min_flows` to row count.

## Match and classify each group

1. A peer name containing `deleted workload`, resolved as raw IP, forces `Deleted workload` and `No Action`.
2. Test every applicable rule: service protocol/port must match; then source and destination selector checks must both pass.
3. For each side, reject matching exclusions first. A true all-workloads selector requires a nonempty ruleset scope matching the side labels. Otherwise allow exact elected IPList membership, or combined labels and expanded groups (AND across keys, allowed values within a key).
4. Sort all matches by category: bouquet first, business in scope second, business in other scope third; then ruleset name and description. The first is primary; remaining matches populate multiline redundant-selector fields.
5. No match gives `No matching rule` / `Create`. One match gives the corresponding Info / `No Action`. Multiple matches give `Optimize` and redundant evidence.

`Optimize` means overlapping matches under this algorithm. It does not prove any existing policy rule can safely be deleted. Matching uses elected IPList names, not a full re-evaluation of every network membership in PCE.

## Network-zone mode

The requested IPList name and `ZNOT_<name>` must resolve exactly. Positive includes form networks; tag suffixes such as `#GEN1` are removed; negated tokens are ignored for zone membership. East-West records require both endpoint IPs inside the zone. The proposal module can additionally scan raw outgoing traffic for in-zone sources to out-of-zone managed-family label destinations. These North/South candidates are kept for proposals but omitted from Flow-Rule Match.

North/South defaults use the complement name and All Services for enabled ingress/egress strategies. The code checks existence of the complement; operators must verify that its actual contents represent the intended complement. The Summary, raw flow tabs, catalogue and Workloads scope are not all restricted to these East-West records.
