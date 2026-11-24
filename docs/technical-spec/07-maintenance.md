# Maintenance and handover validation

## Ownership map

| Area | Primary implementation |
| --- | --- |
| Command sequencing, workload joins, initial workbook, investigations | `carto_ng_orchestrator.py` |
| API invocation, retry, traffic split/merge and CSV permissions | `bin/workloader_common.sh`, `workloader_traffic_in.sh`, `workloader_traffic_out.sh` |
| Scope applicability and label-group expansion | `modules/scope_rules_applicability.py` |
| Scope-file creation and compatibility wrapper | `modules/flows_to_rules.py` |
| Aggregation, matching, all proposal families and styling | `modules/propose_rule_for_scope.py` |
| Service classification/catalogue | `modules/export_services.py` |
| Streamed Excel rebuild and duplicated election/investigation rules | `modules/excel_stream_update.py` |
| Root notification | `modules/email_utils.py` |
| Separate FQDN/IPList lifecycle | `iplist_dna_automanage/` |

The root `email_utils.py` imports absent `config` and `users` modules. It is not the notification module imported by the cartography entry point. Avoid treating it as the authoritative mail path.

## Preserve these contracts across changes

Treat dataset schemas, fixed worksheet titles, proposal section strings, label dimensions and naming predicates as interfaces. Search every duplicated election/investigation implementation before changing a prefix. Never rename a worksheet by changing only its writer: downstream lookup, CreateNew deletion, streaming insertion, Summary formatting and FQDN updates depend on exact titles.

Applicability and actual flow matching are distinct decisions. A change to a family prefix must be assessed for selector specificity AND ruleset placement. Changing aggregation can preserve row counts while changing the policy's allowed role/service combinations; compare actual selector sets.

## Regression scenarios for future code changes

| Area | Minimum meaningful cases |
| --- | --- |
| Family naming | APMA, APM, CSM, APA, unknown suffix-M family; empty prefix; role missing |
| Peer identity | Multiple allowed IPLists with different priorities; no allowed candidate; raw IP; labels; deleted-workload marker; avoid-label resolver match/miss |
| Scope | Exact app/env; extra scope key; source-label inclusion; bouquet complete/incomplete; exclusions; missing group; stale scope file |
| Role filtering | Single, multiple, whole-list exclusion, absent roles; compare raw tabs versus matching and workload-based bouquet values |
| Services | TCP/UDP points/ranges, numeric protocol aliases, ICMP/IGMP; blacklist direction overrides and ambiguous shared source; isolated sensitive ports |
| Zone | Both endpoints in; one out; invalid IP; missing complement; managed-family remote peer; North/South row absent from match sheet but available for proposals |
| Workbook | Normal/streaming, empty datasets, missing Processes, proposal title collision, CreateNew deletion, To investigate dedup, IPv4-only summaries and /21 |
| Operational failure | Copy denied; missing wrapper; nonzero child; SIGKILL after intermediate save; failed IPList href discovery; notification failure |

Keep synthetic fixtures small enough for deterministic checking. Large production input is needed separately to qualify memory and runtime. Never use real PCE mutation or SMTP as a smoke test.

## Evidence collected for this specification

Reproduce the checks with `.venv/bin/python docs/validate_technical_spec_workflow.py`. The harness supplies every export, skips PCE enrichment, omits email and deletes its temporary artifacts.

Three fully stubbed orchestrator runs (normal, streaming, network-zone streaming) used synthetic APMA workloads, two roles, TCP services, IPList peers and an enabled sample rule. They exited zero, opened successfully and produced the same 14 final worksheet titles with active strategies under default CreateNew. These runs validate representative construction paths, not every policy branch or production scale.

A direct writer probe verified that `Proposed Rules` followed by `Proposed rules` triggers openpyxl's case-insensitive uniqueness suffix; writing explicit `Proposed rules1` then replaces the suffixed table. Family probes verified APMA/APM/CSM as managed and APA/CSU as other families. A synthetic ingress selector retained app/env/role for APMA.

The documentation checker validates the chapter manifest, local links, source references, worksheet coverage, and the Word ZIP/XML structure, contents links and bookmarks. Word rendering is checked separately using headless office conversion when available. No live PCE/SMTP validation or production-output equivalence is claimed.

## Known behaviour requiring engineering review

The default `CreateNew` conflicts with explicit FlowRuleReview. Literal scope-file roles do not implement the CLI's full role grammar. Proposal table names collide by case. Effectiveness hit metrics remain placeholders. Module warnings can coexist with exit zero. Workloads Inside Network Zone uses managed interfaces even for unmanaged-only rows. The final metadata duration is recorded early. Incoming IP summaries use IPv4 /21 regardless of source topology. These are documented baseline behaviours, not fixes delivered by this specification.

## Updating the dossier

Update the targeted Markdown first, then regenerate `source-map.md` and the Word file with `docs/build_technical_spec.py`. Run `docs/check_technical_spec.py`; inspect the rendered Word/PDF for heading hierarchy, tables, source links and page flow. Source-map lines refer to the documented baseline and can drift; function names remain the primary navigation key. Commit documentation and generated dossier together if the repository's artifact policy permits. No application source change is needed to rebuild this specification.
