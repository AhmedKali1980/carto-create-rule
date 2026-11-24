# Adjacent components and scope boundaries

## DNA IPList automation

The `iplist_dna_automanage` subproject is a separate scheduled automation, not a stage of the root cartography workbook pipeline. It uses `conf/global.conf`, its own shell wrappers and `modules/dna_automanage.py`. See its existing [technical documentation](../../iplist_dna_automanage/docs/TECHNICAL_DOCUMENTATION.md).

Its implemented sequence is: export IPLists, managed workloads and labels; derive application-label href filters; exclude configured label prefixes; query outgoing FQDN traffic with service exclusions; discard empty FQDNs, `.compute.` names and IP-like hostnames; group destination IPs by FQDN; compare with existing selected DNA IPLists; build create/update CSV payloads; import them; identify stale entries and overlapping IPs; write a report and optionally send email.

New list names come from `sanitize_name`: `DNA_<sanitised-fqdn>-IPL`. Descriptions contain `Last seen at : YYYY-MM-DD`; stale detection parses that literal phrase and defaults to an age greater than 21 days. The prefix used to select existing lists is configurable (`DNA_IPLIST_PREFIX`), while new names are hardcoded to DNA_. Changing only the configurable prefix would not migrate creation behaviour.

The automation performs create/update imports. Stale candidates are reported; they are not automatically deleted by that reporting stage. It is not a harmless startup check and is not a default offline workflow. The separate wrappers use their own Workloader/config argument conventions and retry settings.

The helper `docs/build_docx.py` creates a small Word document for that subproject's older Markdown. It is independent of the new root technical-spec dossier generator. Do not confuse either document's coverage with the root Excel pipeline.

## Other legacy modules and documentation

`modules/common_io.py` contains shared CSV/path helpers but not every module uses them. Some path-election logic is duplicated. `docs/proposed_rules1_algorithm.md` provides an earlier French algorithm table; this English specification is source-traced at the stated baseline and explicitly records naming/case collisions and operational caveats. Preserve the older note as historical context rather than assuming all its output claims apply to every current mode.

CreateRules and RecertifyRules entry points reference missing legacy modules. Their potential workbook tabs cannot be specified as implemented deliverables in this checkout. Likewise configuration entries for BLOCKED_DIFF and UNKNOWN_IPS do not establish that such sheets are created. [The worksheet catalogue](worksheets/README.md) enumerates every worksheet writer found in the available cartography source.
