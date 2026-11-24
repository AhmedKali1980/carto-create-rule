# Proposed rules — stable strategy table

## Inputs and trigger

Logical writer title is `PROPOSED_RULES_SHEET='Proposed rules'` in `propose_rule_for_scope`. Built after matching if one or more enabled strategies produce rows. Schema: Direction, Strategy, Source, Destination, Services, sum_num_flows, Rule Section, Ruleset.

## Construction

1. Use classified, role-filtered internal matching rows (including zone-specific proposal candidates where applicable).
2. Invoke the intra-app, ingress and egress base builders for active strategies. Resolve directional blacklist source lists before each builder. Skip the corresponding direction if strategy is none.
3. Intra-app collects roles and role/service pairs. Ingress splits IPList peers by significant prefix and adds label-based Extrascope recommendations. Base egress handles IPList peers; V1 later adds the richer labels-egress behaviour.
4. Apply allow/finegrained/blacklist semantics described in [strategies](../04-proposal-strategies.md), including default complements and observed exceptions. Add enabled-direction North/South complement defaults in network-zone mode.
5. Sort intra-app, ingress, egress then ruleset, section, destination, source and service. If nonempty, replace the logical title using `append_excel_simple_table` with wrapped Services and save.

## Physical title and interpretation

Because the compatibility analysis sheet already occupies `Proposed Rules`, the lower-case stable title can become `Proposed rules1` automatically. The explicit V1 writer may subsequently remove and replace it. The stable table therefore cannot be assumed to survive as a separate final tab in the default workflow.

Its `sum_num_flows` reflects builder aggregation of matching-row counts and generated defaults, not universally the raw observation count. Confirm the eight-column schema before reading it as stable output. A physical tab named Proposed rules1 without the V1 Comment and dual-counter fields can be this table after V1 produced no output or failed.
