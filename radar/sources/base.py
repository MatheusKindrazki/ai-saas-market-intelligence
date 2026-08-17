"""Shared safe HTTP behavior for source adapters."""
from __future__ import annotations
import json, os, secrets, time, hashlib
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener
from urllib import robotparser
from ..config import Config

USER_AGENT = "deep-opportunity-radar/0.1 (+https://github.com/MatheusKindrazki/ai-saas-market-intelligence; research; contact matheuskindrazki@gmail.com)"
class SourceError(RuntimeError): pass
class BaseSource:
    family: str
    _robots: dict[tuple[str, str], tuple[float, robotparser.RobotFileParser | None, bool]] = {}
    _robots_ttl = 3600
    # These documented public APIs were manually verified as crawler-permitted.
    # Keeping them here avoids turning a transient robots.txt lookup failure into
    # a false source outage before the API request is even attempted.
    _robot_whitelist = {"hn.algolia.com", "api.github.com", "api.stackexchange.com", "api.z.ai", "dev.to", "wordpress.org", "addons.mozilla.org", "gitlab.com"}

    def __init__(self, limit: int = 20, min_interval: float = 1.5, cfg: Config | None = None) -> None:
        self.cfg = cfg or Config.from_env()
        self.limit=limit; self.min_interval=min_interval; self._last=0.0

    def queries(self, query: str | tuple[str, ...] | list[str]) -> tuple[str, ...]:
        return (query,) if isinstance(query, str) else tuple(query)

    def _cache_path(self, url: str) -> Path:
        return self.cfg.cache_dir / (hashlib.sha256(url.encode()).hexdigest() + ".json")

    def _read_cache(self, url: str) -> str | None:
        if not self.cfg.use_cache: return None
        try:
            cached=json.loads(self._cache_path(url).read_text())
            if time.time() - float(cached["fetched_at"]) < 86400 and cached.get("status") == 200:
                return str(cached["body"])
        except (OSError, ValueError, KeyError, TypeError): pass
        return None

    def _write_cache(self, url: str, status: int, body: str) -> None:
        if not self.cfg.use_cache: return
        path=self._cache_path(url); path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"fetched_at": time.time(), "status": status, "body": body}))

    def _robots_allowed(self, url: str) -> bool:
        host=urlparse(url).netloc.casefold().split(":", 1)[0]
        if host in self._robot_whitelist: return True
        key=(self.family, host); cached=self._robots.get(key)
        if cached and time.monotonic()-cached[0] < self._robots_ttl: return cached[2]
        robots_url=f"{urlparse(url).scheme}://{host}/robots.txt"
        parser=robotparser.RobotFileParser(); parser.set_url(robots_url)
        try:
            response=build_opener().open(Request(robots_url, headers={"User-Agent": USER_AGENT}), timeout=15)
            parser.parse(response.read().decode("utf-8", "replace").splitlines())
            allowed=parser.can_fetch(USER_AGENT, url)
        except HTTPError as exc:
            # A missing robots file means no published restrictions. Any other failure is fail-closed.
            allowed=exc.code == 404
        except (URLError, OSError):
            allowed=False
        self._robots[key]=(time.monotonic(), parser if allowed else None, allowed)
        return allowed
    def _headers(self, url: str) -> dict[str, str]:
        """The token is scoped to api.github.com so no other host ever receives our credential."""
        headers={"User-Agent": USER_AGENT}; token=getattr(self.cfg, "github_token", None)
        if token and urlparse(url).netloc.casefold().split(":", 1)[0] == "api.github.com":
            headers["Authorization"]=f"Bearer {token}"
        return headers
    def fetch_json(self, url: str) -> Any:
        return json.loads(self.fetch_text(url))
    def fetch_text(self, url: str) -> str:
        cached=self._read_cache(url)
        if cached is not None: return cached
        if not self._robots_allowed(url): raise SourceError(f"robots denied {urlparse(url).netloc}")
        delay=self.min_interval-(time.monotonic()-self._last)
        if delay>0: time.sleep(delay)
        for attempt in range(3):
            try:
                self._last=time.monotonic(); response=build_opener().open(Request(url,headers=self._headers(url)),timeout=15)
                body=response.read().decode("utf-8", "replace"); self._write_cache(url, response.getcode(), body)
                return body
            except HTTPError as exc:
                if exc.code == 403: raise SourceError("HTTP 403") from exc
                if exc.code == 429:
                    retry_after=exc.headers.get("Retry-After") if exc.headers else None
                    try: wait=max(0.0, float(retry_after)) if retry_after else 2 ** attempt
                    except ValueError: wait=2 ** attempt
                    if attempt == 2: raise SourceError("HTTP 429") from exc
                    time.sleep(wait); continue
                if attempt == 2: raise SourceError(f"HTTP {exc.code}") from exc
            except URLError as exc:
                if attempt == 2: raise SourceError(f"network error: {exc.reason}") from exc
            time.sleep(2 ** attempt)
        raise SourceError("unreachable")
    def keep_since(self, signals: list, since: str | None) -> list:
        if not since: return signals
        cutoff=parse_timestamp(since)
        # An unparseable --since filters nothing rather than killing the family.
        if cutoff is None: return signals
        return [s for s in signals if not s.published_at or (parse_timestamp(s.published_at) or cutoff) >= cutoff]

_salt_cache: dict[str, bytes] = {}

def parse_timestamp(value: str) -> datetime | None:
    """Parse ISO-8601 or RFC 2822 (RSS pubDate) timestamps as UTC-aware datetimes."""
    parsed=None
    try: parsed=datetime.fromisoformat(value.strip().replace("Z","+00:00"))
    except (AttributeError, ValueError):
        try: parsed=parsedate_to_datetime(value)
        except (AttributeError, TypeError, ValueError): return None
    if parsed is None: return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

def _read_salt(path: Path) -> bytes:
    try: return path.read_bytes().strip()
    except OSError: return b""

def author_salt(cfg: Config | None = None) -> bytes:
    """Load — creating on first use — the local salt used for author pseudonyms."""
    path=(cfg or Config.from_env()).salt_path; key=str(path)
    cached=_salt_cache.get(key)
    if cached is not None: return cached
    salt=_read_salt(path)
    if not salt:
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            descriptor=os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError:
            salt=_read_salt(path)  # a concurrent run created it first
        else:
            salt=secrets.token_hex(32).encode()
            with os.fdopen(descriptor, "wb") as handle: handle.write(salt)
        # A present-but-empty salt file would silently de-salt every pseudonym.
        if not salt: raise SourceError(f"empty pseudonymization salt at {path}")
    _salt_cache[key]=salt
    return salt

def author_pseudonym(author: str, cfg: Config | None = None) -> str:
    """Pseudonym contract (docs/ARCHITECTURE.md): sha256(salt + author), salt kept locally."""
    return hashlib.sha256(author_salt(cfg) + author.encode()).hexdigest()

def raw_signal(*, source: str, family: str, external_id: str, url: str, title: str, body: str, query: str|None=None, published_at: str|None=None, author: str|None=None, lang: str="unknown", cfg: Config|None=None):
    from ..models import RawSignal
    now=datetime.now(timezone.utc).isoformat(); body=body or title
    return RawSignal(hashlib.sha256(f"{source}|{external_id}".encode()).hexdigest(),source,family,external_id,url,title,body,author_pseudonym(author, cfg) if author else None,published_at,now,query,lang,hashlib.sha256(body.encode()).hexdigest())
