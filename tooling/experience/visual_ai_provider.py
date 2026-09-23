from __future__ import annotations
import base64,json,os,urllib.request
from pathlib import Path
from typing import Any,Callable
from tooling.experience.visual_ai_qa import normalize_review

class VisualAIProviderError(RuntimeError): pass

def review_image(path:Path,*,endpoint:str|None=None,token:str|None=None,provider:str="configured-visual-ai",model:str|None=None,opener:Callable[...,Any]=urllib.request.urlopen)->dict[str,Any]:
    endpoint=endpoint or os.getenv("VISUAL_AI_ENDPOINT"); token=token or os.getenv("VISUAL_AI_TOKEN")
    if not endpoint or not token: raise VisualAIProviderError("VISUAL_AI_ENDPOINT and VISUAL_AI_TOKEN are required")
    image=base64.b64encode(path.read_bytes()).decode("ascii")
    payload=json.dumps({"model":model,"image_base64":image,"task":"Review UI screenshot for hierarchy, consistency, accessibility and usability. Return structured findings."}).encode()
    req=urllib.request.Request(endpoint,data=payload,headers={"Authorization":f"Bearer {token}","Content-Type":"application/json"},method="POST")
    with opener(req,timeout=60) as response: raw=json.loads(response.read().decode("utf-8"))
    review={"provider":provider,"model":model,"screenshot_sha256":raw.get("screenshot_sha256"),"findings":raw.get("findings",[])}
    if not review["screenshot_sha256"]:
        import hashlib
        review["screenshot_sha256"]="sha256:"+hashlib.sha256(path.read_bytes()).hexdigest()
    return normalize_review(review)
