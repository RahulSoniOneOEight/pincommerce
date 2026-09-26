from __future__ import annotations

import csv
import json
import zipfile
from pathlib import Path
from typing import Any
import xml.etree.ElementTree as ET
import yaml

class InputIntelligenceError(RuntimeError):
    pass

def _text_docx(path: Path) -> str:
    with zipfile.ZipFile(path) as zf:
        xml = zf.read("word/document.xml")
    root = ET.fromstring(xml)
    return " ".join(x.text or "" for x in root.iter() if x.tag.endswith("}t"))

def _text_xlsx(path: Path) -> str:
    values: list[str] = []
    with zipfile.ZipFile(path) as zf:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            shared = ["".join(t.text or "" for t in si.iter() if t.tag.endswith("}t")) for si in root]
        for name in sorted(x for x in zf.namelist() if x.startswith("xl/worksheets/sheet") and x.endswith(".xml")):
            root = ET.fromstring(zf.read(name))
            for cell in (x for x in root.iter() if x.tag.endswith("}c")):
                typ = cell.attrib.get("t")
                val = next((x.text for x in cell if x.tag.endswith("}v")), None)
                if val is None:
                    continue
                if typ == "s":
                    try: val = shared[int(val)]
                    except (ValueError, IndexError): pass
                values.append(str(val))
    return "\n".join(values)

def extract_text(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix in {".txt",".md",".html"}:
        return path.read_text(encoding="utf-8", errors="replace")
    if suffix in {".yaml",".yml"}:
        return yaml.safe_dump(yaml.safe_load(path.read_text(encoding="utf-8")), sort_keys=False)
    if suffix == ".json":
        return json.dumps(json.loads(path.read_text(encoding="utf-8")), ensure_ascii=False, indent=2)
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as fh:
            return "\n".join(" | ".join(row) for row in csv.reader(fh))
    if suffix == ".docx":
        return _text_docx(path)
    if suffix == ".xlsx":
        return _text_xlsx(path)
    if suffix == ".pdf":
        try:
            from pypdf import PdfReader
        except ImportError as exc:
            raise InputIntelligenceError("PDF ingestion requires pypdf") from exc
        return "\n".join((page.extract_text() or "") for page in PdfReader(str(path)).pages)
    raise InputIntelligenceError(f"Unsupported input type: {suffix}")

def normalize_statements(source_id: str, text: str) -> dict[str, Any]:
    lines=[x.strip(" \t-*•") for x in text.splitlines() if x.strip()]
    facts=[]; assumptions=[]; unknowns=[]; conflicts=[]
    seen: dict[str,str] = {}
    for i,line in enumerate(lines,1):
        lower=line.lower()
        record={"id":f"{source_id}-{i:04d}","statement":line,"source_ref":source_id}
        if "?" in line or any(k in lower for k in ("tbd","to be decided","unknown","not confirmed")):
            unknowns.append(record); continue
        if any(k in lower for k in ("assume","assumption","proposed","tentative","expected")):
            assumptions.append(record); continue
        key=lower.split(":",1)[0].strip() if ":" in lower else ""
        if key and key in seen and seen[key] != lower:
            conflicts.append({**record,"conflicts_with":seen[key]})
        elif key:
            seen[key]=lower
        facts.append(record)
    return {"facts":facts,"assumptions":assumptions,"unknowns":unknowns,"conflicts":conflicts}

def ingest_files(paths: list[Path]) -> dict[str, Any]:
    aggregate={"facts":[],"assumptions":[],"unknowns":[],"conflicts":[],"sources":[]}
    for path in paths:
        text=extract_text(path)
        source_id=path.name
        normalized=normalize_statements(source_id,text)
        for key in ("facts","assumptions","unknowns","conflicts"):
            aggregate[key].extend(normalized[key])
        aggregate["sources"].append({"id":source_id,"path":str(path),"characters":len(text)})
    aggregate["status"]="normalized"
    return aggregate
