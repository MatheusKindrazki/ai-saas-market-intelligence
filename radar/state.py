"""Run bookkeeping and staleness lookups."""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from .db import Database
from .models import RunRecord
def now() -> str: return datetime.now(timezone.utc).isoformat()
def start(db: Database, kind: str) -> str:
    run_id=str(uuid.uuid4()); db.start_run(RunRecord(run_id,kind,now(),None,"running",{})); return run_id
def finish(db: Database, run_id: str, ok: bool, detail: dict[str,object]|None=None) -> None: db.finish_run(run_id,"ok" if ok else "error",detail,now())
def last_ok(db: Database, kind: str): return db.last_ok(kind)
