#!/usr/bin/env python3
"""Check documentation coverage, local references and Word navigation structure."""
from __future__ import annotations

import ast
import re
from pathlib import Path
from zipfile import ZipFile
from xml.etree import ElementTree as ET

from build_technical_spec import CHAPTERS, OUTPUT, REPO, ROOT, SYMBOLS

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def check() -> None:
    files = [ROOT / name for name in CHAPTERS]
    assert len(files) == len(set(files)), "Duplicate chapter"
    for path in files:
        text = path.read_text(encoding="utf-8")
        assert len(re.findall(r"^# ", text, re.M)) == 1, f"Expected one chapter title: {path}"
        for target in re.findall(r"\[[^\]]+\]\(([^)]+)\)", text):
            if target.startswith(("http://", "https://")): continue
            dest, _, anchor = target.partition("#")
            resolved = (path.parent / dest).resolve() if dest else path
            assert resolved.is_file(), f"Broken link in {path}: {target}"
            if anchor.startswith("L") and resolved.suffix == ".py":
                assert 0 < int(anchor[1:]) <= len(resolved.read_text().splitlines())
    expected = {
        "Summary", "Workloads", "Rules with umgd app labels", "Processes", "Flow-out", "Flow-in",
        "Service Catalogue", "Scope Applicable Rules", "Ruleset Effectiveness", "Flow-Rule Match",
        "Proposed Rules", "Proposed rules", "Proposed rules1", "Action Plan", "To investigate",
        "Egress IP to investigate", "Ingress IP to investigate",
    }
    index = (ROOT / "worksheets/README.md").read_text()
    for title in expected: assert f"| {title} |" in index, f"Unindexed worksheet: {title}"
    assert len(list((ROOT / "worksheets").glob("[0-9]*.md"))) == len(expected)
    # Discover literal sheet writes and flag new titles for deliberate documentation.
    for source in [REPO / "carto_ng_orchestrator.py", *(REPO / "modules").glob("*.py")]:
        for node in ast.walk(ast.parse(source.read_text())):
            if not isinstance(node, ast.Call): continue
            name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            if name not in {"create_sheet", "to_excel", "append_excel"}: continue
            values = [kw.value for kw in node.keywords if kw.arg in {"title", "sheet_name"}]
            if name == "create_sheet" and node.args: values += [node.args[0]]
            if name == "append_excel" and len(node.args) > 1: values += [node.args[1]]
            for value in values:
                if isinstance(value, ast.Constant) and isinstance(value.value, str):
                    assert value.value in expected, f"Undocumented sheet: {source}: {value.value}"
    for source, names in SYMBOLS.items():
        funcs = {n.name for n in ast.parse((REPO / source).read_text()).body if isinstance(n, ast.FunctionDef)}
        assert set(names) <= funcs, f"Source map drift in {source}"
    with ZipFile(OUTPUT) as package:
        assert package.testzip() is None
        for name in package.namelist():
            if name.endswith((".xml", ".rels")): ET.fromstring(package.read(name))
        document = ET.fromstring(package.read("word/document.xml"))
        bookmarks = {n.get(W + "name") for n in document.iter(W + "bookmarkStart")}
        anchors = [n.get(W + "anchor") for n in document.iter(W + "hyperlink") if n.get(W + "anchor")]
        assert set(anchors) <= bookmarks, "Broken Word internal link"
        assert len(anchors) >= 2 * len(CHAPTERS), "Contents or return links missing"
        styles = [n.get(W + "val") for n in document.iter(W + "pStyle")]
        assert "Heading1" in styles and "Heading2" in styles, "Native headings missing"
        text = " ".join(n.text or "" for n in document.iter(W + "t"))
        for title in expected: assert title in text, f"Word omitted {title}"
        assert "SOURCE_URL" not in text
    print(f"PASS: {len(files)} chapters, {len(expected)} worksheet guides, local/source links, Word XML and {len(anchors)} internal links")


if __name__ == "__main__": check()
