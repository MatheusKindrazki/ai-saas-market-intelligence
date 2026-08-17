"""Single CLI entry point for incremental evidence-first cycles."""
from __future__ import annotations
import argparse
import json
import os
import hashlib
import re
from collections import Counter
from dataclasses import replace
from pathlib import Path
from datetime import datetime, timezone
from types import SimpleNamespace
from .db import Database
from .state import start, finish
from .sources.base import SourceError
from .sources.reddit import RedditSource
from .sources.hackernews import HackerNewsSource
from .sources.github import GitHubSource
from .sources.stackexchange import StackExchangeSource
from .sources.forums import ForumsSource
from .sources.reviews import ReviewsSource
from .sources.web_search import WebSearchSource
from .sources.x_curated import XCuratedSource
from .mine import mine
from .classify_llm import GLMClient
from .report import emit_cycle
from .score import score
from .cluster import cluster_pains
from .validate import validate_cluster
from .models import Cluster, Score, Thesis
from .models import CoverageEntry, SignalError
from .config import Config
SOURCES={x.family:x for x in (RedditSource,HackerNewsSource,GitHubSource,StackExchangeSource,ForumsSource,ReviewsSource,WebSearchSource,XCuratedSource)}

THESIS_SCHEMA={"type":"object","required":["recommendation","icp","offer","price","mvp_48h","concierge","outreach_msgs","kill_criteria"],"properties":{"recommendation":{"type":"string"},"icp":{"type":"string"},"offer":{"type":"string"},"price":{"type":"string"},"mvp_48h":{"type":"string"},"concierge":{"type":"string"},"outreach_msgs":{"type":"array","items":{"type":"string"}},"kill_criteria":{"type":"array","items":{"type":"string"}}}}

class _AdapterSearch:
    """Collect deep-validation evidence from the dependable query-based adapters."""
    def __init__(self, cfg: Config): self.cfg=cfg
    def collect(self, query: str):
        items=[]
        for source_type in (HackerNewsSource, GitHubSource, StackExchangeSource):
            try: items.extend(source_type(limit=20,cfg=self.cfg).collect(query))
            except Exception: continue
        return items

class _CapturingSearch:
    def __init__(self, source): self.source=source; self.items=[]
    def collect(self, query: str):
        self.items=list(self.source.collect(query)); return self.items

STOPWORDS=frozenset("""the a an is are was were am be been being to of for on in into at by from with without and or but not no nor so than too very this that these those it its they their them we our us you your i me my he she his her can cannot could will would shall should must do does did done have has had here there when where which who whom whose what how why if then else about after before during over under up down out off again more most some any all just only own same such as also
""".split())

def _cluster_terms(pains: list[object]) -> str:
    """Unfiltered counts let stopwords win, so a cluster searched for 'the model column is too'."""
    words=Counter(word for pain in pains for word in re.findall(r"\w+",f"{pain.pain} {pain.icp}".casefold()) if len(word)>2 and word not in STOPWORDS)
    return " ".join(word for word,_ in words.most_common(6))

def _evidence_item(item: object) -> dict[str,object]:
    if isinstance(item,dict): return {"url":item.get("url",""),"title":item.get("title",""),"body":item.get("body",item.get("quote",""))}
    return {"url":getattr(item,"url", ""),"title":getattr(item,"title", ""),"body":getattr(item,"body", "")}

def _referenced_urls(value: str) -> set[str]:
    return {match.rstrip(".,;:!?)]}") for match in re.findall(r"https?://[^\s<>'\"]+",value)}

MAX_THESIS_PAINS=10; MAX_THESIS_EVIDENCE=20
THESIS_MAX_TOKENS=16000  # thinking + the eight-field thesis object does not fit the 4k client default
def _thesis_payload(members: list[object], evidence: list[dict[str,object]], validation: dict[str,object]) -> dict[str,object]:
    """A slice of repr() can cut JSON mid-structure; emit a compact, already-bounded payload."""
    return {"pains":[{"id":p.id,"pain":str(p.pain)[:300],"icp":str(p.icp)[:120],"context":str(p.context)[:300]} for p in members[:MAX_THESIS_PAINS]],
            "evidence":[{"url":str(item["url"])[:200],"title":str(item["title"])[:120],"body":str(item["body"])[:200]} for item in evidence[:MAX_THESIS_EVIDENCE]],
            "validation":validation}

