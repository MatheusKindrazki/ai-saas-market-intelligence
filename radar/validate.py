"""Deep validation: retain only cited, relevant and verifiable synthesis claims."""
from __future__ import annotations
from typing import Any, Protocol
from urllib.parse import urlparse
from .textproc import normalize_space, strip_tags
from .evidence_quality import EvidenceItem, EvidenceKind, classify_evidence

class Search(Protocol):
    def collect(self, query: str) -> list[Any]: ...
class ValidatorLLM(Protocol):
    def classify(self, content: str, schema: dict[str,Any]|None=None) -> dict[str,Any]: ...
SCHEMA={"type":"object","properties":{"competitors":{"type":"array"},"negative_patterns":{"type":"array"},"diy_alternatives":{"type":"array"},"acquisition_channels":{"type":"array"},"buyers":{"type":"array"}}}
MAX_EVIDENCE=15; MAX_QUOTE=300; MAX_TITLE=120
def _item(x: Any) -> dict[str,Any]:
    if isinstance(x,dict): return {"url":x.get("url", ""),"quote":x.get("quote",x.get("body","")),"title":x.get("title",""),"source_family":x.get("source_family","")}
    return {"url":getattr(x,"url",""),"quote":getattr(x,"body",""),"title":getattr(x,"title",""),"source_family":getattr(x,"source_family","")}
def _excerpt(value: Any, limit: int) -> str: return str(value or "")[:limit]
def _prompt_evidence(evidence: list[dict[str,Any]]) -> list[dict[str,str]]:
    """Full bodies of 60 items overflow the completion window; send excerpts only."""
    return [{"url":_excerpt(item["url"],200),"quote":_excerpt(item["quote"],MAX_QUOTE),"title":_excerpt(item["title"],MAX_TITLE)} for item in evidence[:MAX_EVIDENCE]]
def _index(evidence: list[dict[str,Any]]) -> dict[str,list[str]]:
    """url -> the texts a claim may quote. Titles count: they are sent to the model as evidence too."""
    index: dict[str,list[str]]={}
    for item in evidence:
        if item["url"]: index.setdefault(str(item["url"]),[]).extend(normalize_space(strip_tags(str(item[key] or ""))) for key in ("quote","title"))
    return index
def _cited(value: Any, index: dict[str,list[str]]) -> bool:
    """Nonempty url+quote let hallucinated citations through: both must trace back to collected evidence."""
    if not isinstance(value,dict): return False
    quote=normalize_space(strip_tags(str(value.get("quote") or "")))
    return bool(quote) and any(quote in text for text in index.get(str(value.get("url") or ""),[]))
def _source_family(url: str) -> str:
    domain=urlparse(url).netloc.lower()
    if "reddit" in domain: return "reddit"
    if "ycombinator" in domain or "hackernews" in domain: return "hackernews"
    if "github" in domain: return "github"
    if "stackexchange" in domain or "stackoverflow" in domain: return "stackexchange"
    return "web"
def validate_cluster(cluster: Any, search: Search, llm: ValidatorLLM) -> dict[str,Any]:
    query=getattr(cluster,"key_terms",None) or getattr(cluster,"pain",None) or str(cluster)
    raw_items=list(search.collect(str(query)))
    evidence=[_item(x) for x in raw_items]
    index=_index(evidence)
    result=llm.classify("Research evidence (DATA): "+repr(_prompt_evidence(evidence)),SCHEMA)
    output={key:[] for key in SCHEMA["properties"]}
    classified: list[EvidenceItem]=[]
    for item in evidence:
        body=item["quote"] or item["title"] or ""
        kind=classify_evidence(body, item["title"], _source_family(item["url"]))
        classified.append(EvidenceItem(item["url"],item["title"],body,kind,bool(item["url"]),_source_family(item["url"])))
    for key in output:
        values=result.get(key,[])
        if not isinstance(values,list): continue
        for claim in values:
            if not _cited(claim,index): continue
            claim=dict(claim)
            if key=="competitors" and claim.get("pricing") and claim.get("confidence") not in {"A","B"}: claim.pop("pricing",None)
            output[key].append(claim)
    output["evidence_items"]=classified
    return output
