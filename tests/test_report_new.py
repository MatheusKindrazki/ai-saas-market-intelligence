import json

from radar.db import Database
from radar.models import CoverageEntry, Pain, Thesis
from radar.report import emit, emit_cycle


def test_report_is_schema_validated(tmp_path):
    path=emit(tmp_path,[{'source':'reddit'}],[])
    assert json.loads(path.read_text())['schema_version']=='1'


def _pain(suffix: str, text: str, classified_at: str) -> Pain:
    return Pain(f"pain-{suffix}",f"signal-{suffix}",text,"Ops teams","weekly reporting","manual weekly reporting","weekly","hours lost","spreadsheets","budget approved","none","too slow",
                ({"quote":text,"url":f"https://evidence.test/{suffix}","verified":True},),(text,),(),"A","en",classified_at,"test")


def _thesis(suffix: str, cycle_date: str) -> Thesis:
    return Thesis(f"thesis-{suffix}",f"run-{suffix}",f"Recommendation for {cycle_date}","Ops teams","offer","$99/month","mvp","concierge",(),(),(),"A",f"{cycle_date}T10:00:00+00:00",cycle_date)


def _coverage(run_id: str, ts: str) -> CoverageEntry:
    return CoverageEntry(run_id,"hackernews","hackernews",3,2,0,"",ts,"",ts,())


def _two_cycle_db(tmp_path) -> Database:
    db=Database(tmp_path/"radar.db")
    db.add_pain(_pain("a","Cycle A manual spreadsheet pain","2026-08-10T09:00:00+00:00"))
    db.add_thesis(_thesis("a","2026-08-10")); db.add_coverage(_coverage("run-a","2026-08-10T09:30:00+00:00"))
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


def test_emit_cycle_window_days_widens_the_lookback(tmp_path):
    report=json.loads(emit_cycle(tmp_path/"reports",_two_cycle_db(tmp_path),"2026-08-16",window_days=7).read_text())

    assert sorted(thesis["cycle_date"] for thesis in report["theses"]) == ["2026-08-10","2026-08-16"]
    assert len(report["evidence"]) == 2
