"""RSS/Atom forum adapters (Product Hunt and WordPress support feeds)."""
from __future__ import annotations
from xml.etree import ElementTree as ET
from .base import BaseSource, raw_signal
def parse_feed(xml: str, source: str) -> list[dict[str,str]]:
    root=ET.fromstring(xml); out=[]
    for item in list(root.findall(".//item"))+list(root.findall("{http://www.w3.org/2005/Atom}entry")):
        def get(name: str) -> str:
            node=item.find(name)
            if node is None: node=item.find("{http://www.w3.org/2005/Atom}"+name)
            return (node.text or "").strip() if node is not None else ""
        link=item.find("link")
        if link is None: link=item.find("{http://www.w3.org/2005/Atom}link")
        url=(link.get("href") if link is not None else "") or get("link")
        out.append({"external_id":get("guid") or get("id") or url,"title":get("title"),"body":get("description") or get("summary") or get("content"),"url":url,"published_at":get("pubDate") or get("updated")})
    return out
class ForumsSource(BaseSource):
 family="forums"
 def collect(self, query_context: str, since: str|None=None):
  data=parse_feed(self.fetch_text("https://www.producthunt.com/feed"),"producthunt")
  return self.keep_since([raw_signal(source="producthunt",family=self.family,query=query_context,lang="unknown",**x) for x in data[:self.limit]],since)
 def wordpress_plugin(self, slug: str, query_context: str, since: str|None=None):
  data=parse_feed(self.fetch_text(f"https://wordpress.org/support/rss/plugin/{slug}/"),"wordpress")
  return self.keep_since([raw_signal(source="wordpress",family=self.family,query=query_context,lang="unknown",**x) for x in data[:self.limit]],since)
