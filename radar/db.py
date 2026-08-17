"""SQLite persistence for the evidence-first radar."""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import Iterable
from .models import Cluster, CoverageEntry, Pain, RawSignal, Score, Thesis, RunRecord, SignalError

SCHEMA = """
CREATE TABLE IF NOT EXISTS signals(id TEXT PRIMARY KEY, source TEXT, source_family TEXT, external_id TEXT, url TEXT, title TEXT, body TEXT, author_pseudonym TEXT, published_at TEXT, collected_at TEXT, query TEXT, lang TEXT, content_hash TEXT, fetch_status TEXT, http_status INTEGER, UNIQUE(source,external_id));
CREATE TABLE IF NOT EXISTS signal_errors(source TEXT,run_id TEXT,error TEXT,ts TEXT);
CREATE TABLE IF NOT EXISTS pains(id TEXT PRIMARY KEY,signal_id TEXT,pain TEXT,icp TEXT,jtbd TEXT,context TEXT,frequency TEXT,impact TEXT,workaround TEXT,wtp_evidence TEXT,current_solution TEXT,dissatisfaction_reason TEXT,quotes_json TEXT,observed_json TEXT,inference_json TEXT,confidence TEXT,lang TEXT,classified_at TEXT,model TEXT);
CREATE TABLE IF NOT EXISTS clusters(id TEXT PRIMARY KEY,key_terms TEXT,member_pain_ids_json TEXT,created_at TEXT);
CREATE TABLE IF NOT EXISTS scores(pain_id TEXT PRIMARY KEY,dimensions_json TEXT,total REAL,verdict TEXT,reasons_json TEXT,scored_at TEXT);
CREATE TABLE IF NOT EXISTS theses(id TEXT PRIMARY KEY,cycle_id TEXT,recommendation TEXT,icp TEXT,offer TEXT,price TEXT,mvp_48h TEXT,concierge TEXT,outreach_msgs_json TEXT,kill_criteria_json TEXT,evidence_ids_json TEXT,confidence TEXT,created_at TEXT,cycle_date TEXT,quality_json TEXT);
CREATE TABLE IF NOT EXISTS coverage(run_id TEXT,source TEXT,family TEXT,attempted INTEGER,collected INTEGER,errors INTEGER,window_start TEXT,window_end TEXT,notes TEXT,ts TEXT,error_details TEXT);
CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,kind TEXT,started_at TEXT,ended_at TEXT,status TEXT,detail_json TEXT);
"""

