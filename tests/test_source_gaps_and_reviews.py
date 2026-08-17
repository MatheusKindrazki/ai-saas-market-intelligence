from __future__ import annotations

from datetime import date

import pytest

from radar.sources.base import SourceError
from radar.sources.forums import ForumsSource
from radar.sources.reddit import REDDIT_COVERAGE_GAP, RedditSource
from radar.sources.reviews import ReviewsSource


def test_reddit_raises_documented_coverage_gap():
    with pytest.raises(SourceError) as error:
        RedditSource().collect("manual work")
    assert str(error.value) == REDDIT_COVERAGE_GAP


def test_forums_maps_devto_json(monkeypatch):
    source = ForumsSource(limit=5)
    monkeypatch.setattr(source, "selected_tag", lambda: "saas")
    monkeypatch.setattr(source, "fetch_json", lambda url: [{
        "id": 42, "title": "A costly manual workflow", "description": "I do this by hand every week.",
        "url": "https://dev.to/example/workflow-42", "published_at": "2026-08-16T00:00:00Z",
        "user": {"username": "maker"},
    }])

    signal = source.collect("manual work")[0]

    assert signal.source == "devto"
    assert signal.external_id == "42"
    assert signal.url == "https://dev.to/example/workflow-42"
    assert signal.body == "I do this by hand every week."
    assert signal.published_at == "2026-08-16T00:00:00Z"


def test_reviews_maps_amo_page_state_and_rotates_plugins(monkeypatch):
    source = ReviewsSource(limit=5)
    amo_html = ('<html><head></head><body>'
                '<script type="application/json">'
                '{"reviews": {"byId": {"99": {"id": 99, "body": "This update makes my workflow much harder.", '
                '"created": "2026-08-15T00:00:00Z", "score": 2, "userName": "reviewer"}}, '
                '"byAddon": {"ublock-origin": {"data": {"reviews": [99]}}}}}'
                '</script></body></html>')
    monkeypatch.setattr(source, "selected_wordpress_plugin", lambda: "jetpack")
    monkeypatch.setattr(source, "selected_amo_addon", lambda: "ublock-origin")
    monkeypatch.setattr(source, "fetch_text", lambda url: amo_html if "addons.mozilla" in url else '<rss><channel><item><guid>wp-1</guid><title>Broken</title><description>Too much manual work</description><link>https://wordpress.org/x</link></item></channel></rss>')

    signals = source.collect("manual work")

    amo = next(signal for signal in signals if signal.source == "amo_reviews")
    assert amo.external_id == "99"
    assert amo.author_pseudonym is not None
    assert amo.body == "This update makes my workflow much harder."
    assert amo.published_at == "2026-08-15T00:00:00Z"
    assert source._rotated_slug(("a", "b", "c")) == ("a", "b", "c")[date.today().toordinal() % 3]
    assert source.errors == []


def test_reviews_keeps_wordpress_signals_when_amo_fails(monkeypatch):
    """An AMO outage used to throw away the WordPress items collected in the same call."""
    source = ReviewsSource(limit=5)
    monkeypatch.setattr(source, "selected_wordpress_plugin", lambda: "jetpack")
    monkeypatch.setattr(source, "selected_amo_addon", lambda: "ublock-origin")

    def fetch_text(url: str) -> str:
        if "addons.mozilla" in url:
            raise SourceError("HTTP 503")
        return '<rss><channel><item><guid>wp-1</guid><title>Broken</title><description>Too much manual work</description><link>https://wordpress.org/x</link></item></channel></rss>'

    monkeypatch.setattr(source, "fetch_text", fetch_text)

    signals = source.collect("manual work")

    assert [signal.source for signal in signals] == ["wordpress_reviews"]
    assert source.errors == [("amo_reviews", "AMO reviews ublock-origin: HTTP 503")]


def test_reviews_wordpress_failure_still_fails_the_family(monkeypatch):
    source = ReviewsSource(limit=5)
    monkeypatch.setattr(source, "fetch_text", lambda url: (_ for _ in ()).throw(SourceError("HTTP 500")))

    with pytest.raises(SourceError):
        source.collect("manual work")
