# Flow-out

## Inputs and trigger

Normal writer: `build_final_excel` / nested `style_flow_sheet`. Streaming writer: `excel_stream_update._stream_flow_csv`. Both use raw `flows_out_<start>_<end>.csv`, not the derived zone-filtered matching input. Normal mode skips an empty table; streaming constructs a replacement sheet from the supplied CSV.

## Construction

1. Live extraction includes source label hrefs for the non-role scope. Two Workloader queries partition reported policy-decision classes. Merge their records through `merge_traffic_csv` with one header and final `0640` permission. A flow stub instead copies a supplied historical file to the current window's output name.
2. Read raw records into a DataFrame in normal mode; stream rows into a write-only workbook at finalisation in streaming mode. Preserve the exported column order and data fields.
3. If enabled, insert `Destination IPList Elected` immediately after `Destination IPList`. Split tokens on semicolon/comma/whitespace; strip href tails; narrow to allowed families when any match exists; apply first configured priority; otherwise lexical fallback.
4. Convert Port and Num Flows to numeric in normal mode. Streaming also recognises Bytes In/Out as numeric. Apply integer display, borders, frozen header and filtering.
5. Colour source/anchor columns green, destination/peer columns orange, and transport/observation columns blue. Streaming uses direction-aware column-family palettes and width caps.

## Interpretation and checks

This is observed outgoing traffic, not only unmatched flows or recommended policy. Role filtering is intentionally later. An elected IPList is a single display/analysis identity, not a listing of every matching network. Eligibility is a preference fallback in ordinary election, not a guaranteed rejection of all unlisted families.

The report may show raw flows outside a requested network zone. Confirm original extraction dates, header compatibility, data counts, one merged header and elected destination identities. Streaming rebuilds the workbook and copies selected values/styles; it is not a byte-preserving Excel round trip.
