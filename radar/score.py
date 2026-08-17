from __future__ import annotations
CORE=("severity","recurrence","willingness_to_pay","market_access","speed_to_value")
def score(dimensions: dict[str,float], reasons: list[str], wtp_quotes: list[str], penalties: list[str]=[]) -> dict[str,object]:
    d=dict(dimensions)
    if not wtp_quotes: d["willingness_to_pay"]=min(2,d.get("willingness_to_pay",0))
    total=sum(d.get(k,0) for k in CORE)-2*len(penalties)
    return {"dimensions":d,"total":max(0,round(total,2)),"verdict":"include" if total>=15 else "exclude","reasons":reasons+penalties}
