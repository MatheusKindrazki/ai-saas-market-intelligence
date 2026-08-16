"""Stack Exchange API adapter."""
from __future__ import annotations
from datetime import datetime, timezone
from urllib.parse import quote_plus
from .base import BaseSource
from ..textproc import detect_language
from .base import raw_signal
class StackExchangeSource(BaseSource):
 family="stackexchange"
 def collect(self,q:str,since: str|None=None): return self.keep_since(self.parse(self.fetch_json(f"https://api.stackexchange.com/2.3/search/advanced?site=stackoverflow&order=desc&sort=creation&filter=withbody&q={quote_plus(q)}&pagesize={self.limit}"),q),since)
 def parse(self,data:dict,q:str):
  return [raw_signal(source="stackexchange",family=self.family,external_id=str(d["question_id"]),url=d["link"],query=q,title=d["title"],body=d.get("body") or d["title"],author=d.get("owner",{}).get("display_name"),published_at=datetime.fromtimestamp(d["creation_date"],timezone.utc).isoformat() if d.get("creation_date") else None,lang=detect_language(d.get("body") or d["title"])) for d in data.get("items",[])[:self.limit]]
