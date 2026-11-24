# Ruleset Effectiveness

## Inputs and trigger

Written by `scope_rules_applicability.append_scope_rules_sheet` in the same save as Scope Applicable Rules. Its data is assembled by `get_applicable_rules` while iterating applicable rules. It is created with a header even if the result is empty.

## Construction

1. For every applicable rule, group by `ruleset_name`. Initial metadata is taken from the first applicable rule with that name: scope, enabled status and `applies_to_scope=Y`.
2. Increment `rules_enabled_count` and `rules_applicable_count` once per applicable rule.
3. Initialise `covered_flows_count=0`, `rules_with_hits_count=0` and `top_services=''`. This implementation does not later populate them from the flow-matching pass.
4. Sort rows by ruleset name. Replace the worksheet and write the nine fields in fixed order, then apply frozen/filter header, borders and width limits.

## Interpretation and checks

Despite its title, this baseline is an applicability summary. Zero coverage/hit counters are placeholders, not proof that a ruleset is unused. `rules_enabled_count` is counted over applicable loaded rules, not over all enabled rules in the PCE ruleset. Both rule counters are therefore equal for the same group in this implementation.

Only rulesets with applicable rules appear. Grouping by name can collapse distinct objects if the export contains duplicate names; it is not grouped by immutable href. Metadata from later rows does not replace initial metadata.

Compare rule counts to Scope Applicable Rules, not to Workloader/PCE hit statistics. Any future implementation of effectiveness metrics must define observation window, unique flow accounting and multiple-match attribution before replacing these placeholders.
