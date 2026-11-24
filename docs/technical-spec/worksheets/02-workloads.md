# Workloads

## Inputs and trigger

Always created by `build_final_excel`, from `all_rows` assembled using dupecheck and managed/unmanaged workload exports. Its column contract includes Info; managed href, host, five labels, interfaces, managed/enforcement state; unmanaged href, host/name, interfaces and five labels; match_type and reason.

## Construction

1. Detect raw reason-based, exploded or already-final dupecheck schema. Raw reasons are split on semicolons; extract managed workload hrefs, classify one-interface versus all-interface matches, deduplicate pairs and enrich managed attributes.
2. Find managed workloads matching selected labels, including role grammar. Filter duplicate rows by those hrefs when the set is nonempty and filtering is enabled. Already-final input provides a fallback href scope when normal selection is empty.
3. Preserve matched rows as `Duplicate found`, then append unmatched managed scope rows as `Not Active in CMDB`.
4. Build lower-case role/app/env/loc tuples from unmanaged sides of matched duplicate rows. Append unmanaged export entries with one of those tuples and no matched href as `Missing Agent`. If no duplicate tuples exist, this heuristic adds no unmanaged-only rows.
5. Write the final CSV in derived/ and the worksheet in fixed managed/unmanaged column order. With network-zone, insert `Inside Network Zone` after managed interfaces.
6. Zone membership uses any parsed managed interface IP in the positive zone networks. Invalid zone lookup gives UNKNOWN. The code overwrites its initial unmanaged-interface fallback with managed interfaces: an unmanaged-only row can show N even when its unmanaged IP belongs to the zone.
7. Freeze/filter the header, apply green managed columns, orange unmanaged columns, grey Info and blue match evidence, with widths and borders.

## Interpretation and checks

`Not Active in CMDB` and `Missing Agent` express join-based heuristics; neither comes from a live CMDB/agent health call. One managed host can have multiple duplicate rows. Test with a duplicate pair, a managed-only host and an unmanaged-only matching tuple. Network-zone adds an indicator; it does not filter the entire Workloads table to the zone.
