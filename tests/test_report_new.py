import json
from dataclasses import replace

from radar.db import Database
from radar.models import CoverageEntry, Pain, RawSignal, RunRecord, Thesis
from radar.report import emit, emit_cycle


def test_report_is_schema_validated(tmp_path):
    path=emit(tmp_path,[{'source':'reddit'}],[])
    assert json.loads(path.read_text())['schema_version']=='1'


def _signal(suffix: str, text: str) -> RawSignal:
    """The source a pain's quotes are checked against; reports drop quotes it no longer contains."""
    return RawSignal(f"signal-{suffix}","reddit","reddit",suffix,f"https://evidence.test/{suffix}","t",
                     f"Honestly, {text} and nobody owns it.",None,None,"2026-08-16","q","en","c"*64)


def _pain(suffix: str, text: str, classified_at: str) -> Pain:
    return Pain(f"pain-{suffix}",f"signal-{suffix}",text,"Ops teams","weekly reporting","manual weekly reporting","weekly","hours lost","spreadsheets","budget approved","none","too slow",
                ({"quote":text,"url":f"https://evidence.test/{suffix}","verified":True},),(text,),(),"A","en",classified_at,"test")


def _thesis(suffix: str, cycle_date: str) -> Thesis:
    return Thesis(f"thesis-{suffix}",f"run-{suffix}",f"Recommendation for {cycle_date}","Ops teams","offer","$99/month","mvp","concierge",(),(),(),"A",f"{cycle_date}T10:00:00+00:00",cycle_date)


def _coverage(run_id: str, ts: str) -> CoverageEntry:
    return CoverageEntry(run_id,"hackernews","hackernews",3,2,0,"",ts,"",ts,())


def _deep_run(db: Database, run_id: str, started_at: str, status: str="ok") -> None:
    db.start_run(RunRecord(run_id,"deep",started_at,None,"running",{}))
    db.finish_run(run_id,status,{},started_at)


def _two_cycle_db(tmp_path) -> Database:
    db=Database(tmp_path/"radar.db")
    db.upsert_signal(_signal("a","Cycle A manual spreadsheet pain"))
    db.add_pain(_pain("a","Cycle A manual spreadsheet pain","2026-08-10T09:00:00+00:00"))
    db.add_thesis(_thesis("a","2026-08-10")); db.add_coverage(_coverage("run-a","2026-08-10T09:30:00+00:00"))
    db.upsert_signal(_signal("b","Cycle B manual spreadsheet pain"))
    db.add_pain(_pain("b","Cycle B manual spreadsheet pain","2026-08-16T09:00:00+00:00"))
    db.add_thesis(_thesis("b","2026-08-16")); db.add_coverage(_coverage("run-b","2026-08-16T09:30:00+00:00"))
    return db


def test_emit_cycle_reports_only_the_requested_cycle(tmp_path):
    """A later daily report used to republish every earlier cycle's thesis and pains."""
    path=emit_cycle(tmp_path/"reports",_two_cycle_db(tmp_path),"2026-08-16")
    report=json.loads(path.read_text())

    assert path.parent.name == "cycle-2026-08-16"
    assert [thesis["cycle_date"] for thesis in report["theses"]] == ["2026-08-16"]
    assert [item["pain"] for item in report["evidence"]] == ["Cycle B manual spreadsheet pain"]
    assert {entry["run_id"] for entry in report["coverage"]} == {"run-b"}
    assert "Cycle A" not in (path.parent/"dossier.md").read_text()
    assert "Recommendation for 2026-08-16" in (path.parent/"thesis.md").read_text()
    assert json.loads((path.parent/"coverage.json").read_text())[0]["run_id"] == "run-b"


def test_emit_cycle_for_an_earlier_cycle_excludes_later_data(tmp_path):
    report=json.loads(emit_cycle(tmp_path/"reports",_two_cycle_db(tmp_path),"2026-08-10").read_text())

    assert [thesis["cycle_date"] for thesis in report["theses"]] == ["2026-08-10"]
    assert [item["pain"] for item in report["evidence"]] == ["Cycle A manual spreadsheet pain"]
    assert {entry["run_id"] for entry in report["coverage"]} == {"run-a"}


