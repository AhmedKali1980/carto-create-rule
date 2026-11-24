# Service Catalogue

## Inputs and trigger

Source: `modules/export_services.py`, `main`, `normalize_flow_row`, `categorize`, `to_rows_catalog`, `append_to_excel_openpyxl`. The root calls it if `ENABLE_SERVICES_CATALOG` is truthy OR CreateNew/FlowRuleReview is active. It uses exact dated raw incoming/outgoing files. If both contain no rows, it warns and returns without creating the tab.

## Construction

1. Read the two raw CSVs. Resolve Port, Protocol/Proto, Transmission/Direction, Num Flows/Hits and first/last detection aliases. Ignore rows lacking port/protocol columns.
2. Normalise protocol to uppercase, port to integer with zero fallback, counts to integer with zero fallback and timestamps to strings.
3. Parse configured control, eradication, admin and allowed port/protocol expressions. Categorise each proto/port using precedence **ERADICATE → CONTROL → ADMIN → ALLOWED → UNKNOWN**.
4. Aggregate by protocol and port. Add raw counts, using 1 when the parsed count is zero/missing; add directional counts only when Transmission starts with Incoming or Outgoing. Track earliest first_seen and latest last_seen using string ordering.
5. Sort category/protocol/port and write `derived/services_catalog.csv` with `category,proto,port,flows_total,flows_in,flows_out,first_seen,last_seen`.
6. Replace or create Service Catalogue, append rows, colour the category column, format headers, widths, borders and filtering, then save the workbook.

## Interpretation and checks

It is a raw observed-service inventory. It is not constrained by the later anchor-role or East-West filtering, nor does it identify rule ownership or actual PCE rule hits. Directional subtotals can be zero if Transmission is missing or uses different wording. Records visible in both exports are not deduplicated. Invalid/zero raw counts contribute one.

The category label expresses configured service governance, not a verified vulnerability. Check overlapping port lists against the stated precedence and compare a sample aggregation to raw records. Excel append errors can be warned while the module exits zero; CSV existence does not prove the tab was saved.
