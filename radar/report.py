from __future__ import annotations
import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from .schema_check import validate
from .evidence_quality import is_monetizable_pain
from .mine import quotes_still_verbatim
SCHEMA=json.loads((Path(__file__).parent/'schemas'/'report.schema.json').read_text())

def build_report(clusters: list[object], coverage: dict[str, object]) -> dict[str, object]:
    """Compatibility helper for the pre-radar offline prototype tests."""
    return {"schema_version": "1", "coverage": coverage, "clusters": [
        {"evidence": [{"url": s.url, "quote": s.body, "confidence": s.confidence.value}
                       for s in cluster.cluster.signals]} for cluster in clusters]}

def emit(directory: Path, coverage: list[dict], theses: list[dict]) -> Path:
    directory.mkdir(parents=True,exist_ok=True); report={"schema_version":"1","coverage":coverage,"theses":theses}; validate(report,SCHEMA)
    (directory/'report.json').write_text(json.dumps(report,indent=2,sort_keys=True))
    (directory/'coverage.json').write_text(json.dumps(coverage,indent=2))
    (directory/'thesis.md').write_text("# Recommended thesis\n\n"+(theses[0].get('recommendation','No thesis clears the bar this cycle.') if theses else 'No thesis clears the bar this cycle.'))
    (directory/'dossier.md').write_text("# Opportunity dossier\n")
    return directory/'report.json'

def emit_cycle(root: Path, db, cycle_date: str|None=None, window_days: int=1) -> Path:
    """Write the four reviewable cycle artifacts from the evidence persisted in this cycle's window.

    Unscoped reads made every later report republish every earlier cycle's thesis and pains, so the
    window — cycle_date back window_days, in UTC like every persisted timestamp — bounds all three reads.
    Within the window each date reports the thesis of its own latest successful deep run, or none.
    """
    cycle_date=cycle_date or datetime.now(timezone.utc).date().isoformat()
    window=((date.fromisoformat(cycle_date)-timedelta(days=max(window_days,1)-1)).isoformat(),cycle_date)
    directory=root/f"cycle-{cycle_date}"; directory.mkdir(parents=True,exist_ok=True)
    latest=db.connection.execute("SELECT run_id FROM coverage WHERE substr(ts,1,10) BETWEEN ? AND ? ORDER BY ts DESC LIMIT 1",window).fetchone()
    coverage=[dict(row) for row in db.connection.execute("SELECT * FROM coverage WHERE run_id IS ? ORDER BY ts",(latest[0],))] if latest else []
    # Defensive: a pain whose quotes no longer occur in the stored signal body is stale evidence.
    # Content changes invalidate their pains at upsert time, but rows written before that must not
    # be republished either, so every emitted quote is re-checked against the body held right now.
    window_pains=db.pains(*window)
    bodies=db.signal_bodies({pain.signal_id for pain in window_pains})
    pains=[pain for pain in window_pains if quotes_still_verbatim(pain,bodies)]
    latest_thesis: dict[str, dict]={}
    # A date's verdict is the outcome of its latest successful deep run, not its latest thesis row.
    # Picking the newest thesis republished an earlier WATCH/A thesis after a later run rejected
    # every candidate — that run persisted nothing, so the date must report no thesis at all.
    # Each date is resolved on its own so one empty date cannot erase another in a weekly window.
    latest_run=db.latest_deep_runs(*window)
    for row in db.connection.execute("SELECT * FROM theses WHERE cycle_date BETWEEN ? AND ? ORDER BY created_at DESC, rowid DESC",window):
        # theses.cycle_id is the deep run that produced it. Dates with no recorded deep run (data
        # written before runs were tracked) keep the old newest-thesis-wins behaviour.
        run_id=latest_run.get(row["cycle_date"])
        if run_id is not None and row["cycle_id"] != run_id: continue
        thesis=dict(row)
        if thesis.get("quality_json"):
            try: thesis.update(json.loads(thesis["quality_json"]))
            except Exception: pass
        latest_thesis.setdefault(row["cycle_date"],thesis)
    # Newest date first: thesis.md recommends theses[0], which stays the most recent cycle's thesis.
    theses=[latest_thesis[day] for day in sorted(latest_thesis,reverse=True)]
    evidence=[{"pain_id":p.id,"pain":p.pain,"icp":p.icp,"quotes":list(p.quotes),"confidence":p.confidence} for p in pains]
    report={"schema_version":"1","coverage":coverage,"theses":theses,"evidence":evidence}
    validate(report,SCHEMA); (directory/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True))
    (directory/"coverage.json").write_text(json.dumps(coverage,indent=2,sort_keys=True))
    lines=["# Opportunity dossier", "", "| Pain | ICP | Evidence |", "|---|---|---|"]
    for p in pains:
        if is_monetizable_pain({"pain":p.pain,"icp":p.icp,"wtp_evidence":p.wtp_evidence}):
            quote=p.quotes[0] if p.quotes else {}; lines.append(f"| {p.pain} | {p.icp} | {quote.get('quote','')} ([source]({quote.get('url','')})) |")
    lines.extend(["", "## Rejected as non-commercial/noise", ""])
    for p in pains:
        if not is_monetizable_pain({"pain":p.pain,"icp":p.icp,"wtp_evidence":p.wtp_evidence}):
            lines.append(f"- {p.pain} (ICP: {p.icp})")
    (directory/"dossier.md").write_text("\n".join(lines)+"\n")
    thesis=theses[0] if theses else None
    if thesis:
        text=f"# Recommended thesis\n\n{thesis.get('recommendation')}\n\nConfidence: {thesis.get('confidence','D')}\n\nReason: {thesis.get('confidence_reason','')}\n\nEvidence matrix:\n"
        for row in thesis.get("evidence_matrix",[]) or []:
            text += f"- [{row.get('kind')}] {row.get('url')} (independence: {row.get('independence')})\n"
    else:
        text="# Recommended thesis\n\nNo thesis clears the bar this cycle.\n"
    (directory/"thesis.md").write_text(text)
    return directory/"report.json"
