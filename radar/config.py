"""Runtime configuration and the deliberately small public-source registry."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

USER_AGENT = "DeepOpportunityRadar/1.0 (+https://github.com/MatheusKindrazki/ai-saas-market-intelligence)"
LLM_ENDPOINT = "https://api.z.ai/api/anthropic/v1/messages"


@dataclass(frozen=True)
class Config:
    db_path: Path = Path("radar_runtime/radar.db")
    cache_dir: Path = Path("radar_runtime/cache")
    salt_path: Path = Path("radar_runtime/secretsalt")
    ua: str = USER_AGENT
    rate_limits: dict[str, float] = field(default_factory=lambda: {
        "reddit": 2.0, "hackernews": 2.0, "github": 2.0,
        "stackexchange": 2.0, "forums": 2.0, "websearch": 2.0, "reviews": 2.0,
    })
    llm_endpoint: str = LLM_ENDPOINT
    llm_model: str = "glm-5.3"
    subreddits: tuple[str, ...] = ("SaaS", "smallbusiness", "sysadmin", "webdev")
    pain_queries: tuple[str, ...] = (
        "manual spreadsheet", "too expensive", "looking for alternative", "takes hours",
    )
    feeds: dict[str, str] = field(default_factory=lambda: {
        "reddit_subreddit": "https://www.reddit.com/r/{subreddit}/.rss",
        "product_hunt": "https://www.producthunt.com/feed",
        "wordpress_support": "https://wordpress.org/support/rss/plugin/{slug}/",
        "bing_rss": "https://www.bing.com/search?q={query}&format=rss",
        "duckduckgo_html": "https://html.duckduckgo.com/html/?q={query}",
    })
    coverage_gaps: dict[str, str] = field(default_factory=lambda: {
        "indie_hackers": "feed.rss is Cloudflare-blocked (403); no live feed is shipped.",
        "atlassian_community": "The documented community RSS endpoint returns 404.",
        "reddit_search": "search.rss is rate-limited (429); per-subreddit Atom RSS is used instead.",
    })

    @classmethod
    def from_env(cls) -> "Config":
        db_path = Path(os.environ.get("RADAR_DB", "radar_runtime/radar.db"))
        return cls(db_path=db_path, cache_dir=db_path.parent / "cache", salt_path=db_path.parent / "secretsalt")
