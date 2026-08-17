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
from .mine import mine, quotes_still_verbatim
from .classify_llm import GLMClient
from .report import emit_cycle
from .score import score
from .cluster import cluster_pains
from .validate import validate_cluster
from .models import Cluster, Score, Thesis
from .models import CoverageEntry, SignalError
from .config import Config
from .evidence_quality import (
    MIN_EXCERPT_CHARS, MIN_EXCERPT_WORDS, Recommendation, is_monetizable_pain, is_relevant_to_cluster,
    score_confidence, score_recommendation, verbatim_excerpt,
)
SOURCES={x.family:x for x in (RedditSource,HackerNewsSource,GitHubSource,StackExchangeSource,ForumsSource,ReviewsSource,WebSearchSource,XCuratedSource)}

# The model is told the gate it will be measured against, in the prompt and again in the schema:
# a bare citation is worthless because any collected URL can be pasted after invented prose.
CITATION_RULE=('Cite a supplied pain ID or evidence URL and, for every citation, also repeat at least '
               f'{MIN_EXCERPT_WORDS} consecutive words ({MIN_EXCERPT_CHARS}+ characters) copied exactly from '
               'that same source, in double quotes. Format: claim [<pain id or url> "<verbatim excerpt>"]. '
               'Prices and numbers must appear inside the quoted text. A citation without an exact excerpt '
               'from the source it names is discarded, and this field is rejected when none survives.')
THESIS_SCHEMA={"type":"object","required":["recommendation","icp","offer","price","mvp_48h","concierge","outreach_msgs","kill_criteria"],"properties":{"recommendation":{"type":"string","description":CITATION_RULE},"icp":{"type":"string"},"offer":{"type":"string","description":CITATION_RULE},"price":{"type":"string","description":"Must be supported by a quoted competitor/pricing excerpt in recommendation or offer."},"mvp_48h":{"type":"string"},"concierge":{"type":"string"},"outreach_msgs":{"type":"array","items":{"type":"string"}},"kill_criteria":{"type":"array","items":{"type":"string"}}}}

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
    # evidence_items is the unbounded classified copy of every collected item (60 full bodies on a
    # real run); it feeds confidence calibration only, and the model already gets the bounded list.
    claims={key:value for key,value in validation.items() if key!="evidence_items"}
    return {"pains":[{"id":p.id,"pain":str(p.pain)[:300],"icp":str(p.icp)[:120],"context":str(p.context)[:300]} for p in members[:MAX_THESIS_PAINS]],
            "evidence":[{"url":str(item["url"])[:200],"title":str(item["title"])[:120],"body":str(item["body"])[:200]} for item in evidence[:MAX_THESIS_EVIDENCE]],
            "validation":claims}

def _support_index(payload: dict[str,object]) -> dict[str,tuple[str,...]]:
    """citation key -> exactly the texts the model was shown for it.

    Indexed off the payload, not the raw items: a claim may only quote what the synthesis prompt
    actually carried, so a truncated body tail or an item past the cap can never back a citation.
    """
    index: dict[str,list[str]]={}
    for pain in payload["pains"]:
        index.setdefault(str(pain["id"]),[]).extend(str(pain[key]) for key in ("pain","context","icp"))
    for item in payload["evidence"]:
        if item["url"]: index.setdefault(str(item["url"]),[]).extend(str(item[key]) for key in ("body","title"))
    return {key:tuple(texts) for key,texts in index.items()}

