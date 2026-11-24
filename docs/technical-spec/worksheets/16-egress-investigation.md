# Egress IP to investigate

## Inputs and trigger

Source: `carto_ng_orchestrator.build_to_investigate_ip_sheets`, run near finalisation after optional FQDN enrichment. Requires To investigate with Direction and Unknown IP headers. It creates this sheet and its incoming counterpart together, including header-only results.

## Construction

1. Read To investigate in its existing order. Keep rows whose trimmed lower-case Direction is `flow-out`.
2. Extract IPv4-looking values with a dotted-decimal regex from Unknown IP and take the first candidate. The regex alone does not validate all octets; IPv6 is not summarised here.
3. Keep only the first row for each selected IP. Copy Destination, Unknown IP, DNS Resolution and FQDN found in PCE if those columns exist. Role/service distinctions in later rows for that IP are discarded.
4. Remove the previous summary sheet. Write `Direction,Destination,Unknown IP,DNS Resolution,FQDN found in PCE,Action`. Action is initially empty for manual review.
5. Apply grey/bold headers, borders, fixed widths, A2 freezing and filtering. Save both summary sheets in one workbook operation.

## Interpretation and checks

This is one first-seen representative record per outgoing IPv4, not an aggregation of all destinations, roles, services or evidence for that IP. Empty FQDN may mean skipped/failed enrichment or no observed name. It is not proof of absent DNS.

Changing To investigate row order can change representative metadata without changing the number of IPs. Verify repeated-IP handling, outgoing/incoming separation, optional missing FQDN column and the intentionally blank Action field. This function only writes workbook content; it does not implement analyst actions.