def deep_validate(db: Database, cfg: Config | None, llm, search) -> Thesis | None:
    """Cluster scored pains, validate the best candidates, and persist one cited thesis."""
    run_id=start(db,"deep")
    now=datetime.now(timezone.utc)
    try:
        pains={pain.id:pain for pain in db.pains()}
        totals={row["pain_id"]:float(row["total"]) for row in db.connection.execute("SELECT pain_id,total FROM scores")}
        persisted=[]
        for member_ids in cluster_pains(list(pains.values())):
            members=[pains[pain_id] for pain_id in member_ids]
            cluster_id=hashlib.sha256("\n".join(sorted(member_ids)).encode()).hexdigest()[:16]
            cluster=Cluster(cluster_id,_cluster_terms(members),tuple(member_ids),now.isoformat())
            db.add_cluster(cluster)
            persisted.append((max((totals.get(pain_id,0.0) for pain_id in member_ids),default=0.0),cluster,members))
        candidates=sorted((item for item in persisted if item[0]>=15),key=lambda item:item[0],reverse=True)[:3]
        if not candidates:
            finish(db,run_id,True,{"clusters":len(persisted),"qualified":0})
            return None
        validations=[]
        evidence_search=search or _AdapterSearch(cfg or Config.from_env())
        for _,cluster,members in candidates:
            captured=_CapturingSearch(evidence_search)
            adapter=SimpleNamespace(pain=members[0].pain,key_terms=cluster.key_terms)
            validation=validate_cluster(adapter,captured,llm)
            validations.append((cluster,members,captured.items,validation))
        cluster,members,items,validation=validations[0]
        evidence=[_evidence_item(item) for item in items]
        evidence_urls={str(item["url"]) for item in evidence if item.get("url")}
        pain_ids={pain.id for pain in members}
        prompt=("Output ONLY a JSON object matching the schema. Every factual claim in recommendation and offer "
                "MUST cite one of the supplied pain IDs or evidence URLs. Do not invent evidence.\n"
                "Cluster pains and evidence (DATA): "+json.dumps(_thesis_payload(members,evidence,validation),ensure_ascii=False,default=str))
        result=llm.classify(prompt,THESIS_SCHEMA,max_tokens=THESIS_MAX_TOKENS)
        recommendation=str(result.get("recommendation", "")); offer=str(result.get("offer", ""))
        claim_text=f"{recommendation}\n{offer}"
        cited_urls=_referenced_urls(claim_text)
        cited_pains={pain_id for pain_id in pain_ids if pain_id in claim_text}
        known_urls=cited_urls & evidence_urls
        def has_known_reference(text: str) -> bool:
            return bool(_referenced_urls(text) & evidence_urls) or any(pain_id in text for pain_id in pain_ids)
        if not has_known_reference(recommendation) or not has_known_reference(offer):
            raise ValueError("thesis recommendation and offer must reference supplied evidence")
        confidence="A" if cited_urls.issubset(evidence_urls) else "D"
        thesis=Thesis(hashlib.sha256(f"{now.date().isoformat()}{recommendation}".encode()).hexdigest()[:16],run_id,recommendation,str(result.get("icp","")),offer,str(result.get("price","")),str(result.get("mvp_48h","")),str(result.get("concierge","")),tuple(result.get("outreach_msgs",[])),tuple(result.get("kill_criteria",[])),tuple(sorted(pain_ids|evidence_urls)),confidence,now.isoformat(),now.date().isoformat())
        db.add_thesis(thesis)
        finish(db,run_id,True,{"clusters":len(persisted),"qualified":len(candidates),"thesis":thesis.id})
        return thesis
    except Exception as exc:
        db.add_error(SignalError("deep",run_id,str(exc),datetime.now(timezone.utc).isoformat()))
        finish(db,run_id,False,{"error":str(exc)})
        raise