def test_emit_cycle_coverage_keeps_the_latest_run_only(tmp_path):
    db=Database(tmp_path/"radar.db")
    db.add_coverage(_coverage("run-early","2026-08-16T02:00:00+00:00"))
    db.add_coverage(_coverage("run-late","2026-08-16T20:00:00+00:00"))

    report=json.loads(emit_cycle(tmp_path/"reports",db,"2026-08-16").read_text())

    assert {entry["run_id"] for entry in report["coverage"]} == {"run-late"}


def test_emit_cycle_with_no_data_in_window_is_empty_but_valid(tmp_path):
    path=emit_cycle(tmp_path/"reports",_two_cycle_db(tmp_path),"2026-08-01")
    report=json.loads(path.read_text())

    assert (report["coverage"],report["theses"],report["evidence"]) == ([],[],[])
    assert "No thesis clears the bar this cycle." in (path.parent/"thesis.md").read_text()


def test_emit_cycle_keeps_only_the_latest_thesis_of_a_retried_cycle(tmp_path):
    """Deep retried on the same date used to publish every attempt; the contract is one per cycle."""
    db=Database(tmp_path/"radar.db")
    db.add_thesis(replace(_thesis("first","2026-08-16"),recommendation="First attempt",created_at="2026-08-16T10:00:00+00:00"))
    db.add_thesis(replace(_thesis("second","2026-08-16"),recommendation="Second attempt",created_at="2026-08-16T18:00:00+00:00"))

    path=emit_cycle(tmp_path/"reports",db,"2026-08-16")
    report=json.loads(path.read_text())

    assert [thesis["recommendation"] for thesis in report["theses"]] == ["Second attempt"]
    assert "Second attempt" in (path.parent/"thesis.md").read_text()


def test_emit_cycle_window_days_widens_the_lookback(tmp_path):
    report=json.loads(emit_cycle(tmp_path/"reports",_two_cycle_db(tmp_path),"2026-08-16",window_days=7).read_text())

    assert sorted(thesis["cycle_date"] for thesis in report["theses"]) == ["2026-08-10","2026-08-16"]
    assert len(report["evidence"]) == 2


def test_emit_cycle_drops_a_thesis_the_latest_deep_run_rejected(tmp_path):
    """A later deep run that rejects every candidate used to republish the morning's WATCH thesis."""
    db=Database(tmp_path/"radar.db")
    _deep_run(db,"run-morning","2026-08-16T09:00:00+00:00")
    db.add_thesis(replace(_thesis("morning","2026-08-16"),cycle_id="run-morning",created_at="2026-08-16T09:30:00+00:00"))
    _deep_run(db,"run-evening","2026-08-16T20:00:00+00:00")  # rejected every candidate: no thesis persisted

    path=emit_cycle(tmp_path/"reports",db,"2026-08-16")
    report=json.loads(path.read_text())

    assert report["theses"] == []
    assert "No thesis clears the bar this cycle." in (path.parent/"thesis.md").read_text()


def test_emit_cycle_keeps_the_thesis_of_the_latest_deep_run(tmp_path):
    db=Database(tmp_path/"radar.db")
    _deep_run(db,"run-first","2026-08-16T09:00:00+00:00")
    db.add_thesis(replace(_thesis("first","2026-08-16"),cycle_id="run-first",recommendation="First attempt",created_at="2026-08-16T09:30:00+00:00"))
    _deep_run(db,"run-second","2026-08-16T20:00:00+00:00")
    db.add_thesis(replace(_thesis("second","2026-08-16"),cycle_id="run-second",recommendation="Second attempt",created_at="2026-08-16T20:30:00+00:00"))

    path=emit_cycle(tmp_path/"reports",db,"2026-08-16")
    report=json.loads(path.read_text())

    assert [thesis["recommendation"] for thesis in report["theses"]] == ["Second attempt"]
    assert "Second attempt" in (path.parent/"thesis.md").read_text()


