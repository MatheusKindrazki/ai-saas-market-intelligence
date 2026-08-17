"""Public WordPress support and Mozilla Add-ons review collectors."""
from __future__ import annotations

from datetime import date

from .base import BaseSource, SourceError, raw_signal
from ..textproc import detect_language


class ReviewsSource(BaseSource):
    family = "reviews"
    wordpress_plugins = ("woocommerce", "jetpack", "contact-form-7", "woocommerce-services", "wordpress-seo")
    amo_addons = ("ublock-origin", "darkreader", "bitwarden-password-manager", "grammarly-1")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.errors: list[tuple[str, str]] = []

    @staticmethod
    def _rotated_slug(slugs: tuple[str, ...]) -> str:
        return slugs[date.today().toordinal() % len(slugs)]

    def selected_wordpress_plugin(self) -> str:
        return self._rotated_slug(self.wordpress_plugins)

    def selected_amo_addon(self) -> str:
        return self._rotated_slug(self.amo_addons)

    def collect(self, query_context: str, since: str | None = None, plugin: str | None = None):
        from .forums import parse_feed

        wordpress_slug = plugin or self.selected_wordpress_plugin()
        wordpress_rows = parse_feed(self.fetch_text(f"https://wordpress.org/support/rss/plugin/{wordpress_slug}/"), "wordpress")
        wordpress = [raw_signal(source="wordpress_reviews", family=self.family, query=query_context, lang=detect_language(row["body"]), cfg=self.cfg, **row) for row in wordpress_rows[:self.limit] if row["body"]]

        # Two independent providers: an AMO outage must not discard the WordPress signals already in hand.
        self.errors = []
        try:
            amo = self.amo_reviews(self.selected_amo_addon(), query_context)
        except SourceError as exc:
            self.errors.append(("amo_reviews", str(exc)))
            amo = []
        return self.keep_since(wordpress + amo, since)

    def amo_reviews(self, addon: str, query_context: str):
        """Reviews via the public add-on review-list page.

        The api/v5 ``.../reviews/`` endpoint returns 404 (verified 2026-08-16);
        the review-list HTML page is public, robots-allowed, and embeds the
        full review records as an application/json script blob.
        """
        import json as _json
        import re as _re

        try:
            html = self.fetch_text(f"https://addons.mozilla.org/en-US/firefox/addon/{addon}/reviews/")
        except SourceError as exc:
            raise SourceError(f"AMO reviews {addon}: {exc}") from exc
        match = _re.search(r'<script[^>]*type="application/json"[^>]*>(.*?)</script>', html, _re.S)
        state = None
        if match:
            try:
                state = _json.loads(match.group(1))
            except ValueError:
                state = None
        records = []
        if isinstance(state, dict):
            by_id = state.get("reviews", {}).get("byId", {})
            records = [by_id[str(rid)] for rid in state.get("reviews", {}).get("byAddon", {}).get(addon, {}).get("data", {}).get("reviews", []) if str(rid) in by_id]
        amo = []
        for row in records[:self.limit]:
            body = (row.get("body") or "").strip()
            if not body:
                continue
            amo.append(raw_signal(source="amo_reviews", family=self.family, external_id=str(row["id"]), url=f"https://addons.mozilla.org/en-US/firefox/addon/{addon}/reviews/", query=query_context, title=f"{addon} review ({row.get('score')} stars)", body=body, author=row.get("userName"), published_at=row.get("created"), lang=detect_language(body), cfg=self.cfg))
        if not amo:
            raise SourceError(f"AMO reviews {addon}: no review bodies on public page")
        return amo
