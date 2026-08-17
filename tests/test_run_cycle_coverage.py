from __future__ import annotations

from radar.config import Config
from radar.db import Database
from radar.run_cycle import SOURCES, collect
from radar.sources.base import BaseSource, SourceError


class GapSource(BaseSource):
    family = "test_gap"

    def collect(self, query_context, since=None):
        raise SourceError("coverage gap: fixture policy restriction")


def test_collect_records_coverage_gap_without_error(tmp_path, monkeypatch):
    monkeypatch.setitem(SOURCES, "test_gap", GapSource)
    db = Database(tmp_path / "radar.db")

    summary = collect(db, families=["test_gap"], cfg=Config(db_path=tmp_path / "radar.db"))

    assert summary["test_gap"]["errors"] == 0
    assert summary["test_gap"]["collected"] == 0
    assert summary["test_gap"]["notes"] == "coverage gap: fixture policy restriction"
    coverage = db.connection.execute("SELECT errors, notes FROM coverage").fetchone()
    assert tuple(coverage) == (0, "coverage gap: fixture policy restriction")
    assert db.connection.execute("SELECT count(*) FROM signal_errors").fetchone()[0] == 0
