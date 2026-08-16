"""DuckDuckGo HTML result-link adapter (no browser automation)."""
from __future__ import annotations
from html.parser import HTMLParser
from urllib.parse import quote_plus
from .base import BaseSource, SourceError
from ..textproc import detect_language
from .base import raw_signal
class _Results(HTMLParser):
 def __init__(self): super().__init__();self.links=[];self._href=None;self._text=[]
 def handle_starttag(self,tag,attrs):
  if tag=="a" and "result__a" in dict(attrs).get("class",""): self._href=dict(attrs).get("href");self._text=[]
 def handle_data(self,data):
  if self._href: self._text.append(data)
 def handle_endtag(self,tag):
  if tag=="a" and self._href: self.links.append((self._href," ".join(self._text).strip()));self._href=None
class WebSearchSource(BaseSource):
 family="web_search"
 def collect(self,q:str,since: str|None=None):
  try:
   html=self.fetch_text(f"https://html.duckduckgo.com/html/?q={quote_plus(q)}")
   if "anomaly" in html.lower() or "captcha" in html.lower(): raise SourceError("blocked/anti-bot")
   parser=_Results();parser.feed(html); links=parser.links
  except SourceError:
   from .forums import parse_feed
   links=[(x["url"],x["title"] or x["body"]) for x in parse_feed(self.fetch_text(f"https://www.bing.com/search?q={quote_plus(q)}&format=rss"),"bing")]
  if not links: raise SourceError("coverage gap: DDG and Bing returned no public results")
  return [raw_signal(source="duckduckgo",family=self.family,external_id=url,url=url,query=q,title=title or "search result",body=title or "search result",lang=detect_language(title)) for url,title in links[:self.limit]]
