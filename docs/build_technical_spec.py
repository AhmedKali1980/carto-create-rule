#!/usr/bin/env python3
"""Build the English handover dossier from the targeted Markdown chapters.

Run from any directory with Python 3.12 and python-docx 1.2.0 installed.
Application code is parsed for source references, never imported or executed.
"""
from __future__ import annotations

import ast
import hashlib
import re
from pathlib import Path
from urllib.parse import quote

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.opc.constants import RELATIONSHIP_TYPE as RT

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO / "docs" / "technical-spec"
OUTPUT = ROOT / "Carto_NG_Technical_Specification.docx"
BASELINE = "30733ecc165f937e56af21bbec8af0d9043d5ce3"
SOURCE_URL = f"https://github.com/AhmedKali1980/carto-create-rule/blob/{BASELINE}/"
CHAPTERS = [
    "README.md", "01-end-to-end.md", "02-data-contracts.md",
    "03-scope-and-matching.md", "04-proposal-strategies.md",
    "05-convention-register.md", "worksheets/README.md",
    *[str(p.relative_to(ROOT)) for p in sorted((ROOT / "worksheets").glob("[0-9]*.md"))],
    "06-operations.md", "07-maintenance.md", "08-adjacent-components.md",
    "source-map.md",
]

SYMBOLS = {
    "carto_ng_orchestrator.py": [
        "main", "load_conf", "run_step", "compute_window_days", "parse_role_filter",
        "find_managed_wkld_hrefs_for_filters", "explode_reason_to_matches", "join_with_managed",
        "enrich_workloads", "build_labelgroup_inclusions_single", "build_final_excel",
        "find_rules_with_unmanaged_app_labels", "build_to_investigate_sheet",
        "build_to_investigate_ip_sheets", "enrich_unknown_ips_with_pce_fqdn", "rename_final_excel",
    ],
    "modules/scope_rules_applicability.py": [
        "_load_selected_scope", "load_labelgroups", "gather_scope_label_values_from_wkld_m",
        "load_rules_enabled", "_bouquet_block_valid", "get_applicable_rules", "append_scope_rules_sheet",
    ],
    "modules/flows_to_rules.py": ["_ensure_selected_scope_file", "main"],
    "modules/propose_rule_for_scope.py": [
        "elect_iplist_from_tokens", "_find_flow_files", "_filter_rows_by_scope_role",
        "_side_matches", "proposal_matches_rule", "detect_peer_type", "propose",
        "append_excel", "build_avoid_iplist_network_index", "make_iplist_resolver",
        "_expand_blacklist_sources", "_resolve_blacklist_sources_for_direction",
        "build_intra_app_proposed_rules", "append_excel_simple_table", "add_flow_rule_match_legend",
        "_iplist_prefix", "_app_prefix", "_is_managed_app_prefix", "_source_selector_for_peer_labels",
        "_load_bouquets_refs", "build_ingress_labels_extrascope_proposed_rules_v1",
        "build_ingress_proposed_rules", "build_ingress_proposed_rules_v1",
        "build_egress_proposed_rules", "build_egress_labels_proposed_rules_v1",
        "build_egress_proposed_rules_v1", "main",
    ],
    "modules/export_services.py": ["categorize", "to_rows_catalog", "append_to_excel_openpyxl", "main"],
    "modules/zone_filter.py": ["_load_zone_networks", "_filter_one_file", "main"],
    "modules/excel_stream_update.py": [
        "elect_iplist_from_tokens", "_stream_flow_csv", "rewrite_workbook_with_streamed_flows",
    ],
    "modules/email_utils.py": ["send_carto_notification"],
    "iplist_dna_automanage/modules/dna_automanage.py": ["sanitize_name", "parse_last_seen", "main"],
}


