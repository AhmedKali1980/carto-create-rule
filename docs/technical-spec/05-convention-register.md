# Naming and business-convention dependency register

Source baseline: `30733ec`. This register describes technical dependencies. A convention can be migrated, but must not be renamed independently of its producers, consumers and regression fixtures. Do not infer the organisational meaning or ownership of a prefix from its technical treatment alone.

## Application families and ruleset placement

| Contract | Exact implemented decision | Change impact / location |
| --- | --- | --- |
| First underscore divides app family from identifier | `_app_prefix('APMA_example')` returns `APMA`; no underscore returns the entire value | Proposal placement and managed-family detection; proposal module `_app_prefix` |
| Managed-family predicate | Uppercase prefix ends with `M`, OR equals `APMA` | APM, CSM and APMA are treated as managed; APA and CSU are not; `_is_managed_app_prefix` |
| Managed-family ingress source | Include app/env/role when available | Removing APMA recognition broadens/changes generated selectors; `_source_selector_for_peer_labels` |
| Managed-family egress destination | Recommend rules in remote `<peer_app>-<peer_env>-RS`; include role | Can transfer apparent rule ownership to another scope; `build_egress_labels_proposed_rules_v1` |
| Other egress family | Recommend local `<app>-<env>-OUTBOUND2<PREFIX>-RS`; omit destination role | For APA the literal is **OUTBOUND2APA**, not OUTBOUN2APA; preserving the spelling is necessary for downstream conventions |
| Scope ruleset suffix | `<app>-<env>-RS` | Used across directional builders, zone defaults and reviews; not an API lookup proving that this ruleset exists |
| Placement text | `Intrascope`, `intra-scope`, `Extrascope`, `Extrascope in other scope`, `Unscopped in OUTBOUND2<PREFIX>`, `North South default rule` | These exact strings, including historical spelling/case, are also inputs to grouping and exception annotation |

Example: with anchor `APMA_ORDER/PRD/DB`, a destination `CSM_SERVICE/PRD/API` is treated as managed and targets the remote CSM ruleset. A destination `APA_SERVICE/PRD/API` targets the anchor's OUTBOUND2APA ruleset and omits API from its destination selector. These are synthetic identifiers; the organisation must validate that this family distinction remains correct.

The predicate is intentionally broader than an enumerated business taxonomy: any prefix ending in M is considered managed. A newly introduced unrelated family ending in M would inherit that behaviour. Renaming an APA-family app to APMA changes policy placement, selectors and North/South eligibility without changing traffic IPs.

## IPList election, grouping and investigation

| Contract | Decision / caveat | Consumers to review together |
| --- | --- | --- |
| `IPLIST_ALLOWED_PREFIXES` | Ordinary election narrows candidates only if at least one allowed candidate exists; otherwise keeps originals | Normal Excel local election, streaming `elect_iplist_from_tokens`, proposal election |
| `IPLIST_NAME_PRIORITY` | First matching prefix wins; otherwise lexical minimum; ties within one priority can depend on input order | Same three election implementations |
| Prefix matching | Case-sensitive `startswith`; optional trailing `*` only; no general glob language | Election helpers |
| Avoid-label network resolver | Strictly excludes ineligible names, longest network prefix wins; same-network candidates use priority | `build_avoid_iplist_network_index`, `make_iplist_resolver` |
| Significant ingress grouping prefixes | `CSD_`, `DNS_`, `SSD_`, `USR_`, `U_`, `NZ4_`, `KUB_`, `NZ3_`, `LBI_`, `LBO_`, `CS_`, `SS_`, `NZ2_`, `NZ1_`, `NZ0` | `_iplist_prefix`; unknown name uses first underscore token plus `_`, otherwise full name |
| Ingress investigation prefixes | `NZ0_`, `NZ1_`, `DNA_`, `DNS_` | Root investigation code, streaming code, proposal highlight code |
| Egress investigation prefixes | `NZ0_`, `NZ1_`, `KUB_`, `LBI_`, `LBO_`, `USR_`, `U_` | Same three consumers; DNA_/DNS_ are not in this outgoing tuple |
| Zone complement | Exact `ZNOT_<zone-name>` must exist | `zone_filter`, root Workloads zone loader, proposal zone resolver |
| Tagged networks | Positive CIDRs/IPs; `#...` suffix removed; `!` negative includes ignored by positive-zone/index parsing | Network extraction helpers |

Current configured election priority is `CSD_;DNS_;SSD_;USR_;U_;NZ4_;NZ3_;KUB_;LBI_;LBO_;CS_;SS_;NZ2_;NZ1_;NZ0_`. The allowed list contains the same families in a slightly different order; priority order, not allowed-list order, determines selection. DNA_ is recognised for ingress investigation but absent from the configured allowed and priority lists. Ordinary fallback may nevertheless elect it. The grouping list uses `NZ0` without underscore, whereas investigation and configured election use `NZ0_`.

## Other business-sensitive literals

| Contract | Effect and migration concern |
| --- | --- |
| `BOUQUETS_` ruleset prefix | Case-sensitive core-service annotation scan. Requires semicolon-separated `app:` tokens in src/dst labels; excludes literal Any IPList variants. Independent of bouquet applicability, which uses empty scope + label/group semantics |
| `AVOID_LABEL_PAIRS` | Exact configured app values after parsing `app=...`; force peer IPList resolution or raw-IP fallback. Rename the configured app and fixture values together |
| `role`, `app`, `env`, `loc`, `OS` | Fixed label dimensions used throughout; aliases are partial and module-specific. New dimensions are not automatically honoured |
| `DB.ORA.GEN1` | No special Oracle-specific branch was found. It is a role value processed by the general role filters; changing it still affects selected scope, joins and generated selectors |
| `deleted workload` | Case-insensitive substring in peer Name marks raw-IP peers as deleted; changing export wording changes classification |
| `Any (0.0.0.0/0)`, `All Services`, `All Roles` | Rendered sentinels used by proposal/default/comment logic, not interchangeable free text |
| `Last seen at : YYYY-MM-DD`, `DNA_<sanitised-fqdn>-IPL` | Adjacent DNA automation lifecycle contracts; changing one side can stop stale detection or create new lists |
| Temporary `_tmp_carto_egress.unknonw.ip_<timestamp>-IPL` | Root PCE lookup contract; historical `unknonw` spelling identifies the lookup artifacts and cleanup target |
| `NO_FQDN_FOUND` | Literal fallback for a completed PCE lookup without a matching IP-to-FQDN entry; not equivalent to a DNS lookup result |
| Incoming `/21` summary | Fixed IPv4 aggregation in Ingress IP to investigate, unrelated to discovered subnet masks |
| Qualys hrefs | Incoming exclusions depend on configured organisation-specific object IDs; recreated labels/IPLists need reviewed href updates |

## Migration rule

Before a naming change: identify the owner and intended semantics; inventory real names and export formats; search all implementations, config, wrappers and operator tooling; capture before/after fixtures; compare peer identity, rule category, destination ruleset, selector role retention and investigation membership; review North/South coverage and blacklist exceptions; regenerate this register and Word dossier. A renamed label or prefix is not safe merely because the command still exits zero.
