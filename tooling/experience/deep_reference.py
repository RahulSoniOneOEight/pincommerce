from __future__ import annotations

from pathlib import Path
from typing import Any
import re
import yaml

ROOT=Path(__file__).resolve().parents[2]

class DeepReferenceError(RuntimeError): pass

def _load(path:Path)->dict[str,Any]:
    if not path.exists(): raise DeepReferenceError(f"Missing reference input: {path}")
    value=yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(value,dict): raise DeepReferenceError(f"Expected mapping: {path}")
    return value

def _name(value:Any,fallback:str)->str:
    if isinstance(value,str): return value
    if isinstance(value,dict): return str(value.get("name") or value.get("id") or fallback)
    return fallback

def extract(record:dict[str,Any])->dict[str,Any]:
    components=[]
    for i,c in enumerate(record.get("components",[]) or [],1):
        components.append({
            "id":str(c.get("id") if isinstance(c,dict) and c.get("id") else f"component-{i}"),
            "name":_name(c,f"component-{i}"),
            "kind":str(c.get("type") if isinstance(c,dict) and c.get("type") else "component"),
            "variants":list(c.get("variants",[]) if isinstance(c,dict) else []),
            "evidence":c if isinstance(c,dict) else {"name":str(c)},
        })
    patterns=[]
    for i,p in enumerate(record.get("patterns",[]) or [],1):
        patterns.append({"id":str(p.get("id") if isinstance(p,dict) and p.get("id") else f"pattern-{i}"),"name":_name(p,f"pattern-{i}"),"evidence":p})
    notes=" ".join(str(x) for x in record.get("notes",[]) or [])
    inferred_nav=[]
    for token in ("header","sidebar","bottom nav","tabs","mega-nav","drawer","breadcrumb"):
        if re.search(re.escape(token),notes,re.I): inferred_nav.append(token)
    return {
        "source_id":record.get("source_id"),
        "source_type":record.get("type"),
        "provenance":record.get("provenance",{}),
        "components":components,
        "patterns":patterns,
        "tokens":record.get("tokens",{}),
        "colors":record.get("colors",{}),
        "typography":record.get("typography",{}),
        "spacing":record.get("spacing",{}),
        "radii":record.get("radii",{}),
        "assets":record.get("assets",[]),
        "navigation":inferred_nav,
        "status":"extracted" if components or patterns or record.get("tokens") or record.get("colors") else "insufficient-evidence",
    }

def analyze_client(client_id:str,root:Path=ROOT)->dict[str,Any]:
    p=root/"client-projects"/client_id
    src=p/"experience"/"design"/"sources"
    if not src.exists(): raise DeepReferenceError("No normalized reference sources directory")
    analyses=[]
    for path in sorted(list(src.glob("*.yaml"))+list(src.glob("*.yml"))):
        analyses.append(extract(_load(path)))
    blockers=[x.get("source_id") or "unknown" for x in analyses if x["status"]!="extracted"]
    return {"client_id":client_id,"sources":analyses,"blockers":blockers,"status":"ready" if analyses and not blockers else "blocked"}
