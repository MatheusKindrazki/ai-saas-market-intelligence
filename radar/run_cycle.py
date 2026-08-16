"""Single CLI entry point for incremental evidence-first cycles."""
from __future__ import annotations
import argparse
import json
import os
from dataclasses import replace
from pathlib import Path
from datetime import datetime, timezone
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
from .models import Score
from .models import CoverageEntry, SignalError
from .config import Config
SOURCES={x.family:x for x in (RedditSource,HackerNewsSource,GitHubSource,StackExchangeSource,ForumsSource,ReviewsSource,WebSearchSource,XCuratedSource)}
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
    p=argparse.ArgumentParser(); p.add_argument("command",choices=("collect","mine","score","report","full"));p.add_argument("--db",required=True);p.add_argument("--since");p.add_argument("--no-cache",action="store_true");p.add_argument("--deep",action="store_true");p.add_argument("--families")
    a=p.parse_args(argv); db=Database(a.db); details={}
    cfg=replace(Config.from_env(), db_path=Path(a.db), cache_dir=Path(a.db).parent / "cache", salt_path=Path(a.db).parent / "secretsalt", use_cache=not a.no_cache)
    try:
        if a.command in {"collect","full"}: details["collect"]=collect(db,families=a.families.split(",") if a.families else None,since=a.since,cfg=cfg)
        if a.command in {"mine","full"}:
            client=GLMClient()
            if not client.api_key:
                print("GLM_API_KEY is required for classification")
                raise SystemExit(2)
            run=start(db,"mine"); made=mine(db,client,run);finish(db,run,True,{"pains":len(made)});details["mine"]=len(made)
        if a.command in {"score","full"}: details["score"]=score_pains(db)
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
