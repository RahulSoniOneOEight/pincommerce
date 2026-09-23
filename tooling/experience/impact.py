from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def affected_clients(root:Path, pattern_id:str)->dict[str,Any]:
    affected=[]
    projects=root/"client-projects"
    if not projects.exists():
        return {"pattern":pattern_id,"affected":[]}
    for project in projects.iterdir():
        selection=project/"experience"/"design"/"selection.yaml"
        if not selection.exists():
            continue
        value=yaml.safe_load(selection.read_text(encoding="utf-8"))
        for pattern in value.get("patterns",[]):
            if pattern.get("pattern")==pattern_id:
                affected.append({
                    "client_id":project.name,
                    "selection_id":value.get("selection_id"),
                    "selected":pattern.get("selected",{}),
                })
                break
    return {"pattern":pattern_id,"affected":affected,"count":len(affected)}
