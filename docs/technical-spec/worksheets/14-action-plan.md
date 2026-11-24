# Action Plan

## Inputs and trigger

Source: `propose_rule_for_scope.propose` and final `main` output stage, using `append_excel`. This is an analysis-task subset, not the V1 policy recommendation table. The default CreateNew orchestrator removes it after the module succeeds.

## Construction

1. Aggregate and classify traffic as for Flow-Rule Match. No applicable matching rule sets Action=Create; multiple matches set Optimize; a single match or deleted workload sets No Action.
2. Select only Create/Optimize rows, preserving matching-table order. Apply the same anchor-role filter in main.
3. Unlike Flow-Rule Match's explicit `rows_flow_match` filtering, the action subset is not separately stripped of internal North/South candidates before writing.
4. After proposal generation and legend update, replace Action Plan using the matching `OUTPUT_HEADER`: scope/peer/service/counts, action/category, primary/redundant evidence and ruleset metadata.
5. Apply matching-table formats/colours and save. Run post-formatting afterward. In the root default mode delete exact titles Action Plan and Proposed Rules; Flow-Rule Match remains.

## Interpretation and checks

Create/Optimize describe review tasks and possible overlap, not automatic remediation. In particular, redundant matches do not establish which rule can be removed safely. This sheet does not include every proposed policy row, and proposal builders can use already covered business traffic outside this subset.

A header-only Action Plan is possible. Absence from a final default workbook is expected; presence in an intermediate failed file does not prove completion. To analyse it separately, run the module on a workbook copy with explicit original dates/scope, recognising that the orchestrator normally removes it later.
