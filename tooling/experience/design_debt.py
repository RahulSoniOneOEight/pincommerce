from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HEX = re.compile(r"#[0-9A-Fa-f]{6}\b")

SCAN_EXTENSIONS = {".dart",".tsx",".ts",".jsx",".js",".css"}


def scan(root: Path = ROOT) -> dict:
    findings = []
    icon_families = set()
    for base in (root / "packages", root / "apps"):
        if not base.exists():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix not in SCAN_EXTENSIONS:
                continue
            text = path.read_text(encoding="utf-8", errors="ignore")
            if HEX.search(text):
                findings.append({"type":"raw-color","path":str(path.relative_to(root))})
            low = text.lower()
            for family in ("iconoir","lucide","phosphor","materialicons","material_symbols"):
                if family in low:
                    icon_families.add(family)
    if len(icon_families) > 1:
        findings.append({"type":"mixed-icon-families","families":sorted(icon_families)})
    return {
        "finding_count":len(findings),
        "findings":findings,
        "status":"clean" if not findings else "review",
    }


def main() -> int:
    parser=argparse.ArgumentParser(description="Scan UI code for design-system debt")
    parser.add_argument("--root",type=Path,default=ROOT)
    args=parser.parse_args()
    result=scan(args.root)
    import yaml
    print(yaml.safe_dump(result,sort_keys=False))
    return 0


if __name__=="__main__":
    raise SystemExit(main())
