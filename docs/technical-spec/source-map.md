# Source traceability map

Documented baseline: `30733ecc165f937e56af21bbec8af0d9043d5ce3`. Links below point to the local source; the Word dossier links to that exact GitHub commit. Function names are the stable lookup key when line numbers drift.

## carto_ng_orchestrator.py

| Function | Source |
| --- | --- |
| `main` | [line 2042](../../carto_ng_orchestrator.py#L2042) |
| `load_conf` | [line 54](../../carto_ng_orchestrator.py#L54) |
| `run_step` | [line 214](../../carto_ng_orchestrator.py#L214) |
| `compute_window_days` | [line 181](../../carto_ng_orchestrator.py#L181) |
| `parse_role_filter` | [line 281](../../carto_ng_orchestrator.py#L281) |
| `find_managed_wkld_hrefs_for_filters` | [line 482](../../carto_ng_orchestrator.py#L482) |
| `explode_reason_to_matches` | [line 447](../../carto_ng_orchestrator.py#L447) |
| `join_with_managed` | [line 514](../../carto_ng_orchestrator.py#L514) |
| `enrich_workloads` | [line 579](../../carto_ng_orchestrator.py#L579) |
| `build_labelgroup_inclusions_single` | [line 743](../../carto_ng_orchestrator.py#L743) |
| `build_final_excel` | [line 982](../../carto_ng_orchestrator.py#L982) |
| `find_rules_with_unmanaged_app_labels` | [line 837](../../carto_ng_orchestrator.py#L837) |
| `build_to_investigate_sheet` | [line 1515](../../carto_ng_orchestrator.py#L1515) |
| `build_to_investigate_ip_sheets` | [line 1686](../../carto_ng_orchestrator.py#L1686) |
| `enrich_unknown_ips_with_pce_fqdn` | [line 1957](../../carto_ng_orchestrator.py#L1957) |
| `rename_final_excel` | [line 160](../../carto_ng_orchestrator.py#L160) |

## modules/scope_rules_applicability.py

| Function | Source |
| --- | --- |
| `_load_selected_scope` | [line 78](../../modules/scope_rules_applicability.py#L78) |
| `load_labelgroups` | [line 121](../../modules/scope_rules_applicability.py#L121) |
| `gather_scope_label_values_from_wkld_m` | [line 142](../../modules/scope_rules_applicability.py#L142) |
| `load_rules_enabled` | [line 178](../../modules/scope_rules_applicability.py#L178) |
| `_bouquet_block_valid` | [line 322](../../modules/scope_rules_applicability.py#L322) |
| `get_applicable_rules` | [line 352](../../modules/scope_rules_applicability.py#L352) |
| `append_scope_rules_sheet` | [line 454](../../modules/scope_rules_applicability.py#L454) |

## modules/flows_to_rules.py

| Function | Source |
| --- | --- |
| `_ensure_selected_scope_file` | [line 100](../../modules/flows_to_rules.py#L100) |
| `main` | [line 157](../../modules/flows_to_rules.py#L157) |

## modules/propose_rule_for_scope.py

| Function | Source |
| --- | --- |
| `elect_iplist_from_tokens` | [line 422](../../modules/propose_rule_for_scope.py#L422) |
| `_find_flow_files` | [line 463](../../modules/propose_rule_for_scope.py#L463) |
| `_filter_rows_by_scope_role` | [line 541](../../modules/propose_rule_for_scope.py#L541) |
| `_side_matches` | [line 856](../../modules/propose_rule_for_scope.py#L856) |
| `proposal_matches_rule` | [line 930](../../modules/propose_rule_for_scope.py#L930) |
| `detect_peer_type` | [line 1011](../../modules/propose_rule_for_scope.py#L1011) |
| `propose` | [line 1041](../../modules/propose_rule_for_scope.py#L1041) |
| `append_excel` | [line 1628](../../modules/propose_rule_for_scope.py#L1628) |
| `build_avoid_iplist_network_index` | [line 2251](../../modules/propose_rule_for_scope.py#L2251) |
| `make_iplist_resolver` | [line 2313](../../modules/propose_rule_for_scope.py#L2313) |
| `_expand_blacklist_sources` | [line 2420](../../modules/propose_rule_for_scope.py#L2420) |
| `_resolve_blacklist_sources_for_direction` | [line 2569](../../modules/propose_rule_for_scope.py#L2569) |
| `build_intra_app_proposed_rules` | [line 2747](../../modules/propose_rule_for_scope.py#L2747) |
| `append_excel_simple_table` | [line 2993](../../modules/propose_rule_for_scope.py#L2993) |
| `add_flow_rule_match_legend` | [line 3208](../../modules/propose_rule_for_scope.py#L3208) |
| `_iplist_prefix` | [line 3334](../../modules/propose_rule_for_scope.py#L3334) |
| `_app_prefix` | [line 3353](../../modules/propose_rule_for_scope.py#L3353) |
| `_is_managed_app_prefix` | [line 3365](../../modules/propose_rule_for_scope.py#L3365) |
| `_source_selector_for_peer_labels` | [line 3376](../../modules/propose_rule_for_scope.py#L3376) |
| `_load_bouquets_refs` | [line 3510](../../modules/propose_rule_for_scope.py#L3510) |
| `build_ingress_labels_extrascope_proposed_rules_v1` | [line 3596](../../modules/propose_rule_for_scope.py#L3596) |
| `build_ingress_proposed_rules` | [line 3726](../../modules/propose_rule_for_scope.py#L3726) |
| `build_ingress_proposed_rules_v1` | [line 3702](../../modules/propose_rule_for_scope.py#L3702) |
| `build_egress_proposed_rules` | [line 3978](../../modules/propose_rule_for_scope.py#L3978) |
| `build_egress_labels_proposed_rules_v1` | [line 4222](../../modules/propose_rule_for_scope.py#L4222) |
| `build_egress_proposed_rules_v1` | [line 4477](../../modules/propose_rule_for_scope.py#L4477) |
| `main` | [line 4722](../../modules/propose_rule_for_scope.py#L4722) |

## modules/export_services.py

| Function | Source |
| --- | --- |
| `categorize` | [line 122](../../modules/export_services.py#L122) |
| `to_rows_catalog` | [line 130](../../modules/export_services.py#L130) |
| `append_to_excel_openpyxl` | [line 173](../../modules/export_services.py#L173) |
| `main` | [line 267](../../modules/export_services.py#L267) |

## modules/zone_filter.py

| Function | Source |
| --- | --- |
| `_load_zone_networks` | [line 182](../../modules/zone_filter.py#L182) |
| `_filter_one_file` | [line 228](../../modules/zone_filter.py#L228) |
| `main` | [line 271](../../modules/zone_filter.py#L271) |

## modules/excel_stream_update.py

| Function | Source |
| --- | --- |
| `elect_iplist_from_tokens` | [line 96](../../modules/excel_stream_update.py#L96) |
| `_stream_flow_csv` | [line 649](../../modules/excel_stream_update.py#L649) |
| `rewrite_workbook_with_streamed_flows` | [line 921](../../modules/excel_stream_update.py#L921) |

## modules/email_utils.py

| Function | Source |
| --- | --- |
| `send_carto_notification` | [line 67](../../modules/email_utils.py#L67) |

## iplist_dna_automanage/modules/dna_automanage.py

| Function | Source |
| --- | --- |
| `sanitize_name` | [line 69](../../iplist_dna_automanage/modules/dna_automanage.py#L69) |
| `parse_last_seen` | [line 74](../../iplist_dna_automanage/modules/dna_automanage.py#L74) |
| `main` | [line 81](../../iplist_dna_automanage/modules/dna_automanage.py#L81) |

## Shell extraction

[Common retry and CSV merge](../../bin/workloader_common.sh), [outgoing traffic](../../bin/workloader_traffic_out.sh), [incoming traffic](../../bin/workloader_traffic_in.sh), [temporary IPList import](../../bin/workloader_ipl_import.sh) and [delete](../../bin/workloader_ipl_delete.sh) form the root shell boundary.

## Scope of this map

This map is generated from the checked-out source. When documenting a newer implementation, deliberately update the baseline metadata, revise the affected chapters and revalidate behaviour before regenerating the dossier.
