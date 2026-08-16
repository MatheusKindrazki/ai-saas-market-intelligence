"""Reddit public JSON adapter."""
from __future__ import annotations
from datetime import datetime, timezone
from urllib.parse import quote_plus
from .base import BaseSource
from ..textproc import detect_language
from .base import raw_signal
class RedditSource(BaseSource):
    family="reddit"; subreddits=("founders","smallbusiness","SaaS","sysadmin","msp","accounting","ecommerce","agencies","dentistry","veterinary","construction")
    def collect(self, query_context: str, since: str|None=None):
        out=[]
        for subreddit in self.subreddits:
            out += self.parse_atom(self.fetch_text(f"https://www.reddit.com/r/{subreddit}/.rss"),query_context)
        return self.keep_since(out[:self.limit],since)
    def parse(self, data: dict, query: str):
        out=[]
        for item in data.get("data",{}).get("children",[])[:self.limit]:
            d=item["data"]; body=d.get("selftext") or d.get("title","")
            if not body: continue
            out.append(raw_signal(source="reddit",family=self.family,external_id=d.get("id") or d.get("permalink"),url="https://www.reddit.com"+d.get("permalink","/"),query=query,title=d.get("title","untitled"),body=body,author=d.get("author"),published_at=datetime.fromtimestamp(d["created_utc"],timezone.utc).isoformat() if d.get("created_utc") else None,lang=detect_language(body)))
        return out
    def parse_atom(self, xml: str, query: str):
        from .forums import parse_feed
        return [raw_signal(source="reddit",family=self.family,query=query,lang=detect_language(x["body"]),**x) for x in parse_feed(xml,"reddit") if x["body"]]
