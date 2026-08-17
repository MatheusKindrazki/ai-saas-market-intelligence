from radar.db import Database
from radar.models import Cluster, Pain, RawSignal, Score

def signal(body="manual work", content_hash="c" * 64, external_id="1", signal_id="a"):
    return RawSignal(signal_id, "reddit", "reddit", external_id, "https://x.test/1", "t", body, "hash", "2026-01-01", "2026-01-02", "q", "en", content_hash)

def pain(pain_id="pain-a", signal_id="a", text="the manual spreadsheet takes hours"):
    return Pain(pain_id, signal_id, text, "Ops teams", "weekly reporting", "manual weekly reporting", "weekly", "hours lost", "spreadsheets", "$99/month", "none", "too slow",
                ({"quote": text, "url": "https://x.test/1", "verified": True},), (text,), (), "A", "en", "2026-01-02T09:00:00+00:00", "test")

def score(pain_id="pain-a"):
    return Score(pain_id, {"severity": 5.0}, 20.0, "keep", ("evidence-first baseline",), "2026-01-02T09:00:00+00:00")

def cluster(cluster_id="cluster-a", members=("pain-a",)):
    return Cluster(cluster_id, "manual spreadsheet", tuple(members), "2026-01-02T09:00:00+00:00")

def _classified(db):
    """The derived rows a signal's body backs: pains, their scores, and clusters listing them."""
    return ([p.id for p in db.pains()],
            [r[0] for r in db.connection.execute("SELECT pain_id FROM scores ORDER BY pain_id")],
            [r[0] for r in db.connection.execute("SELECT id FROM clusters ORDER BY id")])

def test_signal_insert_is_idempotent_and_updates_content(tmp_path):
    db = Database(tmp_path / "r.db")
    assert db.connection.execute("PRAGMA user_version").fetchone()[0] == 1
    assert db.upsert_signal(signal()) is True
    assert db.upsert_signal(signal()) is False
    assert db.upsert_signal(signal("takes hours")) is False
    assert db.signals()[0].body == "takes hours"
    assert db.connection.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"

def test_opens_a_db_whose_parent_directories_are_missing(tmp_path):
    """A clean checkout has no radar_runtime/; sqlite3.connect used to fail on it."""
    path = tmp_path / "radar_runtime" / "nested" / "radar.db"

    db = Database(path)

    assert path.exists()
    assert db.upsert_signal(signal()) is True

def test_changed_content_invalidates_pains_scores_and_clusters(tmp_path):
    """Live sources edit posts: quotes mined from the old body no longer occur in the new one."""
    db = Database(tmp_path / "r.db")
    db.upsert_signal(signal("the manual spreadsheet takes hours"))
    db.add_pain(pain()); db.add_score(score()); db.add_cluster(cluster())

    assert db.upsert_signal(signal("the author rewrote the post", "d" * 64)) is False

    assert _classified(db) == ([], [], [])
    # The signal must look unclassified again so the next mine re-reads it against the new body.
    assert db.classified_signal_ids() == set()
    assert db.signals()[0].body == "the author rewrote the post"

def test_unchanged_content_hash_preserves_pains_scores_and_clusters(tmp_path):
    """An idempotent daily refetch must not throw away — and pay to re-mine — the same evidence."""
    db = Database(tmp_path / "r.db")
    db.upsert_signal(signal("the manual spreadsheet takes hours"))
    db.add_pain(pain()); db.add_score(score()); db.add_cluster(cluster())

    assert db.upsert_signal(signal("the manual spreadsheet takes hours")) is False

    assert _classified(db) == (["pain-a"], ["pain-a"], ["cluster-a"])

def test_invalidation_is_scoped_to_the_changed_signal(tmp_path):
    db = Database(tmp_path / "r.db")
    db.upsert_signal(signal("the manual spreadsheet takes hours"))
    db.upsert_signal(signal("another manual spreadsheet complaint", "e" * 64, external_id="2", signal_id="b"))
    db.add_pain(pain()); db.add_score(score()); db.add_cluster(cluster())
    db.add_pain(pain("pain-b", "b")); db.add_score(score("pain-b")); db.add_cluster(cluster("cluster-b", ("pain-b",)))

    db.upsert_signal(signal("the author rewrote the post", "d" * 64))

    assert _classified(db) == (["pain-b"], ["pain-b"], ["cluster-b"])

def test_invalidation_removes_a_cluster_that_only_partly_overlaps(tmp_path):
    """A cluster is a frozen member list: one deleted member makes the whole row unexecutable."""
    db = Database(tmp_path / "r.db")
    db.upsert_signal(signal("the manual spreadsheet takes hours"))
    db.upsert_signal(signal("another manual spreadsheet complaint", "e" * 64, external_id="2", signal_id="b"))
    db.add_pain(pain()); db.add_pain(pain("pain-b", "b"))
    db.add_cluster(cluster("cluster-mixed", ("pain-a", "pain-b")))

    db.upsert_signal(signal("the author rewrote the post", "d" * 64))

    assert _classified(db) == (["pain-b"], [], [])
