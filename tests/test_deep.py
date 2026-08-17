import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from radar.db import Database
from radar.models import Pain, Score
from radar.run_cycle import _cluster_terms, deep_validate
from radar.validate import validate_cluster


class FakeSearch:
    def collect(self, query):
        return [
            {"url": "https://evidence.test/one", "title": "One", "body": "Manual work takes hours."},
            {"url": "https://evidence.test/two", "title": "Two", "body": "Teams need automation."},
        ]


class FakeLLM:
    def __init__(self, recommendation):
        self.recommendation = recommendation

    def classify(self, content, schema=None, max_tokens=None):
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


def test_cluster_terms_keep_content_words_only():
    """A live run searched 'The Model column is too' and got 60 irrelevant items back."""
    pain = SimpleNamespace(
        pain="The Model column is too computationally expensive to run on the scheduled cron path",
        icp="Data engineers maintaining cron pipelines",
    )

    terms = _cluster_terms([pain]).split()

    assert "model" in terms and "cron" in terms
    assert not {"the", "is", "to", "on"} & set(terms)
    assert all(len(term) >= 3 for term in terms)


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


class BulkSearch:
    """Real adapters return up to 60 long items; the prompt must not carry them all."""
    def collect(self, query):
        return [{"url": f"https://evidence.test/{i}", "title": "T" * 400, "body": "B" * 5000} for i in range(60)]


def test_validate_cluster_prompt_caps_items_and_excerpts_bodies():
    prompts = []

    class RecordingLLM:
        def classify(self, content, schema=None):
            prompts.append(content)
            return {"competitors": [{"url": "https://evidence.test/0", "quote": "cited", "confidence": "A"}]}

    output = validate_cluster(SimpleNamespace(key_terms="manual work"), BulkSearch(), RecordingLLM())

    assert prompts[0].count("https://evidence.test/") <= 15
    assert len(prompts[0]) < 8000
    assert "B" * 400 not in prompts[0]
    assert output["competitors"] == [{"url": "https://evidence.test/0", "quote": "cited", "confidence": "A"}]


def test_deep_thesis_prompt_is_bounded_and_json_serialisable(tmp_path):
    db = Database(tmp_path / "radar.db")
    seed_pain(db)
    prompts = []

    class RecordingLLM(FakeLLM):
        def classify(self, content, schema=None, max_tokens=None):
            prompts.append(content)
            return super().classify(content, schema)

    thesis = deep_validate(db, None, RecordingLLM("Build this for pain-1 using https://evidence.test/0."), BulkSearch())

    assert thesis is not None and thesis.confidence == "A"
    payload = json.loads(prompts[-1].split("(DATA): ", 1)[1])
    assert len(payload["evidence"]) <= 20
    assert all(len(item["body"]) <= 200 for item in payload["evidence"])
    assert len(prompts[-1]) < 12000


def test_deep_thesis_call_asks_for_a_bigger_output_budget_than_validation(tmp_path):
    """The thesis JSON is large; at the 4k client default it came back cut mid-string."""
    db = Database(tmp_path / "radar.db")
    seed_pain(db)
    budgets = []

    class RecordingLLM(FakeLLM):
        def classify(self, content, schema=None, max_tokens=None):
            budgets.append(max_tokens)
            return super().classify(content, schema)

    assert deep_validate(db, None, RecordingLLM("Build this for pain-1 using https://evidence.test/one."), FakeSearch()) is not None
    assert budgets[-1] == 16000
    assert budgets[:-1] == [None] * (len(budgets) - 1)