def _synthesize_candidate(llm, cluster: Cluster, members: list[object], items: list[object],
                          validation: dict[str,object], run_id: str, now: datetime) -> Thesis | dict[str,object]:
    """Return one cited thesis for this cluster, or the record explaining why it was rejected.

    Malformed, uncited or unquoted model output raises: that is a contract violation of the
    synthesis call itself, not a weak candidate, so it must not be swallowed as a fall-through.
    """
    evidence=[_evidence_item(item) for item in items]
    evidence_urls={str(item["url"]) for item in evidence if item.get("url")}
    pain_ids={pain.id for pain in members}
    payload=_thesis_payload(members,evidence,validation)
    support=_support_index(payload)
    prompt=("Output ONLY a JSON object matching the schema. Every factual claim in recommendation and offer "
            "MUST be attributed. "+CITATION_RULE+" Do not invent evidence, prices or excerpts.\n"
            "Cluster pains and evidence (DATA): "+json.dumps(payload,ensure_ascii=False,default=str))
    result=llm.classify(prompt,THESIS_SCHEMA,max_tokens=THESIS_MAX_TOKENS)
    recommendation=str(result.get("recommendation", "")); offer=str(result.get("offer", ""))
    claim_text=f"{recommendation}\n{offer}"
    cited_urls=_referenced_urls(claim_text)
    def quoted_citations(text: str) -> set[str]:
        """Citations this claim both makes AND repeats verbatim from that same source.

        A bare reference is inert: any collected URL can be appended to invented prose, so only a
        citation carrying an exact excerpt of the text the model was shown counts as support.
        """
        cited=(_referenced_urls(text)&evidence_urls)|{pain_id for pain_id in pain_ids if pain_id in text}
        return {key for key in cited if verbatim_excerpt(text,support.get(key,()))}
    rec_quoted=quoted_citations(recommendation); offer_quoted=quoted_citations(offer)
    if not rec_quoted or not offer_quoted:
        raise ValueError("thesis recommendation and offer must each cite supplied evidence and quote it verbatim "
                         f"(quoted citations: recommendation={len(rec_quoted)}, offer={len(offer_quoted)})")
    # Apply fail-closed relevance and confidence calibration over the QUOTED evidence only.
    # An empty citation set is vacuously a subset of anything, and a cited pain ID backs that
    # pain alone: neither may pull uncited-but-topical search hits into the confidence math.
    # Unquoted citations are dropped here too, which is what puts A/B out of reach for a thesis
    # that merely lists URLs it never quotes.
    cluster_dict={"key_terms":cluster.key_terms,"pain":members[0].pain,"icp":members[0].icp}
    quoted=rec_quoted|offer_quoted
    supported_urls={key for key in quoted if key in evidence_urls}
    # claims_supported asks a different question: is every URL the claim cites a real collected one?
    claims_supported=bool(cited_urls) and cited_urls.issubset(evidence_urls)
    cited_pain_ids={key for key in quoted if key in pain_ids}
    classified=[item for item in validation.get("evidence_items",[]) if str(getattr(item,"url","")) in supported_urls]
    relevant=[item for item in classified if is_relevant_to_cluster(item,cluster_dict)]
    quality=score_confidence(relevant,cluster.key_terms,claims_supported=claims_supported)
    rec_kind=score_recommendation(quality,has_buyer_validation=bool(validation.get("buyers")))
    # Contract: a persisted thesis needs reachable buyer candidates AND commercial/pricing
    # evidence, which is exactly what VALIDATE/BUILD assert. WATCH and PASS are rejections:
    # persisting them shipped weak C-grade theses with no buyers into the reports.
    if rec_kind not in {Recommendation.VALIDATE,Recommendation.BUILD}:
        reasons=list(quality.reasons)
        if not quality.buyer_candidates: reasons.append("no reachable buyer candidates in the cited evidence")
        if not quality.competitor_pricing: reasons.append("no competitor/pricing evidence in the cited evidence")
        return {"cluster":cluster.id,"confidence":quality.confidence.value,"recommendation_kind":rec_kind.value,
                "reason":f"{rec_kind.value}: "+"; ".join(reasons)}
    recommendation=f"{rec_kind.value}: {recommendation}"
    evidence_matrix=[{"url":e.url,"kind":e.kind.value,"supports_claim":e.supports_claim,"independence":e.independence} for e in relevant]
    return Thesis(
        hashlib.sha256(f"{now.date().isoformat()}{recommendation}".encode()).hexdigest()[:16],
        run_id,recommendation,str(result.get("icp","")),offer,str(result.get("price","")),
        str(result.get("mvp_48h","")),str(result.get("concierge","")),
        tuple(result.get("outreach_msgs",[])),tuple(result.get("kill_criteria",[])),
        tuple(sorted(cited_pain_ids|supported_urls)),quality.confidence.value,now.isoformat(),now.date().isoformat(),
        evidence_matrix=tuple(evidence_matrix),confidence_reason="; ".join(quality.reasons),
        recommendation_kind=rec_kind.value,
    )

