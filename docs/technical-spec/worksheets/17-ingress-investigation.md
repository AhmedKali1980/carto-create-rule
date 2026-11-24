# Ingress IP to investigate

## Inputs and trigger

Built with the outgoing summary by `build_to_investigate_ip_sheets`, from To investigate after the optional PCE lookup phase. It requires the common Direction/Unknown IP headers, not the presence of incoming rows. A normal empty table still has a header.

## Construction

1. Scan source rows in order. Keep Direction=`flow-in`, using case-insensitive comparison after trimming.
2. Extract the first IPv4-looking token in Unknown IP. Deduplicate by that token, keeping the first Source metadata and discarding subsequent role/service distinctions for that IP.
3. Calculate `Subnet /21` using `ipaddress.ip_network(f'{ip}/21', strict=False)`. Invalid addresses leave the subnet blank. This is a fixed derived IPv4 grouping, not a discovered interface/network mask.
4. Replace the sheet and write `Direction,Source,Unknown IP,Subnet /21`. No DNS, FQDN, service or Action column is carried into this summary.
5. Apply grey/bold headers, cell borders, widths, frozen header and filtering. Save together with Egress IP to investigate.

## Interpretation and checks

The /21 decision is a hardcoded business/reporting assumption that must be reviewed before applying this sheet to another addressing convention. A source subnet is not established by observing one address. IPv6 records are not represented by this dotted-IPv4 summariser.

Check repeated-IP deduplication and representative Source, then verify a sample /21 boundary (for example, 192.0.2.17 maps to 192.0.0.0/21). If To investigate is missing or malformed, the function returns without creating the pair; the outer orchestrator warns on exceptions and may otherwise finish.