def test_emit_cycle_ignores_a_failed_deep_run_after_a_thesis(tmp_path):
    """Only successful deep runs decide the cycle's outcome; a crashed retry erases nothing."""
    db=Database(tmp_path/"radar.db")
    _deep_run(db,"run-ok","2026-08-16T09:00:00+00:00")
    db.add_thesis(replace(_thesis("ok","2026-08-16"),cycle_id="run-ok",created_at="2026-08-16T09:30:00+00:00"))
    _deep_run(db,"run-crashed","2026-08-16T20:00:00+00:00",status="error")

    report=json.loads(emit_cycle(tmp_path/"reports",db,"2026-08-16").read_text())

    assert [thesis["cycle_id"] for thesis in report["theses"]] == ["run-ok"]


def _rewrite_signal(db: Database, signal_id: str, body: str) -> None:
    db.connection.execute("UPDATE signals SET body=? WHERE id=?",(body,signal_id)); db.connection.commit()


def test_emit_cycle_omits_a_pain_whose_quote_left_its_signal(tmp_path):
    """Rows classified before the edit are stale: the quote no longer occurs in the stored body."""
    db=_two_cycle_db(tmp_path)
    _rewrite_signal(db,"signal-b","The author rewrote this post and nothing of the old text is left.")

    path=emit_cycle(tmp_path/"reports",db,"2026-08-16")
    report=json.loads(path.read_text())
    dossier=(path.parent/"dossier.md").read_text()

    assert report["evidence"] == []
    assert "Cycle B manual spreadsheet pain" not in dossier
    assert "Cycle B manual spreadsheet pain" not in path.read_text()


def test_emit_cycle_keeps_a_pain_whose_quote_still_occurs_in_its_signal(tmp_path):
    """The filter is defensive, not destructive: verifiable evidence still reaches both artifacts."""
    path=emit_cycle(tmp_path/"reports",_two_cycle_db(tmp_path),"2026-08-16")

    assert [item["pain"] for item in json.loads(path.read_text())["evidence"]] == ["Cycle B manual spreadsheet pain"]
    assert "Cycle B manual spreadsheet pain" in (path.parent/"dossier.md").read_text()


def test_emit_cycle_omits_a_pain_whose_signal_row_is_gone(tmp_path):
    """No source text to check against is not a pass: an unverifiable citation is not evidence."""
    db=_two_cycle_db(tmp_path)
    db.connection.execute("DELETE FROM signals WHERE id='signal-b'"); db.connection.commit()

    path=emit_cycle(tmp_path/"reports",db,"2026-08-16")

    assert json.loads(path.read_text())["evidence"] == []
    assert "Cycle B manual spreadsheet pain" not in (path.parent/"dossier.md").read_text()


def test_emit_cycle_stale_pain_is_dropped_from_the_rejected_section_too(tmp_path):
    """The dossier's rejected list quotes nothing, but naming a stale pain still republishes it."""
    db=_two_cycle_db(tmp_path)
    db.add_pain(_pain("noise","Wizard mana potion grind","2026-08-16T09:00:00+00:00"))
    _rewrite_signal(db,"signal-b","The author rewrote this post and nothing of the old text is left.")

    path=emit_cycle(tmp_path/"reports",db,"2026-08-16")
    dossier=(path.parent/"dossier.md").read_text()

    assert "Cycle B" not in dossier
    assert "Wizard mana potion grind" not in dossier  # signal-noise was never collected


def test_emit_cycle_window_keeps_earlier_dates_when_the_latest_date_has_no_thesis(tmp_path):
    """A 7-day dossier must not lose Monday's valid thesis because Sunday's deep run rejected all."""
    db=Database(tmp_path/"radar.db")
    _deep_run(db,"run-a","2026-08-10T09:00:00+00:00")
    db.add_thesis(replace(_thesis("a","2026-08-10"),cycle_id="run-a",created_at="2026-08-10T09:30:00+00:00"))
    _deep_run(db,"run-b","2026-08-16T09:00:00+00:00")
    db.add_thesis(replace(_thesis("b","2026-08-16"),cycle_id="run-b",created_at="2026-08-16T09:30:00+00:00"))
    _deep_run(db,"run-b-retry","2026-08-16T20:00:00+00:00")  # rejected every candidate

    report=json.loads(emit_cycle(tmp_path/"reports",db,"2026-08-16",window_days=7).read_text())

    assert [thesis["cycle_date"] for thesis in report["theses"]] == ["2026-08-10"]
    assert [thesis["cycle_id"] for thesis in report["theses"]] == ["run-a"]