def write_source_map() -> None:
    lines = ["# Source traceability map", "",
             f"Documented baseline: `{BASELINE}`. Links below point to the local source; "
             "the Word dossier links to that exact GitHub commit. Function names are the "
             "stable lookup key when line numbers drift.", ""]
    for source, selected in SYMBOLS.items():
        tree = ast.parse((REPO / source).read_text(encoding="utf-8"))
        functions = {n.name: n.lineno for n in tree.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        lines += [f"## {source}", "", "| Function | Source |", "| --- | --- |"]
        for name in selected:
            line = functions[name]
            lines.append(f"| `{name}` | [line {line}](../../{source}#L{line}) |")
        lines.append("")
    lines += ["## Shell extraction", "",
              "[Common retry and CSV merge](../../bin/workloader_common.sh), "
              "[outgoing traffic](../../bin/workloader_traffic_out.sh), "
              "[incoming traffic](../../bin/workloader_traffic_in.sh), "
              "[temporary IPList import](../../bin/workloader_ipl_import.sh) and "
              "[delete](../../bin/workloader_ipl_delete.sh) form the root shell boundary.", "",
              "## Scope of this map", "",
              "This map is generated from the checked-out source. When documenting a newer "
              "implementation, deliberately update the baseline metadata, revise the affected "
              "chapters and revalidate behaviour before regenerating the dossier.", ""]
    (ROOT / "source-map.md").write_text("\n".join(lines), encoding="utf-8")


def slug(text: str) -> str:
    return re.sub(r"[^\w\- ]", "", text.lower()).replace(" ", "-")


def bookmark_name(path: Path, heading: str = "") -> str:
    key = str(path.resolve()) + "#" + heading
    return "b" + hashlib.sha256(key.encode()).hexdigest()[:28]


def add_bookmark(paragraph, name: str, ident: int) -> None:
    start = OxmlElement("w:bookmarkStart")
    start.set(qn("w:id"), str(ident)); start.set(qn("w:name"), name)
    end = OxmlElement("w:bookmarkEnd"); end.set(qn("w:id"), str(ident))
    paragraph._p.insert(0, start); paragraph._p.append(end)


def hyperlink(paragraph, label: str, target: str, internal: bool = False) -> None:
    link = OxmlElement("w:hyperlink")
    if internal:
        link.set(qn("w:anchor"), target)
    else:
        rid = paragraph.part.relate_to(target, RT.HYPERLINK, is_external=True)
        link.set(qn("r:id"), rid)
    run = OxmlElement("w:r"); props = OxmlElement("w:rPr")
    color = OxmlElement("w:color"); color.set(qn("w:val"), "087E8B"); props.append(color)
    underline = OxmlElement("w:u"); underline.set(qn("w:val"), "single"); props.append(underline)
    run.append(props); text = OxmlElement("w:t"); text.text = label; run.append(text)
    link.append(run); paragraph._p.append(link)


INLINE = re.compile(r"(\[[^\]]+\]\([^)]+\)|`[^`]+`|\*\*[^*]+\*\*)")


def inline(paragraph, text: str, current: Path) -> None:
    for piece in INLINE.split(text):
        if not piece:
            continue
        match = re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)", piece)
        if match:
            label, target = match.groups()
            if target.startswith(("https://", "http://")):
                hyperlink(paragraph, label, target)
            else:
                file_part, _, anchor = target.partition("#")
                dest = (current.parent / file_part).resolve() if file_part else current.resolve()
                if dest in INCLUDED:
                    hyperlink(paragraph, label, bookmark_name(dest, anchor), True)
                else:
                    relative = dest.relative_to(REPO).as_posix()
                    hyperlink(paragraph, label, SOURCE_URL + quote(relative) + ("#" + anchor if anchor else ""))
        elif piece.startswith("`"):
            run = paragraph.add_run(piece[1:-1]); run.font.name = "Consolas"; run.font.size = Pt(9)
        elif piece.startswith("**"):
            paragraph.add_run(piece[2:-2]).bold = True
        else:
            paragraph.add_run(piece)


