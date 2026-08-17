from radar.db import Database
from radar.models import RawSignal

def signal(body="manual work"):
    return RawSignal("a", "reddit", "reddit", "1", "https://x.test/1", "t", body, "hash", "2026-01-01", "2026-01-02", "q", "en", "c" * 64)

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
