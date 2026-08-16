"""Public WordPress plugin review/support RSS subset."""
from .base import BaseSource, SourceError, raw_signal
class ReviewsSource(BaseSource):
 family="reviews"
 def collect(self, query_context: str, since: str|None=None, plugin: str="woocommerce"):
  from .forums import parse_feed
  rows=parse_feed(self.fetch_text(f"https://wordpress.org/support/rss/plugin/{plugin}/"),"wordpress")
  return self.keep_since([raw_signal(source="wordpress_reviews",family=self.family,query=query_context,lang="unknown",**x) for x in rows[:self.limit]],since)
