from __future__ import annotations

import hmac
import os
from typing import Any

ROLES={"viewer":{"view"},"reviewer":{"view","comment","approve-target"},"approver":{"view","comment","approve-target","approve-experience"},"admin":{"view","comment","approve-target","approve-experience","manage"}}

class ReviewAuthError(RuntimeError): pass

def authorize(identity:str,role:str,action:str,token:str|None=None)->dict[str,Any]:
    if role not in ROLES: raise ReviewAuthError("unknown role")
    expected=os.getenv("REVIEW_MODE_WRITE_TOKEN")
    if not expected or not token or not hmac.compare_digest(token,expected):
        raise ReviewAuthError("invalid review credential")
    if action not in ROLES[role]:
        raise ReviewAuthError(f"role {role} cannot {action}")
    if not identity: raise ReviewAuthError("identity required")
    return {"identity":identity,"role":role,"action":action,"authorized":True}
