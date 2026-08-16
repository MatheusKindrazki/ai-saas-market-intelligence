"""Shared safe HTTP behavior for source adapters."""
from __future__ import annotations
import json, time, hashlib
from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener

USER_AGENT = "deep-opportunity-radar/0.1 (+https://github.com/MatheusKindrazki/ai-saas-market-intelligence; research; contact matheuskindrazki@gmail.com)"
class SourceError(RuntimeError): pass
class BaseSource:
    family: str
    def __init__(self, limit: int = 20, min_interval: float = 1.5) -> None: self.limit=limit;self.min_interval=min_interval;self._last=0.0
    def fetch_json(self, url: str) -> Any:
        return json.loads(self.fetch_text(url))
    def fetch_text(self, url: str) -> str:
        delay=self.min_interval-(time.monotonic()-self._last)
        if delay>0: time.sleep(delay)
        for attempt in range(3):
            try:
                self._last=time.monotonic(); response=build_opener().open(Request(url,headers={"User-Agent":USER_AGENT}),timeout=15)
                return response.read().decode("utf-8", "replace")
            except HTTPError as exc:
                if exc.code in (403,429): raise SourceError(f"HTTP {exc.code}") from exc
                if attempt == 2: raise SourceError(f"HTTP {exc.code}") from exc
            except URLError as exc:
                if attempt == 2: raise SourceError(f"network error: {exc.reason}") from exc
            time.sleep(2 ** attempt)
        raise SourceError("unreachable")
    def keep_since(self, signals: list, since: str | None) -> list:
        if not since: return signals
        cutoff=datetime.fromisoformat(since.replace("Z","+00:00"))
        return [s for s in signals if not s.published_at or datetime.fromisoformat(s.published_at.replace("Z","+00:00")) >= cutoff]
def raw_signal(*, source: str, family: str, external_id: str, url: str, title: str, body: str, query: str|None=None, published_at: str|None=None, author: str|None=None, lang: str="unknown"):
    from ..models import RawSignal
    now=datetime.now(timezone.utc).isoformat(); body=body or title
    return RawSignal(hashlib.sha256(f"{source}|{external_id}".encode()).hexdigest(),source,family,external_id,url,title,body,hashlib.sha256(author.encode()).hexdigest() if author else None,published_at,now,query,lang,hashlib.sha256(body.encode()).hexdigest())
