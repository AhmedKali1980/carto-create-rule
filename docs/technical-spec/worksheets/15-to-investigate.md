# To investigate

## Inputs and trigger

Enabled by default. Normal path: `build_to_investigate_sheet` reads finished Flow-out/Flow-in sheets. Streaming path: `_stream_flow_csv` collects matching rows to a temporary disk CSV during flow injection, then `rewrite_workbook_with_streamed_flows` constructs the sheet. Source: elected peer IPList, endpoint roles/IP, service fields and optional DNS.

## Construction

1. For outgoing rows retain elected destination prefixes `NZ0_,NZ1_,KUB_,LBI_,LBO_,USR_,U_`. For incoming rows retain elected source prefixes `NZ0_,NZ1_,DNA_,DNS_`. These tuples are directional and case-sensitive.
2. Map outgoing Source to Source Role, Destination to elected destination IPList, Unknown IP to Destination IP. Incoming Source is elected source IPList, Destination is Destination Role, Unknown IP is Source IP. Normal mode includes fallbacks when role values/columns are unavailable.
3. Use an available service field, otherwise build Protocol/Port. Perform cached, best-effort reverse DNS with configured timeout. A missing PTR record does not invalidate the row.
4. Deduplicate by all six output values: Direction (`Flow-out`/`Flow-in`), Source, Destination, Service, Unknown IP and DNS Resolution. Different roles/services can therefore yield several rows for one IP.
5. Replace/create the sheet with these six columns, filter/freeze header and set widths. It can be empty if no elected prefix qualifies. Streaming disk-backs collected rows but still keeps deduplication sets in memory.
6. Unless explicitly skipped, collect unique outgoing IPv4 candidates (excluding 169.254.*), create/provision a temporary PCE IPList, export its href, query traffic to it and map Destination IP to FQDN. Add/update `FQDN found in PCE` (using `NO_FQDN_FOUND` when no map entry exists); attempt temporary-list deletion when href discovery succeeded.

## Interpretation and checks

This is a naming-based review queue, not all unknown Internet addresses. It depends on election and raw flows, so role/zone-limited matching results can be narrower. DNS resolution and observed FQDN are different evidence sources; the latter requires PCE operations and write privileges.

Preserve exact title and columns: both final IP summary sheets and FQDN enrichment read them by name. Verify direction, a qualifying and nonqualifying prefix, multiple services for one IP and graceful DNS failure. No temporary-PCE lookup is performed by the documentation's offline checks.
