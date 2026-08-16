from datetime import datetime, timezone

import pytest

from radar.db import Database
from radar.models import Pain, Score
from radar.run_cycle import deep_validate


class FakeSearch:
    def collect(self, query):
        return [
            {"url": "https://evidence.test/one", "title": "One", "body": "Manual work takes hours."},
            {"url": "https://evidence.test/two", "title": "Two", "body": "Teams need automation."},
        ]


class FakeLLM:
    def __init__(self, recommendation):
        self.recommendation = recommendation

    def classify(self, content, schema=None):
        if "Research evidence" in content:
            return {"competitors": [], "negative_patterns": [], "diy_alternatives": [], "acquisition_channels": [], "buyers": []}
        return {
            "recommendation": self.recommendation,
            "icp": "Operations teams",
            "offer": "Automate weekly intake using " + self.recommendation.split("using ", 1)[-1],
            "price": "$99/month",
            "mvp_48h": "Import a spreadsheet and produce a report.",
            "concierge": "Run the workflow manually for five teams.",
            "outreach_msgs": ["We saw this recurring workflow."],
            "kill_criteria": ["Fewer than three interviews booked."],
        }


def seed_pain(db, total=18):
    now = datetime.now(timezone.utc).isoformat()
    pain = Pain(
        "pain-1", "signal-1", "Manual spreadsheet work takes hours", "Operations teams",
        "Finish weekly reporting", "Weekly reporting is manual", "weekly", "hours lost",
        "spreadsheets", "budget approved", "none", "too slow", (), (), (), "A", "en", now, "test",
    )
    db.add_pain(pain)
    db.add_score(Score(pain.id, {"severity": 5}, total, "include", ("test",), now))


def test_deep_persists_verified_thesis_and_cluster(tmp_path):
    db = Database(tmp_path / "radar.db")
    seed_pain(db)

    thesis = deep_validate(db, None, FakeLLM("Build this for pain-1 using https://evidence.test/one."), FakeSearch())

    assert thesis is not None
    assert thesis.confidence == "A"
    assert db.connection.execute("SELECT COUNT(*) FROM clusters").fetchone()[0] == 1
    assert db.connection.execute("SELECT COUNT(*) FROM theses").fetchone()[0] == 1


def test_deep_rejects_thesis_with_no_known_evidence_reference(tmp_path):
    db = Database(tmp_path / "radar.db")
    seed_pain(db)

    with pytest.raises(ValueError, match="evidence"):
        deep_validate(db, None, FakeLLM("Build this using https://invented.test/proof."), FakeSearch())

    assert db.connection.execute("SELECT COUNT(*) FROM theses").fetchone()[0] == 0
    assert db.connection.execute("SELECT COUNT(*) FROM signal_errors").fetchone()[0] == 1


def test_deep_is_silent_when_no_cluster_clears_score_bar(tmp_path):
    db = Database(tmp_path / "radar.db")
    seed_pain(db, total=14)

    assert deep_validate(db, None, FakeLLM("Build this for pain-1."), FakeSearch()) is None
    assert db.connection.execute("SELECT COUNT(*) FROM theses").fetchone()[0] == 0
