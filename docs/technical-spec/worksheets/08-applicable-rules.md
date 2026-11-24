# Scope Applicable Rules

## Inputs and trigger

Source: `flows_to_rules.main`, `scope_rules_applicability.get_applicable_rules`, `append_scope_rules_sheet`. Called before detailed flow review in CreateNew/FlowRuleReview. Inputs are per-run scope.params, managed workloads, expanded label groups and enabled-rule export. The writer creates a header even when no rule is applicable.

## Construction

1. Create or reuse `derived/scope.params.txt`. Resolve app/env target and gather available workload label values under selected scope.
2. Load direct/expanded group members indexed by dimension/group name. Load only export rows with a truthy `rule_enabled` flag.
3. Try bouquet semantics for empty-scope rules (complete source OR destination block with nontrivial labels and groups, all required intersections and no intersecting exclusions).
4. Otherwise accept business rules with exact target app/env ruleset scope OR source labels containing target values. Classify as in-scope or other-scope according to the scope content.
5. Replace the worksheet and prepend `Rule Category`. Write ruleset metadata, rule type/services and source/destination all-workloads, labels, label groups and IPLists. Exclusions participate in decisions but are not all displayed in this reduced sheet schema.
6. Freeze A2, filter, style the header, fit widths and save together with Ruleset Effectiveness.

## Interpretation and checks

This is a candidate-rule table, not a hit report. The selection is independent of the ruleset's name prefix; ruleset-name filtering flags accepted by the wrapper are ignored. `BOUQUETS_` naming is not required for the bouquet category here.

Check a rule whose scope is exactly app/env, a source-label extension and an empty-scope label/group bouquet. Match labels with exact casing and inspect all raw exclusions when a result appears surprising. The wrapper can exit zero after a warned append failure, so verify the sheet itself.
