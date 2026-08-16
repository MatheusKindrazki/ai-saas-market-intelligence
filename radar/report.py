from __future__ import annotations
import json
from datetime import date
from pathlib import Path
from .schema_check import validate
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

def emit_cycle(root: Path, db, cycle_date: str|None=None) -> Path:
    """Write the four reviewable cycle artifacts from persisted evidence."""
    directory=root/f"cycle-{cycle_date or date.today().isoformat()}"; directory.mkdir(parents=True,exist_ok=True)
    coverage=[dict(row) for row in db.connection.execute("SELECT * FROM coverage ORDER BY ts")]
    pains=db.pains(); theses=[dict(row) for row in db.connection.execute("SELECT * FROM theses ORDER BY created_at DESC")]
    evidence=[{"pain_id":p.id,"pain":p.pain,"icp":p.icp,"quotes":list(p.quotes),"confidence":p.confidence} for p in pains]
    report={"schema_version":"1","coverage":coverage,"theses":theses,"evidence":evidence}
    validate(report,SCHEMA); (directory/"report.json").write_text(json.dumps(report,indent=2,sort_keys=True))
    (directory/"coverage.json").write_text(json.dumps(coverage,indent=2,sort_keys=True))
    lines=["# Opportunity dossier", "", "| Pain | ICP | Evidence |", "|---|---|---|"]
    for p in pains:
        quote=p.quotes[0] if p.quotes else {}; lines.append(f"| {p.pain} | {p.icp} | {quote.get('quote','')} ([source]({quote.get('url','')})) |")
    (directory/"dossier.md").write_text("\n".join(lines)+"\n")
    thesis=theses[0] if theses else None
    text="# Recommended thesis\n\n"+(thesis.get("recommendation") if thesis else "No thesis clears the bar this cycle.")
    if thesis: text += f"\n\nConfidence: {thesis.get('confidence','D')}"
    (directory/"thesis.md").write_text(text+"\n")
    return directory/"report.json"