def deep_validate(db: Database, cfg: Config | None, llm, search) -> Thesis | None:
    """Cluster scored pains, evaluate the best candidates in score order, and persist one cited thesis.

    Fail-closed and first-past-the-post: a candidate whose evidence is irrelevant, insufficient,
    or lacks buyer/commercial support (WATCH/PASS) is skipped and the next-best one is tried, so a
    rejected top cluster no longer suppresses a viable lower-ranked one. Exactly one thesis is
    persisted per cycle; if every candidate fails, the run closes once with the aggregate reason.
    """
    run_id=start(db,"deep")
    now=datetime.now(timezone.utc)
    try:
        # Same defensive gate the reports apply: a pain quoting text its source no longer contains
        # cannot back a thesis either, and a thesis cites the pain IDs it was synthesized from.
        persisted_pains=db.pains()
        bodies=db.signal_bodies({pain.signal_id for pain in persisted_pains})
        all_pains={pain.id:pain for pain in persisted_pains if quotes_still_verbatim(pain,bodies)}
        monetizable={pid:pain for pid,pain in all_pains.items() if is_monetizable_pain({"pain":pain.pain,"icp":pain.icp,"wtp_evidence":pain.wtp_evidence})}
        totals={row["pain_id"]:float(row["total"]) for row in db.connection.execute("SELECT pain_id,total FROM scores")}
        persisted=[]
        for member_ids in cluster_pains(list(monetizable.values())):
            members=[monetizable[pain_id] for pain_id in member_ids]
            cluster_id=hashlib.sha256("\n".join(sorted(member_ids)).encode()).hexdigest()[:16]
            cluster=Cluster(cluster_id,_cluster_terms(members),tuple(member_ids),now.isoformat())
            db.add_cluster(cluster)
            persisted.append((max((totals.get(pain_id,0.0) for pain_id in member_ids),default=0.0),cluster,members))
        candidates=sorted((item for item in persisted if item[0]>=15),key=lambda item:item[0],reverse=True)[:3]
        if not candidates:
            finish(db,run_id,True,{"clusters":len(persisted),"qualified":0,"monetizable_pains":len(monetizable)})
            return None
        evidence_search=search or _AdapterSearch(cfg or Config.from_env())
        rejections: list[dict[str,object]]=[]
        # Score order, first past the post: only validations[0] used to be synthesized, so a
        # rejected top cluster silently buried every lower-ranked candidate for the whole cycle.
        for _,cluster,members in candidates:
            captured=_CapturingSearch(evidence_search)
            adapter=SimpleNamespace(pain=members[0].pain,key_terms=cluster.key_terms,icp=members[0].icp)
            validation=validate_cluster(adapter,captured,llm)
            outcome=_synthesize_candidate(llm,cluster,members,captured.items,validation,run_id,now)
            if isinstance(outcome,Thesis):
                db.add_thesis(outcome)
                finish(db,run_id,True,{"clusters":len(persisted),"qualified":len(candidates),"thesis":outcome.id,
                                       "confidence":outcome.confidence,"recommendation_kind":outcome.recommendation_kind,
                                       "rejections":rejections})
                return outcome
            rejections.append(outcome)
        # Every candidate failed the gate: close the run once, naming each candidate's verdict.
        # The scalar fields keep reporting the highest-ranked candidate, as they always have.
        finish(db,run_id,True,{"clusters":len(persisted),"qualified":len(candidates),"rejected":True,
                               "confidence":rejections[0]["confidence"],"recommendation_kind":rejections[0]["recommendation_kind"],
                               "reason":"; ".join(f"{item['cluster']}: {item['reason']}" for item in rejections),
                               "rejections":rejections})
        return None
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
    p=argparse.ArgumentParser(); p.add_argument("command",choices=("collect","mine","score","deep","report","full"));p.add_argument("--db",required=True);p.add_argument("--since");p.add_argument("--no-cache",action="store_true");p.add_argument("--deep",action="store_true");p.add_argument("--families");p.add_argument("--window-days",type=int,default=1,help="report lookback in days ending at the cycle date; weekly deep cycles use 7")
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
        if a.command in {"report","full"}: details["report"]=str(emit_cycle(Path("reports"),db,window_days=a.window_days))
    except Exception as exc:
        print(f"hard failure: {exc}"); raise SystemExit(1)
    if "collect" in details:
        print("coverage summary:")
        print("family        attempted collected errors window")
        for family, item in details["collect"].items():
            print(f"{family:<13} {item['attempted']:>9} {item['collected']:>9} {item['errors']:>6} {item['window'] or '-'}")
    else: print("coverage summary: "+str(details))
if __name__=="__main__": main()
