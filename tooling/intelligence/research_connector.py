from __future__ import annotations

import hashlib
import os
import re
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any, Callable

class ResearchConnectorError(RuntimeError): pass

class _ResearchParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.title=""
        self._in_title=False
        self.headings:list[str]=[]
        self._capture_heading: str|None=None
        self._buf:list[str]=[]
        self.text:list[str]=[]
    def handle_starttag(self, tag:str, attrs:list[tuple[str,str|None]])->None:
        if tag=="title": self._in_title=True
        if tag in {"h1","h2","h3"}:
            self._capture_heading=tag; self._buf=[]
    def handle_endtag(self, tag:str)->None:
        if tag=="title": self._in_title=False
        if self._capture_heading==tag:
            value=" ".join(x for x in self._buf if x).strip()
            if value: self.headings.append(value)
            self._capture_heading=None; self._buf=[]
    def handle_data(self,data:str)->None:
        value=" ".join(data.split())
        if not value: return
        if self._in_title: self.title=(self.title+" "+value).strip()
        if self._capture_heading: self._buf.append(value)
        if len(value)>=20: self.text.append(value)

def capture(url:str, *, source_id:str, publisher:str|None=None, evidence_terms:list[str]|None=None, opener:Callable[...,Any]=urllib.request.urlopen)->dict[str,Any]:
    req=urllib.request.Request(url,headers={"User-Agent":"PinCommerce-Research/1.0"})
    with opener(req,timeout=30) as response:
        body=response.read()
        content_type=response.headers.get("Content-Type","")
    digest="sha256:"+hashlib.sha256(body).hexdigest()
    text=body.decode("utf-8",errors="replace")
    parser=_ResearchParser(); parser.feed(text)
    corpus=" ".join([parser.title,*parser.headings,*parser.text[:500]])
    matched=[]
    for term in evidence_terms or []:
        if re.search(r"\b"+re.escape(term)+r"\b",corpus,re.I): matched.append(term)
    return {
        "id":source_id,
        "ref":url,
        "publisher":publisher,
        "captured_at":datetime.now(timezone.utc).isoformat(),
        "kind":"web-research",
        "content_type":content_type,
        "content_hash":digest,
        "title":parser.title,
        "headings":parser.headings[:50],
        "evidence":matched,
        "excerpt":" ".join(parser.text[:20])[:4000],
    }
