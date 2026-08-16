"""SQLite persistence for the evidence-first radar."""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from .models import Cluster, CoverageEntry, Pain, RawSignal, Score, Thesis, RunRecord, SignalError

SCHEMA = """
CREATE TABLE IF NOT EXISTS signals(id TEXT PRIMARY KEY, source TEXT, source_family TEXT, external_id TEXT, url TEXT, title TEXT, body TEXT, author_pseudonym TEXT, published_at TEXT, collected_at TEXT, query TEXT, lang TEXT, content_hash TEXT, fetch_status TEXT, http_status INTEGER, UNIQUE(source,external_id));
CREATE TABLE IF NOT EXISTS signal_errors(source TEXT,run_id TEXT,error TEXT,ts TEXT);
CREATE TABLE IF NOT EXISTS pains(id TEXT PRIMARY KEY,signal_id TEXT,pain TEXT,icp TEXT,jtbd TEXT,context TEXT,frequency TEXT,impact TEXT,workaround TEXT,wtp_evidence TEXT,current_solution TEXT,dissatisfaction_reason TEXT,quotes_json TEXT,observed_json TEXT,inference_json TEXT,confidence TEXT,lang TEXT,classified_at TEXT,model TEXT);
CREATE TABLE IF NOT EXISTS clusters(id TEXT PRIMARY KEY,key_terms TEXT,member_pain_ids_json TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS scores(pain_id TEXT PRIMARY KEY,dimensions_json TEXT,total REAL,verdict TEXT,reasons_json TEXT,scored_at TEXT);
CREATE TABLE IF NOT EXISTS theses(id TEXT PRIMARY KEY,cycle_id TEXT,recommendation TEXT,icp TEXT,offer TEXT,price TEXT,mvp_48h TEXT,concierge TEXT,outreach_msgs_json TEXT,kill_criteria_json TEXT,evidence_ids_json TEXT,confidence TEXT,created_at TEXT,cycle_date TEXT);
CREATE TABLE IF NOT EXISTS coverage(run_id TEXT,source TEXT,family TEXT,attempted INTEGER,collected INTEGER,errors INTEGER,window_start TEXT,window_end TEXT,notes TEXT,ts TEXT);
CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,kind TEXT,started_at TEXT,ended_at TEXT,status TEXT,detail_json TEXT);
"""

class Database:
    def __init__(self, path: Path | str) -> None:
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.executescript(SCHEMA)
        self.connection.execute("PRAGMA user_version=1")
        self.connection.commit()
    def close(self) -> None: self.connection.close()
    def upsert_signal(self, signal: RawSignal) -> bool:
        values = tuple(getattr(signal, k) for k in RawSignal.__dataclass_fields__)
        inserted = self.connection.execute("INSERT OR IGNORE INTO signals VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values).rowcount == 1
        if not inserted:
            self.connection.execute("UPDATE signals SET content_hash=?,body=?,title=?,collected_at=?,fetch_status=?,http_status=? WHERE source=? AND external_id=?", (signal.content_hash, signal.body, signal.title, signal.collected_at, signal.fetch_status, signal.http_status, signal.source, signal.external_id))
        self.connection.commit(); return inserted
    def signals(self) -> list[RawSignal]:
        return [RawSignal(**dict(r)) for r in self.connection.execute("SELECT * FROM signals ORDER BY id")]
    def add_pain(self, p: Pain) -> None:
        self.connection.execute("INSERT OR REPLACE INTO pains VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (*[getattr(p,k) for k in list(Pain.__dataclass_fields__)[:12]],json.dumps(p.quotes),json.dumps(p.observed),json.dumps(p.inference),p.confidence,p.lang,p.classified_at,p.model)); self.connection.commit()
    def add_cluster(self, x: Cluster) -> None: self.connection.execute("INSERT OR REPLACE INTO clusters VALUES (?,?,?,?)",(x.id,x.key_terms,json.dumps(x.member_pain_ids),x.created_at));self.connection.commit()
    def add_score(self, x: Score) -> None: self.connection.execute("INSERT OR REPLACE INTO scores VALUES (?,?,?,?,?,?)",(x.pain_id,json.dumps(x.dimensions),x.total,x.verdict,json.dumps(x.reasons),x.scored_at));self.connection.commit()
    def add_thesis(self, x: Thesis) -> None: self.connection.execute("INSERT OR REPLACE INTO theses VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(*list(x.__dict__.values())[:8],json.dumps(x.outreach_msgs),json.dumps(x.kill_criteria),json.dumps(x.evidence_ids),x.confidence,x.created_at,x.cycle_date));self.connection.commit()
    def add_coverage(self, x: CoverageEntry) -> None: self.connection.execute("INSERT INTO coverage VALUES (?,?,?,?,?,?,?,?,?,?)",tuple(x.__dict__.values()));self.connection.commit()
    def add_error(self, error: SignalError) -> None:
        self.connection.execute("INSERT INTO signal_errors VALUES (?,?,?,?)", (error.source,error.run_id,error.error,error.ts)); self.connection.commit()
    def pains(self) -> list[Pain]:
        rows=self.connection.execute("SELECT * FROM pains ORDER BY id")
        return [Pain(r["id"],r["signal_id"],r["pain"],r["icp"],r["jtbd"],r["context"],r["frequency"],r["impact"],r["workaround"],r["wtp_evidence"],r["current_solution"],r["dissatisfaction_reason"],tuple(json.loads(r["quotes_json"])),tuple(json.loads(r["observed_json"])),tuple(json.loads(r["inference_json"])),r["confidence"],r["lang"],r["classified_at"],r["model"]) for r in rows]
    def start_run(self, record: RunRecord) -> None:
        self.connection.execute("INSERT INTO runs VALUES (?,?,?,?,?,?)",(record.id,record.kind,record.started_at,record.ended_at,record.status,json.dumps(record.detail)));self.connection.commit()
    def finish_run(self, run_id: str, status: str, detail: dict[str, object] | None=None, ended_at: str | None=None) -> None:
        from datetime import datetime, timezone
        ended_at=ended_at or datetime.now(timezone.utc).isoformat()
        self.connection.execute("UPDATE runs SET ended_at=?,status=?,detail_json=? WHERE id=?",(ended_at,status,json.dumps(detail or {}),run_id));self.connection.commit()
    def last_ok(self, kind: str):
        return self.connection.execute("SELECT * FROM runs WHERE kind=? AND status='ok' ORDER BY ended_at DESC LIMIT 1",(kind,)).fetchone()
