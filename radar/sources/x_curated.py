"""X is intentionally disabled without configured access."""
from .base import BaseSource, SourceError
class XCuratedSource(BaseSource):
 family="x_curated"
 def collect(self, query_context: str, since: str|None=None): raise SourceError("coverage gap: X access not configured")