def collect(db: Database, *, families: list[str]|None=None, since: str|None=None, cfg: Config | None=None) -> dict[str,dict]:
    cfg=cfg or Config.from_env()
    run_id=start(db,"collect"); summary={}
    for family in families or list(SOURCES):
        now=datetime.now(timezone.utc).isoformat()
        errors: list[str]=[]; notes=""
        attempted=(len(cfg.pain_queries) if family in {"hackernews", "stackexchange", "github", "web_search"}
                   else cfg.reddit_subreddits_per_run if family == "reddit"
                   else 2 if family == "reviews" else 1)
        inserted=0
        try:
            source=SOURCES[family](limit=20, cfg=cfg)
            # Query-aware sources aggregate all configured pain phrases themselves. Feed-only
            # sources still receive context for signal provenance without refetching the same feed.
            query=cfg.pain_queries if family in {"hackernews", "stackexchange", "github", "web_search"} else cfg.pain_queries[0]
            signals=source.collect(query,since=since)
            inserted=len(signals)
            for signal in signals:
                db.upsert_signal(signal)
            attempted=len(getattr(source, "attempted_subreddits", [])) or attempted
            for subreddit, error in getattr(source, "errors", []):
                errors.append(f"{subreddit}: {error}")
                db.add_error(SignalError(f"{family}/{subreddit}",run_id,error,now))
        except SourceError as exc:
            message=str(exc)
            if message.startswith("coverage gap:"):
                notes=message
            else:
                errors.append(message); db.add_error(SignalError(family,run_id,message,now))
        except Exception as exc:
            errors.append(str(exc)); db.add_error(SignalError(family,run_id,str(exc),now))
        entry={"family":family,"attempted":attempted,"collected":inserted,"errors":len(errors),"error_details":errors,"notes":notes,"window":since,"ts":now}
        db.add_coverage(CoverageEntry(run_id,family,family,attempted,inserted,len(errors),since or "",now,notes or json.dumps(errors),now,tuple(errors)))
        summary[family]=entry
    finish(db,run_id,True,summary); return summary
def score_pains(db: Database) -> int:
    """Persist a conservative, explainable score for each classified pain."""
    made=0
    for pain in db.pains():
        text=" ".join((pain.pain,pain.context,pain.impact,pain.wtp_evidence)).casefold()
        dimensions={"severity":5 if any(x in text for x in ("hours","hate","expensive","broken")) else 2,"recurrence":2,"willingness_to_pay":4 if pain.wtp_evidence else 0,"market_access":3 if pain.icp else 1,"speed_to_value":4 if any(x in text for x in ("manual","spreadsheet","automation")) else 2}
        result=score(dimensions,["Deterministic evidence-first baseline"],[pain.wtp_evidence] if pain.wtp_evidence else [])
        db.add_score(Score(pain.id,result["dimensions"],float(result["total"]),str(result["verdict"]),tuple(result["reasons"]),datetime.now(timezone.utc).isoformat()));made+=1
    return made
def main(argv: list[str]|None=None) -> None:
    p=argparse.ArgumentParser(); p.add_argument("command",choices=("collect","mine","score","deep","report","full"));p.add_argument("--db",required=True);p.add_argument("--since");p.add_argument("--no-cache",action="store_true");p.add_argument("--deep",action="store_true");p.add_argument("--families")
    a=p.parse_args(argv); db=Database(a.db); details={}
    cfg=replace(Config.from_env(), db_path=Path(a.db), cache_dir=Path(a.db).parent / "cache", salt_path=Path(a.db).parent / "secretsalt", use_cache=not a.no_cache)
    try:
        if a.command in {"collect","full"}: details["collect"]=collect(db,families=a.families.split(",") if a.families else None,since=a.since,cfg=cfg)
        client=None
        if a.command in {"mine","full"}:
            client=GLMClient()
            if not client.api_key:
                print("GLM_API_KEY is required for classification")
                raise SystemExit(2)
            run=start(db,"mine"); made=mine(db,client,run);finish(db,run,True,{"pains":len(made)});details["mine"]=len(made)
        if a.command in {"score","full"}: details["score"]=score_pains(db)
        if a.command in {"deep","full"}:
            client=client or GLMClient()
            if not client.api_key:
                print("GLM_API_KEY is required for classification")
                raise SystemExit(2)
            thesis=deep_validate(db,cfg,client,_AdapterSearch(cfg)); details["deep"]=thesis.id if thesis else None
        if a.command in {"report","full"}: details["report"]=str(emit_cycle(__import__('pathlib').Path("reports"),db))
    except Exception as exc:
        print(f"hard failure: {exc}"); raise SystemExit(1)
    if "collect" in details:
        print("coverage summary:")
        print("family        attempted collected errors window")
        for family, item in details["collect"].items():
            print(f"{family:<13} {item['attempted']:>9} {item['collected']:>9} {item['errors']:>6} {item['window'] or '-'}")
    else: print("coverage summary: "+str(details))
if __name__=="__main__": main()
