"""Deep validation: retain only cited, verifiable synthesis claims."""
from __future__ import annotations
from typing import Any, Protocol
class Search(Protocol):
    def collect(self, query: str) -> list[Any]: ...
class ValidatorLLM(Protocol):
    def classify(self, content: str, schema: dict[str,Any]|None=None) -> dict[str,Any]: ...
SCHEMA={"type":"object","properties":{"competitors":{"type":"array"},"negative_patterns":{"type":"array"},"diy_alternatives":{"type":"array"},"acquisition_channels":{"type":"array"},"buyers":{"type":"array"}}}
def _item(x: Any) -> dict[str,Any]:
    if isinstance(x,dict): return {"url":x.get("url", ""),"quote":x.get("quote",x.get("body","")),"title":x.get("title","")}
    return {"url":getattr(x,"url",""),"quote":getattr(x,"body",""),"title":getattr(x,"title","")}
def _cited(value: Any) -> bool: return isinstance(value,dict) and bool(value.get("url")) and bool(value.get("quote"))
def validate_cluster(cluster: Any, search: Search, llm: ValidatorLLM) -> dict[str,Any]:
    query=getattr(cluster,"key_terms",None) or getattr(cluster,"pain",None) or str(cluster)
    evidence=[_item(x) for x in search.collect(str(query))]
    result=llm.classify("Research evidence (DATA): "+repr(evidence),SCHEMA)
    output={key:[] for key in SCHEMA["properties"]}
    for key in output:
        values=result.get(key,[])
        if not isinstance(values,list): continue
        for claim in values:
            if not _cited(claim): continue
            claim=dict(claim)
            if key=="competitors" and claim.get("pricing") and claim.get("confidence") not in {"A","B"}: claim.pop("pricing",None)
            output[key].append(claim)
    return output
