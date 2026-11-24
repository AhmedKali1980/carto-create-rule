# Rules with umgd app labels

## Inputs and trigger

Built inside `build_final_excel` when `enable_umgd_app_label_rules_sheet` is true (root CLI defaults true). Source function: `find_rules_with_unmanaged_app_labels`. Inputs are Workloads `app_unmanaged` values and `raw/export_rules.enabled.csv`.

## Construction

1. Collect distinct nonempty unmanaged application values from the constructed Workloads DataFrame. Values already depend on the reconciliation and tuple-based scope logic.
2. Read the enabled-rule export with delimiter sniffing and UTF-8 BOM tolerance. Select ruleset name/scope, type/description/enabled status, services and source/destination label/exclusion columns.
3. Scan `ruleset_scope`, `src_labels`, `src_labels_exclusions`, `dst_labels`, `dst_labels_exclusions` for app expressions. The regex accepts `app:` or `app=` and values composed of letters, numbers, underscore, dot and hyphen.
4. Intersect extracted app values with unmanaged app values. For each matching export row, keep the rule metadata and scanned selectors, add comma-joined `matched_umgd_apps` and `matched_in_columns`.
5. Write the worksheet even for a normal empty result, using fixed headers, dark blue header formatting, filters and widths. Exceptions are warned and can skip the worksheet.

## Interpretation and checks

This is a reference audit: an app value in an exclusion is included intentionally. It does not mean the rule authorises that unmanaged workload, has hits, or belongs to the selected scope. Label groups and IPList membership are not expanded here. The function does not independently filter the enabled flag; it trusts the exported dataset despite displaying `rule_enabled`.

An app-name alphabet change can truncate regex extraction. Confirm a sample rule referring to an unmanaged app in both a positive selector and an exclusion. Empty output may mean no references, no unmanaged scope apps or an absent export; distinguish these through logs and inputs.
