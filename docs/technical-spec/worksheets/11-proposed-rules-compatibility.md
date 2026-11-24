# Proposed Rules — compatibility analysis table

## Inputs and trigger

`propose_rule_for_scope.main` writes this exact title after Flow-Rule Match, provided the chosen analysis title is different. It is a backward-compatibility copy of matching rows, not the strategy recommendation table. Writer: `append_excel` with `OUTPUT_HEADER`.

## Construction

1. Take the same classified, role-filtered and North/South-hidden rows used by Flow-Rule Match.
2. Replace the exact matching title if it already exists.
3. Write the analysis schema: direction, anchor dimensions, peer, protocol/port, row count/timestamps, Info/Action, primary and redundant rule metadata.
4. Use the same matching colour precedence, numeric formats, wrapped evidence columns, filtering and frozen header as Flow-Rule Match.
5. Later stable recommendation generation requests `Proposed rules`, differing only in capitalisation. openpyxl's uniqueness logic renames that new sheet, which can then collide with explicit V1 `Proposed rules1`.
6. In default CreateNew the orchestrator explicitly deletes `Proposed Rules` after the proposal module returns successfully.

## Interpretation and checks

An intermediate table named Proposed Rules may contain analysed traffic rather than proposed Source/Destination/Services instructions. Check the header: analysis begins with `direction,anchor_app,...`; recommendation tables begin `Direction,Strategy,Source,...`.

Absence in a completed default run is intentional. Do not use this table as an import-ready rule payload or rename it independently of CreateNew removal and the other two proposal writers. A preserved failed-run workbook may still contain it.
