"""Hacker News Algolia adapter."""
from __future__ import annotations
from datetime import datetime, timezone
from urllib.parse import quote_plus
from .base import BaseSource
from ..textproc import detect_language
from .base import raw_signal
class HackerNewsSource(BaseSource):
    family="hackernews"
    def collect(self, query_context: str, since: str|None=None): return self.keep_since(self.parse(self.fetch_json(f"https://hn.algolia.com/api/v1/search_by_date?query={quote_plus(query_context)}&tags=(story,comment)&hitsPerPage={self.limit}"),query_context),since)
    def parse(self,data:dict,query:str):
        result=[]
        for d in data.get("hits",[])[:self.limit]:
            body=d.get("comment_text") or d.get("story_text") or d.get("title") or ""; title=d.get("story_title") or d.get("title") or "HN discussion"
            if body: result.append(raw_signal(source="hackernews",family=self.family,external_id=str(d.get("objectID")),url=f"https://news.ycombinator.com/item?id={d.get('objectID')}",query=query,title=title,body=body,author=d.get("author"),published_at=d.get("created_at"),lang=detect_language(body)))
        return result
