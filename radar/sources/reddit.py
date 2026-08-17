"""Reddit adapter retained for parsing, but collection is policy-blocked."""
from __future__ import annotations

from datetime import datetime, timezone

from .base import BaseSource, SourceError, raw_signal
from ..textproc import detect_language


REDDIT_COVERAGE_GAP = "coverage gap: reddit robots.txt denies all crawlers (Public Content Policy)"


class RedditSource(BaseSource):
    family = "reddit"
    subreddits = ("founders", "smallbusiness", "SaaS", "sysadmin", "msp", "accounting", "ecommerce", "agencies", "dentistry", "veterinary", "construction")

    def collect(self, query_context: str | tuple[str, ...] | list[str], since: str | None = None):
        """Raise immediately: Reddit's published robots policy denies this collector."""
        raise SourceError(REDDIT_COVERAGE_GAP)

    def parse(self, data: dict, query: str):
        out = []
        for item in data.get("data", {}).get("children", [])[:self.limit]:
            row = item["data"]
            body = row.get("selftext") or row.get("title", "")
            if not body:
                continue
            out.append(raw_signal(source="reddit", family=self.family, external_id=row.get("id") or row.get("permalink"), url="https://www.reddit.com" + row.get("permalink", "/"), query=query, title=row.get("title", "untitled"), body=body, author=row.get("author"), published_at=datetime.fromtimestamp(row["created_utc"], timezone.utc).isoformat() if row.get("created_utc") else None, lang=detect_language(body), cfg=self.cfg))
        return out

    def parse_atom(self, xml: str, query: str):
        from .forums import parse_feed
        return [raw_signal(source="reddit", family=self.family, query=query, lang=detect_language(row["body"]), cfg=self.cfg, **row) for row in parse_feed(xml, "reddit") if row["body"]]
