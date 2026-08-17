"""Search adapter retained for future compliant providers; public engines are unavailable."""
from __future__ import annotations

from .base import BaseSource, SourceError


WEB_SEARCH_COVERAGE_GAP = "coverage gap: all public search engines blocked or robots-disallowed"


class WebSearchSource(BaseSource):
    family = "web_search"

    def collect(self, q: str | tuple[str, ...] | list[str], since: str | None = None):
        raise SourceError(WEB_SEARCH_COVERAGE_GAP)
