from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from radar.db import Database
from radar.models import Pain, RawSignal
from radar.run_cycle import main


def _signal(suffix: str, text: str) -> RawSignal:
    return RawSignal(f"signal-{suffix}","reddit","reddit",suffix,f"https://evidence.test/{suffix}","t",
                     f"Honestly, {text} and nobody owns it.",None,None,"2026-08-16","q","en","c"*64)


def _pain(suffix: str, text: str, classified_at: str) -> Pain:
    return Pain(f"pain-{suffix}",f"signal-{suffix}",text,"Ops teams","weekly reporting","manual weekly reporting","weekly","hours lost","spreadsheets","budget approved","none","too slow",
                ({"quote":text,"url":f"https://evidence.test/{suffix}","verified":True},),(text,),(),"A","en",classified_at,"test")


def _week_db(tmp_path) -> tuple[Database, str]:
    """Two pains inside the weekly window: today's and one six days back."""
    today=datetime.now(timezone.utc).date()
    db=Database(tmp_path/"radar.db")
    for suffix,text,classified_at in (("today","Today manual spreadsheet pain",today),
                                      ("older","Six days back manual spreadsheet pain",today-timedelta(days=6))):
        db.upsert_signal(_signal(suffix,text)); db.add_pain(_pain(suffix,text,f"{classified_at.isoformat()}T09:00:00+00:00"))
    return db, today.isoformat()


def _evidence(tmp_path, cycle_date: str) -> list[str]:
    report=json.loads((tmp_path/"reports"/f"cycle-{cycle_date}"/"report.json").read_text())
    return sorted(item["pain"] for item in report["evidence"])


def test_report_window_days_carries_the_whole_week(tmp_path, monkeypatch):
    """The weekly deep cycle used to emit a thesis with zero evidence under the daily window."""
    _, cycle_date=_week_db(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["report","--db",str(tmp_path/"radar.db"),"--window-days","7"])

    assert _evidence(tmp_path,cycle_date) == ["Six days back manual spreadsheet pain","Today manual spreadsheet pain"]


def test_report_defaults_to_the_single_day_window(tmp_path, monkeypatch):
    _, cycle_date=_week_db(tmp_path)
    monkeypatch.chdir(tmp_path)

    main(["report","--db",str(tmp_path/"radar.db")])

    assert _evidence(tmp_path,cycle_date) == ["Today manual spreadsheet pain"]
