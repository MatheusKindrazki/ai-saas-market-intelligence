"""Fail-closed complaint mining with a hard verbatim evidence gate."""
from __future__ import annotations
import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Protocol
from .db import Database
from .models import Pain, RawSignal, SignalError
from .textproc import normalize_space, normalized_contains, strip_tags
PAIN_PHRASES=("i hate","looking for alternative","manual spreadsheet","takes hours","too expensive","wish there was","how do you handle","cancelled because","is there a tool","paying someone to","ódio","planilha manual","procuro alternativa","caro demais","gastar horas","existe alguma ferramenta","busco alternativa","odio","hoja de cálculo","demasiado caro","existe alguna herramienta")
def is_candidate(title: str, body: str) -> bool:
    # "manual <b>spreadsheet</b>" is the same complaint as "manual spreadsheet": match the stripped text.
    return any(x in normalize_space(strip_tags(title+" "+body)) for x in PAIN_PHRASES)
def validate_observed(body: str, observed: list[str]) -> bool:
    return bool(observed) and all(normalized_contains(body,q) for q in observed)

FIELDS=("pain","icp","jtbd","context","frequency","impact","workaround","wtp_evidence","current_solution","dissatisfaction_reason")
class LLM(Protocol):
    def classify(self, content: str, schema: dict[str,Any]|None=None) -> dict[str,Any]: ...
SCHEMA={"type":"object","required":["is_complaint","observed","inference"],"properties":{**{x:{"type":"string"} for x in FIELDS},"is_complaint":{"type":"boolean"},"observed":{"type":"array","items":{"type":"string"}},"inference":{"type":"array","items":{"type":"string"}},"lang":{"type":"string"},"confidence_hint":{"type":"string"}}}
def _value(data: dict[str,Any], field: str) -> str: return str(data.get(field) or "")
def mine_signal(db: Database, signal: RawSignal, llm: LLM, run_id: str|None=None) -> Pain | None:
    if not is_candidate(signal.title, signal.body): return None
    try:
        # The model must see — and quote from — the same tag-free text the verbatim gate checks.
        body=strip_tags(signal.body)
        content="TITLE:\n"+strip_tags(signal.title)+"\nBODY:\n"+body+"\nOutput ONLY a JSON object matching this schema. Quote observed evidence VERBATIM, character-for-character, from the BODY text only."
        result=llm.classify(content,SCHEMA)
        observed=list(result.get("observed") or [])
        if not result.get("is_complaint") or not validate_observed(body,observed):
            raise ValueError("unclassified: missing or non-verbatim observed quote")
        quotes=tuple({"quote":quote,"url":signal.url,"verified":True} for quote in observed)
        pain=Pain(hashlib.sha256((signal.id+"|"+_value(result,"pain")).encode()).hexdigest(),signal.id,*[_value(result,x) for x in FIELDS],quotes,tuple(observed),tuple(map(str,result.get("inference") or [])),"A",str(result.get("lang") or signal.lang),datetime.now(timezone.utc).isoformat(),"glm-5.3")
        db.add_pain(pain); return pain
    except Exception as exc:
        db.add_error(SignalError(signal.source,run_id,str(exc),datetime.now(timezone.utc).isoformat()))
        db.connection.execute("UPDATE signals SET fetch_status='unclassified' WHERE id=?",(signal.id,));db.connection.commit()
        return None
def mine(db: Database, llm: LLM, run_id: str|None=None, retry_failed: bool=False) -> list[Pain]:
    """retry_failed re-attempts signals mine_signal already marked 'unclassified'; off by default
    because the verbatim gate is deterministic — a re-run buys the same rejection for 3x120s of API retries."""
    classified=db.classified_signal_ids()
    def normalize(text: str) -> str: return re.sub(r"[^\w]+", " ", text.casefold()).strip()
    signals=db.signals()
    seen={normalize(signal.body) for signal in signals if signal.id in classified}
    pains=[]
    for signal in signals:
        # The persisted content hash catches exact repeats; this catches cheap formatting-only repeats
        # before spending another model request in the same batch.
        normalized=normalize(signal.body)
        if signal.id in classified or normalized in seen: continue
        if signal.fetch_status=="unclassified" and not retry_failed: continue
        seen.add(normalized)
        if pain:=mine_signal(db,signal,llm,run_id): pains.append(pain)
    return pains
