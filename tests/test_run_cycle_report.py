from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from radar.db import Database
from radar.models import Pain
from radar.run_cycle import main


def _pain(suffix: str, text: str, classified_at: str) -> Pain:
    return Pain(f"pain-{suffix}",f"signal-{suffix}",text,"Ops teams","weekly reporting","manual weekly reporting","weekly","hours lost","spreadsheets","budget approved","none","too slow",
                ({"quote":text,"url":f"https://evidence.test/{suffix}","verified":True},),(text,),(),"A","en",classified_at,"test")


def _week_db(tmp_path) -> tuple[Database, str]:
    """Two pains inside the weekly window: today's and one six days back."""
    today=datetime.now(timezone.utc).date()
    db=Database(tmp_path/"radar.db")
    db.add_pain(_pain("today","Today manual spreadsheet pain",f"{today.isoformat()}T09:00:00+00:00"))
    db.add_pain(_pain("older","Six days back manual spreadsheet pain",f"{(today-timedelta(days=6)).isoformat()}T09:00:00+00:00"))
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
