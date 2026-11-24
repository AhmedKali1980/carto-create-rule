# Policy proposal strategies

Source: [propose_rule_for_scope.py](../../modules/propose_rule_for_scope.py), `build_intra_app_proposed_rules`, `build_ingress_proposed_rules`, their V1 variants and `main`.

## Shared pipeline

Matching rows are the input, after the anchor-role filter. Proposal generation is not restricted to `Action=Create`: already covered business traffic can also contribute. Bouquet traffic is excluded by the directional builders. Some paths require nonempty anchor app/env/role, a recognised protocol and a strictly positive port. Protocol-only ICMP/IGMP records consequently do not produce all of the same proposal families as TCP/UDP.

Resolve each strategy independently: `allow`, `finegrained`, `blacklist`; a direction without an explicit strategy is left at `none` by the module. The root CLI accepts only the three active choices; omit a flag to avoid generating that direction.

Blacklist CLI values name one or more `carto.conf` lists. Direction-specific arguments take precedence. The legacy shared argument is permitted only when exactly one direction uses blacklist. Parse and merge TCP/UDP intervals within 1–65535; compute their complement for default rules. A blacklist recommendation is still an allow-style policy proposal: it covers the non-blacklisted service ranges and creates explicitly labelled exceptions for observed blacklisted ports. It is not a direct deny-rule installation.

`PORTS_ADMIN`, `PORTS_TO_ERADICATE` and `PORTS_TO_CONTROL` also define services that must remain isolated in finegrained aggregation and contribute comments describing list membership. This use is independent of which lists were selected as a blacklist.

## Intra-application

Use rows whose UI direction is `intra-app` and whose peer labels share the anchor app/env. Gather scope roles from managed workloads with proposal fallback, then apply the role filter. Place recommendations in `<app>-<env>-RS`.

| Strategy | Construction |
| --- | --- |
| allow | One open recommendation per scope with the collected source/destination roles and All Services |
| finegrained | Aggregate observed directed role pairs and services; configured sensitive TCP/UDP ports stay in separate rows |
| blacklist | Default scope-role coverage with the complement of selected port intervals, plus observed blacklisted-service exceptions per role pair |

The stable proposal writer uses sections such as `Intrascope` and `Intrascope Exceptions`. V1 normalises exception placement back to `Intrascope` and records `Blacklist Exception` in Comment. Default rows carry `Blacklist default rule` in V1. Role lists and observations are evidence for review, not proof that all cross-role combinations are required.

## Ingress

Anchor is the destination workload. IPList peers and label peers follow different paths.

| Peer | allow | finegrained | blacklist |
| --- | --- | --- | --- |
| IPList | Group IPLists by significant prefix and scope; target collected roles; All Services | Group by app/env/role/IPList-prefix/proto/port; then V1 may combine services for identical selectors | Default Any-to-scope-role complement rule, plus observed blacklisted ports grouped by role and prefix |
| Labels, V1 | Aggregate observed services per derived source selector and destination role | Same selector-level service aggregation; sensitive single ports stay separate in the final ingress grouping pass | Group non-blacklisted observations; put each observed blacklisted service in a separate exception row |

IPList ingress belongs in `intra-scope`; labels ingress in `Extrascope`, both within the anchor `<app>-<env>-RS`. Never combine ingress IPLists from different significant prefixes. The selector for a managed-family label peer contains app/env/role; other families contain app/env only. `loc` and `OS` are dropped deliberately. Labels ingress in V1 `allow` still lists observed services; it is not converted to All Services.

## Egress

Anchor is the source workload. V1 gives each egress IPList destination its own output row; roles and services are aggregated around that destination. Finegrained keeps configured sensitive services separate. Blacklist produces a scope default toward Any and observed blacklisted exceptions. The `allow` path retains historical IPList aggregation behaviour.

Labels egress depends on the destination app prefix:

| Destination family | Ruleset placement | Destination selector | Section |
| --- | --- | --- | --- |
| Prefix ends in M, or is APMA | `<peer_app>-<peer_env>-RS` | app/env/role; missing role displayed as `All Roles` | `Extrascope in other scope` |
| Other prefix, e.g. APA | `<anchor_app>-<anchor_env>-OUTBOUND2<PREFIX>-RS` | app/env, without role | `Unscopped in OUTBOUND2<PREFIX>` |

For label peers, V1 `allow` and `finegrained` aggregate observed services around destination and source scope. Finegrained isolates configured sensitive ports. Blacklist separates observed blacklisted-port exceptions from the other observed services; do not assume every label-peer branch constructs the same complement default as IPList branches.

## Zone defaults, annotations and output

With network-zone enabled, append ingress/egress defaults involving `ZNOT_<zone>` and scope roles for active strategies. They use All Services, section/comment `North South default rule`, and `East-West (Y/N)=N`. Managed North/South egress label candidates contribute additional recommendations only when they have no existing rule match.

V1 postprocessing groups compatible ingress finegrained rows; adds configured port-list comments; optionally marks selectors referenced by `BOUQUETS_` rulesets with `Remote (App label/iplist) used in Bouquets`; sorts annotated egress/ingress first, then remaining egress/ingress, then other directions, with stable selector tie-breaks. Red investigation highlighting takes priority over orange bouquet-reference highlighting; blacklist defaults are bold.

The stable and V1 writers have different schemas and grouping. The baseline also has case-colliding worksheet names: see [proposal worksheets](worksheets/13-proposed-rules-v1.md). Proposal exceptions are caught and logged, after which Action Plan may still be written. Review warnings, final worksheet schemas and counts; do not rely solely on exit code or a `Wrote ...` line. This pipeline does not automatically apply the recommended rules to PCE.
