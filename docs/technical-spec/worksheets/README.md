# Excel worksheet catalogue

Every worksheet writer in the available cartography source is represented below. Titles are interface contracts: downstream code looks them up by name. A missing tab can be an intended mode decision, an empty-input condition or a partial failure.

| Logical worksheet | Construction guide | Presence |
| --- | --- | --- |
| Summary | [Summary](01-summary.md) | Initial workbook |
| Workloads | [Workloads](02-workloads.md) | Initial workbook, including empty table |
| Rules with umgd app labels | [Unmanaged-app rule audit](03-unmanaged-app-rules.md) | Enabled by default; errors can skip it |
| Processes | [Processes](04-processes.md) | Only when process rows are nonempty |
| Flow-out | [Outgoing flows](05-flow-out.md) | Nonempty in normal mode; rebuilt from raw CSV in streaming mode |
| Flow-in | [Incoming flows](06-flow-in.md) | Same mode distinction |
| Service Catalogue | [Services](07-services.md) | Hook enabled/forced by analysis mode; absent if both raw inputs have no data |
| Scope Applicable Rules | [Applicable rules](08-applicable-rules.md) | Scope analysis succeeds in appending |
| Ruleset Effectiveness | [Effectiveness](09-effectiveness.md) | Written with applicable rules |
| Flow-Rule Match | [Matching](10-flow-rule-match.md) | Flow review module; retained by default CreateNew |
| Proposed Rules | [Compatibility analysis table](11-proposed-rules-compatibility.md) | Intermediate; exact title removed by CreateNew |
| Proposed rules | [Stable strategy table](12-proposed-rules-stable.md) | Logical writer title; case collision affects physical name |
| Proposed rules1 | [V1 strategy table](13-proposed-rules-v1.md) | Created when V1 recommendations exist; retained by CreateNew |
| Action Plan | [Actions](14-action-plan.md) | Intermediate; removed by CreateNew |
| To investigate | [Investigation details](15-to-investigate.md) | Enabled by default; may be empty |
| Egress IP to investigate | [Outgoing IP summary](16-egress-investigation.md) | Created from a valid To investigate header, even if empty |
| Ingress IP to investigate | [Incoming IP summary](17-ingress-investigation.md) | Created together with outgoing IP summary |

## Critical proposal-title interaction

The code intentionally writes three logical tables with similar names: matching compatibility table `Proposed Rules`, stable recommendation table `Proposed rules`, and V1 recommendation table `Proposed rules1`. Excel/openpyxl enforces case-insensitive title uniqueness, while the code's existing-sheet checks are case-sensitive.

Observed sequence: writing the compatibility table then the stable table produces physical title `Proposed rules1` for the latter. Writing V1 explicitly to that title removes and replaces the stable table. Default CreateNew then deletes `Proposed Rules` and `Action Plan`, leaving V1 if recommendations were generated. If V1 is empty/skipped after stable output, the same physical `Proposed rules1` title can contain the stable schema instead. Inspect headers, not just titles.

Normal, streaming and network-zone synthetic runs with active strategies all produced these 14 final tabs: Summary, Workloads, Rules with umgd app labels, Processes, Flow-out, Flow-in, Service Catalogue, Scope Applicable Rules, Ruleset Effectiveness, Flow-Rule Match, Proposed rules1, To investigate, Egress IP to investigate, Ingress IP to investigate. This is an observed fixture result, not a guarantee of 14 tabs for every run.

Historical config names `SCOPE_RULES`, `BLOCKED_DIFF`, `UNKNOWN_IPS` are not additional implemented worksheets here. Legacy absent modules may have produced other deliverables in a different deployment; those require their source and sample workbook for documentation.
