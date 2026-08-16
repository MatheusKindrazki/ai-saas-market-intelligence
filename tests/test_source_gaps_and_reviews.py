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


def test_reviews_maps_amo_json_and_rotates_plugins(monkeypatch):
    source = ReviewsSource(limit=5)
    monkeypatch.setattr(source, "selected_wordpress_plugin", lambda: "jetpack")
    monkeypatch.setattr(source, "selected_amo_addon", lambda: "ublock-origin")
    monkeypatch.setattr(source, "fetch_text", lambda url: '<rss><channel><item><guid>wp-1</guid><title>Broken</title><description>Too much manual work</description><link>https://wordpress.org/x</link></item></channel></rss>')
    monkeypatch.setattr(source, "fetch_json", lambda url: {"results": [{
        "id": 99, "body": "This update makes my workflow much harder.", "created": "2026-08-15T00:00:00Z",
        "user": {"username": "reviewer"}, "url": "https://addons.mozilla.org/review/99",
    }]})

    signals = source.collect("manual work")

    amo = next(signal for signal in signals if signal.source == "amo_reviews")
    assert amo.external_id == "99"
    assert amo.author_pseudonym is not None
    assert amo.body == "This update makes my workflow much harder."
    assert source._rotated_slug(("a", "b", "c")) == ("a", "b", "c")[date.today().toordinal() % 3]