class Database:
    def __init__(self, path: Path | str) -> None:
        # A clean checkout has no radar_runtime/, and sqlite3.connect will not create it.
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.executescript(SCHEMA)
        columns={row[1] for row in self.connection.execute("PRAGMA table_info(coverage)")}
        if "error_details" not in columns:
            self.connection.execute("ALTER TABLE coverage ADD COLUMN error_details TEXT")
        self.connection.execute("PRAGMA user_version=1")
        thesis_columns={row[1] for row in self.connection.execute("PRAGMA table_info(theses)")}
        if "quality_json" not in thesis_columns:
            self.connection.execute("ALTER TABLE theses ADD COLUMN quality_json TEXT")
        self.connection.commit()
    def close(self) -> None: self.connection.close()
    def upsert_signal(self, signal: RawSignal) -> bool:
        values = tuple(getattr(signal, k) for k in RawSignal.__dataclass_fields__)
        inserted = self.connection.execute("INSERT OR IGNORE INTO signals VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values).rowcount == 1
        if not inserted:
            existing = self.connection.execute("SELECT id,content_hash FROM signals WHERE source=? AND external_id=?", (signal.source, signal.external_id)).fetchone()
            # Live sources edit posts. Everything classified from the old body quotes text that is
            # no longer there, so the derived rows are dropped before the new body lands: an
            # unchanged hash keeps them, which is what makes the daily refetch idempotent.
            if existing is not None and existing["content_hash"] != signal.content_hash:
                self.invalidate_derived(existing["id"])
            self.connection.execute("UPDATE signals SET content_hash=?,body=?,title=?,collected_at=?,fetch_status=?,http_status=? WHERE source=? AND external_id=?", (signal.content_hash, signal.body, signal.title, signal.collected_at, signal.fetch_status, signal.http_status, signal.source, signal.external_id))
        self.connection.commit(); return inserted
    def invalidate_derived(self, signal_id: str) -> set[str]:
        """Drop every classification derived from one signal's body; returns the deleted pain ids.

        Fail-closed: the pain itself goes, not just its quotes, because its whole record — pain,
        context, wtp evidence — was read out of text this database no longer holds. Deleting the
        pains alone would leave scores keyed to nothing and clusters listing absent members.
        """
        pain_ids={row[0] for row in self.connection.execute("SELECT id FROM pains WHERE signal_id=?", (signal_id,))}
        if not pain_ids: return pain_ids
        placeholders=",".join("?"*len(pain_ids)); params=tuple(pain_ids)
        self.connection.execute(f"DELETE FROM scores WHERE pain_id IN ({placeholders})", params)
        self.connection.execute(f"DELETE FROM pains WHERE id IN ({placeholders})", params)
        # A cluster is a frozen member list, so one invalidated member makes the whole row
        # unexecutable — deep re-derives its clusters from the surviving pains anyway.
        for row in self.connection.execute("SELECT id,member_pain_ids_json FROM clusters").fetchall():
            try: members=set(json.loads(row["member_pain_ids_json"] or "[]"))
            except (TypeError, ValueError): members=set()
            if members & pain_ids: self.connection.execute("DELETE FROM clusters WHERE id=?", (row["id"],))
        return pain_ids
    def signals(self) -> list[RawSignal]:
        return [RawSignal(**dict(r)) for r in self.connection.execute("SELECT * FROM signals ORDER BY id")]
    def signal_bodies(self, signal_ids: Iterable[str] | None = None) -> dict[str, str]:
        """signal id -> the body stored right now, for re-checking quotes mined from an older one.

        Scoped by id when the caller knows them: the signals table only ever grows, and a report
        needs the handful of bodies its own window's pains were mined from, not every body ever
        collected. A missing id is simply absent from the result — the caller decides what that means.
        """
        if signal_ids is None:
            return {row[0]: row[1] or "" for row in self.connection.execute("SELECT id,body FROM signals")}
        ids = sorted(set(signal_ids)); bodies: dict[str, str] = {}
        for start in range(0, len(ids), 400):  # stay well under SQLite's bound-variable limit
            chunk = ids[start:start + 400]
            bodies.update({row[0]: row[1] or "" for row in self.connection.execute(
                f"SELECT id,body FROM signals WHERE id IN ({','.join('?' * len(chunk))})", chunk)})
        return bodies
    def classified_signal_ids(self) -> set[str]:
        return {r[0] for r in self.connection.execute("SELECT signal_id FROM pains")}
    def add_pain(self, p: Pain) -> None:
        self.connection.execute("INSERT OR REPLACE INTO pains VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (*[getattr(p,k) for k in list(Pain.__dataclass_fields__)[:12]],json.dumps(p.quotes),json.dumps(p.observed),json.dumps(p.inference),p.confidence,p.lang,p.classified_at,p.model)); self.connection.commit()
    def add_cluster(self, x: Cluster) -> None: self.connection.execute("INSERT OR REPLACE INTO clusters VALUES (?,?,?,?)",(x.id,x.key_terms,json.dumps(x.member_pain_ids),x.created_at));self.connection.commit()
    def add_score(self, x: Score) -> None: self.connection.execute("INSERT OR REPLACE INTO scores VALUES (?,?,?,?,?,?)",(x.pain_id,json.dumps(x.dimensions),x.total,x.verdict,json.dumps(x.reasons),x.scored_at));self.connection.commit()
    def add_thesis(self, x: Thesis) -> None:
        quality = json.dumps({
            "evidence_matrix": list(x.evidence_matrix),
            "confidence_reason": x.confidence_reason,
            "recommendation_kind": x.recommendation_kind,
        })
        self.connection.execute("INSERT OR REPLACE INTO theses VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",(*list(x.__dict__.values())[:8],json.dumps(x.outreach_msgs),json.dumps(x.kill_criteria),json.dumps(x.evidence_ids),x.confidence,x.created_at,x.cycle_date,quality));self.connection.commit()
    def add_coverage(self, x: CoverageEntry) -> None:
        self.connection.execute("INSERT INTO coverage (run_id,source,family,attempted,collected,errors,window_start,window_end,notes,ts,error_details) VALUES (?,?,?,?,?,?,?,?,?,?,?)", (*tuple(x.__dict__.values())[:10],json.dumps(x.error_details)))
        self.connection.commit()
    def add_error(self, error: SignalError) -> None:
        self.connection.execute("INSERT INTO signal_errors VALUES (?,?,?,?)", (error.source,error.run_id,error.error,error.ts)); self.connection.commit()
    def pains(self, since: str|None=None, until: str|None=None) -> list[Pain]:
        """since/until are inclusive UTC dates (YYYY-MM-DD) matched against classified_at."""
        rows=self.connection.execute("SELECT * FROM pains WHERE substr(classified_at,1,10) BETWEEN ? AND ? ORDER BY id",(since or "0000-01-01",until or "9999-12-31"))
        return [Pain(r["id"],r["signal_id"],r["pain"],r["icp"],r["jtbd"],r["context"],r["frequency"],r["impact"],r["workaround"],r["wtp_evidence"],r["current_solution"],r["dissatisfaction_reason"],tuple(json.loads(r["quotes_json"])),tuple(json.loads(r["observed_json"])),tuple(json.loads(r["inference_json"])),r["confidence"],r["lang"],r["classified_at"],r["model"]) for r in rows]
    def start_run(self, record: RunRecord) -> None:
        self.connection.execute("INSERT INTO runs VALUES (?,?,?,?,?,?)",(record.id,record.kind,record.started_at,record.ended_at,record.status,json.dumps(record.detail)));self.connection.commit()
    def finish_run(self, run_id: str, status: str, detail: dict[str, object] | None=None, ended_at: str | None=None) -> None:
        from datetime import datetime, timezone
        ended_at=ended_at or datetime.now(timezone.utc).isoformat()
        self.connection.execute("UPDATE runs SET ended_at=?,status=?,detail_json=? WHERE id=?",(ended_at,status,json.dumps(detail or {}),run_id));self.connection.commit()
    def last_ok(self, kind: str):
        return self.connection.execute("SELECT * FROM runs WHERE kind=? AND status='ok' ORDER BY ended_at DESC LIMIT 1",(kind,)).fetchone()
    def latest_deep_runs(self, since: str, until: str) -> dict[str, str]:
        """cycle date -> id of the newest successful deep run of that date, for dates in the window.

        A deep run stamps its thesis with the UTC date it started, so the run's own start date is
        the cycle date without a join. Failed runs are excluded: a crashed retry decides nothing.
        """
        latest: dict[str,str]={}
        for row in self.connection.execute(
            "SELECT id, substr(started_at,1,10) AS cycle_date FROM runs WHERE kind='deep' AND status='ok' "
            "AND substr(started_at,1,10) BETWEEN ? AND ? ORDER BY ended_at DESC, started_at DESC, rowid DESC",
            (since,until)):
            latest.setdefault(row["cycle_date"],row["id"])
        return latest
