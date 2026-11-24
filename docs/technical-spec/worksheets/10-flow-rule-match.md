# Flow-Rule Match

## Inputs and trigger

Source: `propose_rule_for_scope.main`, `propose`, `proposal_matches_rule`, `append_excel`. Created by the analysis branch and retained by default CreateNew. Input is the selected incoming/outgoing flow pair, applicable rules, groups and election/configuration rules. Module default grouping is labels and minimum row count is 1.

## Construction

1. Prefer a complete derived zone pair unless `--prefer-raw`; otherwise use exact dated raw pair, then latest matching dated pair. Log the actual selected files.
2. Map anchor/peer sides by direction, resolve peer identity, normalise protocol/port and aggregate by raw direction, five anchor labels, peer type/value and service. Track CSV record count and timestamps.
3. In zone mode keep East-West records plus special managed remote egress candidates. The latter contribute to proposals but are excluded from this sheet.
4. Classify groups against services and both selectors of each applicable rule. Deleted-workload IP overrides matching; otherwise select primary by category priority and deterministic ruleset/description ordering. Preserve other matches as multiline redundant metadata.
5. Apply the anchor-role filter and, for intra-app rows with a peer role, the same peer-role filter. Write `derived/flow_rule_match_<start>_<end>.csv` and replace the worksheet using `OUTPUT_HEADER`.
6. Output anchor fields, peer/service/count/time fields, suggested ruleset, Info/Action/category, primary selectors, redundant selectors/categories/names/descriptions, and primary ruleset/description last. Freeze/filter, integer formats and wrapping apply.
7. Colour precedence is investigation-prefix red, deleted grey, Optimize orange, no-match/Create yellow, bouquet blue, business in-scope green, other-scope pink. The later legend is a separate workbook load/save and occupies extra columns/rows on the same sheet; worksheet max_row is not the analysis-record count.

## Interpretation and checks

`num_flows` is aggregated input-row count. Incoming/outgoing records remain distinct even when UI direction becomes intra-app. `Create` means no algorithmic match, `Optimize` means multiple matches, and `No Action` is not a certification of policy correctness. The suggested ruleset here is a helper based on anchor app/env, not the final V1 placement.

Validate one primary and one redundant match against raw selectors/services, verify role/zone filtering, and compare the CSV with worksheet rows. A successful write can precede a later SIGKILL or proposal failure.
