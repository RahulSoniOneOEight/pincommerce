from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml

ROOT=Path(__file__).resolve().parents[2]


def _rgb(hex_value: str) -> tuple[int,int,int]:
    h=hex_value.lstrip("#")
    return tuple(int(h[i:i+2],16) for i in (0,2,4))


def _lum(hex_value: str) -> float:
    values=[]
    for c in _rgb(hex_value):
        x=c/255
        values.append(x/12.92 if x<=0.03928 else ((x+0.055)/1.055)**2.4)
    return 0.2126*values[0]+0.7152*values[1]+0.0722*values[2]


def contrast(a: str,b: str)->float:
    l1,l2=sorted((_lum(a),_lum(b)),reverse=True)
    return round((l1+0.05)/(l2+0.05),2)


def compile_theme(theme: dict[str,Any]) -> dict[str,Any]:
    roles=dict(theme.get("semantic_roles",{}))
    checks=[]
    pairs=[
        ("content.primary","surface.page",4.5),
        ("content.secondary","surface.page",4.5),
        ("content.inverse","action.primary",4.5),
        ("feedback.error","surface.page",4.5),
    ]
    for fg,bg,minimum in pairs:
        if fg in roles and bg in roles:
            ratio=contrast(roles[fg],roles[bg])
            checks.append({"foreground":fg,"background":bg,"ratio":ratio,"minimum":minimum,"status":"pass" if ratio>=minimum else "fail"})
    dark={}
    for key,value in roles.items():
        if key=="surface.page": dark[key]="#111315"
        elif key=="surface.raised": dark[key]="#1B1E21"
        elif key=="surface.interactive": dark[key]="#24282D"
        elif key=="content.primary": dark[key]="#F5F7FA"
        elif key=="content.secondary": dark[key]="#C2C7D0"
        elif key=="content.inverse": dark[key]="#111315"
        else: dark[key]=value
    return {
        "theme_id":theme.get("theme_id"),
        "light":roles,
        "dark":dark,
        "contrast_checks":checks,
        "status":"passed" if checks and all(x["status"]=="pass" for x in checks) else "review",
    }


def main()->int:
    parser=argparse.ArgumentParser(description="Compile semantic theme variants and contrast evidence")
    parser.add_argument("--input",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    theme=yaml.safe_load(args.input.read_text(encoding="utf-8"))
    result=compile_theme(theme)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(yaml.safe_dump(result,sort_keys=False),encoding="utf-8")
    print(args.output)
    return 0 if result["status"]=="passed" else 2


if __name__=="__main__":
    raise SystemExit(main())
