# Carto NG technical specification

Engineering handover • 24 November 2026 • source baseline `30733ec`.

This specification describes the implementation in this checkout, not an idealised workflow or a verified production deployment. It covers the cartography CLI, all workbook worksheet families, policy decisions, and the adjacent DNA automation. The organisation-specific meanings of application families must be confirmed by the policy owner; the code's decisions are documented explicitly.

## Reading routes

| Need | Read |
| --- | --- |
| Understand a complete run | [End-to-end execution](01-end-to-end.md) |
| Identify inputs, outputs and configuration | [Data contracts](02-data-contracts.md) |
| Understand which policy applies and how flows match | [Scope and matching](03-scope-and-matching.md) |
| Understand generated policy proposals | [Proposal strategies](04-proposal-strategies.md) |
| Assess a naming change | [Convention dependency register](05-convention-register.md) |
| Explain an Excel worksheet | [Worksheet catalogue](worksheets/README.md) |
| Run, replay or diagnose a cartography | [Operations](06-operations.md) |
| Maintain the implementation after handover | [Maintenance and validation](07-maintenance.md) |
| Understand the separate DNA automation | [Adjacent components](08-adjacent-components.md) |

## Scope and evidence

The source baseline includes the group-read correction for traffic CSVs. It has not been refreshed from GitHub for this documentation task. The specification is source-traced; synthetic, fully stubbed normal, streaming and network-zone executions are used to verify representative workbook behaviour. No production exports, credentials or live PCE operations are required for these checks. Production scale, actual Workloader compatibility and the business suitability of recommendations remain separate validation activities.

Observed limitations are intentionally retained in this specification: missing shell wrappers, conflicting mode defaults, worksheet case collisions, metadata that is not a true hit metric, and output that can be partially written before an error. They are not silently corrected by documentation work.

## Deliverables and regeneration

The Markdown chapters are the source of truth for the Word dossier. Each worksheet has a separate short construction guide. [The source map](source-map.md) links functions and their baseline line numbers.

Build the dossier from the repository root:

```bash
.venv/bin/python docs/build_technical_spec.py
.venv/bin/python docs/check_technical_spec.py
.venv/bin/python docs/validate_technical_spec_workflow.py
```

The generator requires `python-docx` (validated with 1.2.0). It does not run the application. Output: `docs/technical-spec/Carto_NG_Technical_Specification.docx`. The Word file contains a clickable contents section, native heading styles, internal bookmarks, source hyperlinks and page numbers. Markdown links to other included chapters become internal Word links. The contents section is prebuilt and works without updating Word fields.

Changes to these files do not change application logic. No deployment, push or publication is implied by document generation.
