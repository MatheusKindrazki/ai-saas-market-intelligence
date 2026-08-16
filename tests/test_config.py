from pathlib import Path

from radar.config import Config, USER_AGENT


def test_defaults_are_safe_and_identifiable():
    cfg = Config()
    assert cfg.ua == USER_AGENT
    assert cfg.rate_limits["reddit"] == 10.0
    assert cfg.reddit_subreddits_per_run == 6
    assert len(cfg.pain_queries) >= 10
    assert cfg.feeds["reddit_subreddit"].endswith("/.rss")
    assert cfg.feeds["wordpress_support"].endswith("{slug}/")
    assert cfg.feeds["product_hunt"] == "https://www.producthunt.com/feed"
    assert "indie_hackers" in cfg.coverage_gaps


def test_env_overrides_db_and_runtime_paths(monkeypatch):
    monkeypatch.setenv("RADAR_DB", "/tmp/radar-test.db")
    cfg = Config.from_env()
    assert cfg.db_path == Path("/tmp/radar-test.db")
    assert cfg.cache_dir == Path("/tmp/cache")
