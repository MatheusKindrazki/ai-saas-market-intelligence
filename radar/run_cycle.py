"""Single CLI entry point for incremental evidence-first cycles."""
from __future__ import annotations
import argparse
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
SOURCES={x.family:x for x in (RedditSource,HackerNewsSource,GitHubSource,StackExchangeSource,ForumsSource,ReviewsSource,WebSearchSource,XCuratedSource)}
def collect(db: Database, *, families: list[str]|None=None, since: str|None=None, query: str="manual workflow expensive software alternative") -> dict[str,dict]:
    run_id=start(db,"collect"); summary={}
    for family in families or list(SOURCES):
        try:
            signals=SOURCES[family](limit=20).collect(query,since=since); inserted=sum(db.upsert_signal(s) for s in signals)
            summary[family]={"attempted":len(signals),"collected":inserted,"errors":0}
        except Exception as exc:
            db.add_error(__import__('radar.models',fromlist=['SignalError']).SignalError(family,run_id,str(exc),datetime.now(timezone.utc).isoformat()))
            summary[family]={"attempted":0,"collected":0,"errors":1,"error":str(exc)}
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
    try:
        if a.command in {"collect","full"}: details["collect"]=collect(db,families=a.families.split(",") if a.families else None,since=a.since)
        if a.command in {"mine","full"}:
            run=start(db,"mine"); made=mine(db,GLMClient(),run);finish(db,run,True,{"pains":len(made)});details["mine"]=len(made)
        if a.command in {"score","full"}: details["score"]=score_pains(db)
        if a.command in {"report","full"}: details["report"]=str(emit_cycle(__import__('pathlib').Path("reports"),db))
    except Exception as exc:
        print(f"hard failure: {exc}"); raise SystemExit(1)
    print("coverage summary: "+str(details))
if __name__=="__main__": main()