def table(doc, rows: list[str], current: Path) -> None:
    cells = [[c.strip() for c in line.strip().strip("|").split("|")] for line in rows]
    cells = [r for r in cells if not all(re.fullmatch(r":?-+:?", c) for c in r)]
    tbl = doc.add_table(rows=0, cols=len(cells[0])); tbl.style = "Light Shading Accent 1"
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    for idx, row in enumerate(cells):
        word_row = tbl.add_row()
        for cell, value in zip(word_row.cells, row):
            inline(cell.paragraphs[0], value, current)
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_after = Pt(4)
                for run in paragraph.runs:
                    run.font.size = Pt(8.5)
                    if idx == 0: run.bold = True
        if idx == 0:
            repeat = OxmlElement("w:tblHeader"); word_row._tr.get_or_add_trPr().append(repeat)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def render_chapter(doc, path: Path, ident: int) -> int:
    lines = path.read_text(encoding="utf-8").splitlines(); i = 0
    doc.add_page_break()
    nav = doc.add_paragraph(); hyperlink(nav, "Back to contents", "contents", True)
    while i < len(lines):
        line = lines[i]
        if not line.strip(): i += 1; continue
        if line.startswith("```"):
            i += 1; code = []
            while i < len(lines) and not lines[i].startswith("```"):
                code.append(lines[i]); i += 1
            for value in code:
                p = doc.add_paragraph(style="Code Block"); p.add_run(value)
            i += 1; continue
        heading = re.match(r"^(#{1,6}) (.*)", line)
        if heading:
            level = min(len(heading[1]), 4); title = heading[2]
            p = doc.add_heading(title, level)
            if level == 1:
                add_bookmark(p, bookmark_name(path), ident); ident += 1
            add_bookmark(p, bookmark_name(path, slug(title)), ident); ident += 1
            i += 1; continue
        if line.startswith("|"):
            block = []
            while i < len(lines) and lines[i].startswith("|"):
                block.append(lines[i]); i += 1
            table(doc, block, path); continue
        item = re.match(r"^(\d+\. |[-*] )(.*)", line)
        if item:
            # Explicit numeric prefixes preserve sequences across intervening tables.
            p = doc.add_paragraph(style="List Bullet" if line.startswith(("- ", "* ")) else None)
            inline(p, item[2] if line.startswith(("- ", "* ")) else line, path)
            i += 1; continue
        para = [line]; i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||```|\d+\. |[-*] )", lines[i]):
            para.append(lines[i]); i += 1
        p = doc.add_paragraph(); inline(p, " ".join(para), path)
    return ident


INCLUDED = {(ROOT / name).resolve() for name in CHAPTERS}


def build() -> None:
    write_source_map()
    doc = Document(); section = doc.sections[0]
    section.page_width = Cm(21); section.page_height = Cm(29.7)
    section.top_margin = Cm(1.8); section.bottom_margin = Cm(1.8)
    section.left_margin = Cm(1.9); section.right_margin = Cm(1.9)
    normal = doc.styles["Normal"]; normal.font.name = "Calibri"; normal.font.size = Pt(10)
    normal.paragraph_format.space_after = Pt(6); normal.paragraph_format.line_spacing = 1.08
    for name in ["Heading 1", "Heading 2", "Heading 3"]:
        style = doc.styles[name]; style.font.name = "Calibri"; style.font.color.rgb = RGBColor.from_string("17365D")
        style.paragraph_format.keep_with_next = True
    code = doc.styles.add_style("Code Block", 1); code.font.name = "Consolas"; code.font.size = Pt(8)
    code.paragraph_format.space_after = Pt(0); code.paragraph_format.line_spacing = 1
    section.header.paragraphs[0].text = "CARTO NG  |  ENGINEERING HANDOVER"
    section.header.paragraphs[0].style = doc.styles["Caption"]
    footer = section.footer.paragraphs[0]; footer.alignment = 2
    footer.add_run("Carto NG technical specification  •  ")
    field = OxmlElement("w:fldSimple"); field.set(qn("w:instr"), "PAGE"); footer._p.append(field)
    doc.core_properties.title = "Carto NG — Technical Specification and Engineering Handover"
    doc.core_properties.subject = "End-to-end workflow, worksheet construction and business convention dependencies"
    doc.core_properties.author = "Carto project"
    doc.add_paragraph("CARTO NG", "Title")
    doc.add_paragraph("Technical Specification\nand Engineering Handover", "Subtitle")
    doc.add_paragraph("24 November 2026  |  Source baseline 30733ec")
    doc.add_paragraph("Implementation-based reference for maintainers and policy reviewers.")
    doc.add_paragraph("Includes every Excel worksheet family, end-to-end execution, naming dependencies, operations and maintenance checks.")
    doc.add_paragraph("Evidence: source inspection and small, fully stubbed normal, streaming and network-zone runs. No production PCE or SMTP operation is implied.")
    doc.add_page_break(); p = doc.add_heading("Contents", 1); add_bookmark(p, "contents", 1)
    doc.add_paragraph("Click a chapter to navigate. Use Word's Navigation Pane for subsection headings. This contents section is already populated and requires no field refresh.")
    for index, name in enumerate(CHAPTERS, 1):
        path = ROOT / name
        title = next(l[2:] for l in path.read_text().splitlines() if l.startswith("# "))
        p = doc.add_paragraph(); p.paragraph_format.space_after = Pt(4)
        hyperlink(p, f"{index:02d}  {title}", bookmark_name(path), True)
    ident = 2
    for name in CHAPTERS: ident = render_chapter(doc, ROOT / name, ident)
    doc.save(OUTPUT)
    print(f"Built {OUTPUT} ({len(CHAPTERS)} chapters)")


if __name__ == "__main__":
    build()
