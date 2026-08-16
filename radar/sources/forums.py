"""Public forum adapters: DEV Community JSON and reusable RSS/Atom parsing."""
from __future__ import annotations

from datetime import date
from xml.etree import ElementTree as ET

from .base import BaseSource, raw_signal
from ..textproc import detect_language


def parse_feed(xml: str, source: str) -> list[dict[str, str]]:
    root = ET.fromstring(xml)
    out = []
    for item in list(root.findall(".//item")) + list(root.findall("{http://www.w3.org/2005/Atom}entry")):
        def get(name: str) -> str:
            node = item.find(name)
            if node is None:
                node = item.find("{http://www.w3.org/2005/Atom}" + name)
            return (node.text or "").strip() if node is not None else ""
        link = item.find("link")
        if link is None:
            link = item.find("{http://www.w3.org/2005/Atom}link")
        url = (link.get("href") if link is not None else "") or get("link")
        out.append({"external_id": get("guid") or get("id") or url, "title": get("title"), "body": get("description") or get("summary") or get("content"), "url": url, "published_at": get("pubDate") or get("updated")})
    return out


class ForumsSource(BaseSource):
    family = "forums"
    tags = ("saas", "startups", "smallbusiness", "productivity", "entrepreneurship")

    def selected_tag(self) -> str:
        return self.tags[date.today().toordinal() % len(self.tags)]

    def collect(self, query_context: str, since: str | None = None):
        tag = self.selected_tag()
        rows = self.fetch_json(f"https://dev.to/api/articles?per_page={self.limit}&tag={tag}")
        signals = []
        for row in rows[:self.limit]:
            body = row.get("description") or row.get("title", "")
            if not body:
                continue
            user = row.get("user") or {}
            signals.append(raw_signal(source="devto", family=self.family, external_id=str(row["id"]), url=row.get("canonical_url") or row.get("url") or f"https://dev.to/articles/{row['id']}", query=query_context, title=row.get("title") or "untitled", body=body, author=user.get("username") or user.get("name"), published_at=row.get("published_at"), lang=detect_language(body)))
        return self.keep_since(signals, since)

    def wordpress_plugin(self, slug: str, query_context: str, since: str | None = None):
        data = parse_feed(self.fetch_text(f"https://wordpress.org/support/rss/plugin/{slug}/"), "wordpress")
        return self.keep_since([raw_signal(source="wordpress", family=self.family, query=query_context, lang=detect_language(row["body"]), **row) for row in data[:self.limit]], since)
