# Flow-in

## Inputs and trigger

Normal and streaming writers are the same as Flow-out, with incoming direction. Source is raw `flows_in_<start>_<end>.csv`; derived `flows_in.zone.csv` is used for analysis, not this exported-observation sheet.

## Construction

1. Resolve include label hrefs for the destination scope with role deliberately omitted. Build newline-delimited Qualys source-label and source-IPList exclusion files from configured hrefs.
2. The incoming wrapper supplies `--incl-dst-file` and optional `--excl-src-file` arguments. It performs the two reported-decision extraction queries, merges their data while dropping the second header, sets `0640`, and renames the completed CSV. Incoming stubs bypass those queries but not later processing.
3. Load the raw records into a normal DataFrame, or stream them during final workbook reconstruction.
4. Insert `Source IPList Elected` after `Source IPList` when enabled. The source is the remote peer, so it uses the common allowed/priority prefix election contract.
5. Preserve exported metadata, coerce numeric fields as in the outgoing sheet, colour source/peer columns orange, destination/anchor columns green, and service/observation columns blue. Add widths, frozen header, borders and filtering.

## Interpretation and checks

Incoming source exclusions are specific to extraction: they do not automatically exclude the same traffic from outgoing exports, IPList indexes or rule references. Recreated Qualys objects require updated hrefs, not only matching names.

The table can contain roles not selected for final proposals and traffic outside a network zone. To investigate later checks the elected source prefix; this must not be confused with outgoing destination-prefix logic. Normal mode omits Flow-in for an empty DataFrame; a downstream missing tab can therefore be an empty-data condition. Validate the raw source count, exclusion configuration and source election independently from matching-sheet totals.
