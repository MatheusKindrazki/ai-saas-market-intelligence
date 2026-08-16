"""Public WordPress support and Mozilla Add-ons review collectors."""
from __future__ import annotations

from datetime import date

from .base import BaseSource, SourceError, raw_signal
from ..textproc import detect_language


class ReviewsSource(BaseSource):
    family = "reviews"
    wordpress_plugins = ("woocommerce", "jetpack", "contact-form-7", "woocommerce-services", "wordpress-seo")
    amo_addons = ("ublock-origin", "darkreader", "bitwarden-password-manager", "grammarly-1")

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
        wordpress = [raw_signal(source="wordpress_reviews", family=self.family, query=query_context, lang=detect_language(row["body"]), **row) for row in wordpress_rows[:self.limit] if row["body"]]

        addon = self.selected_amo_addon()
        try:
            amo_data = self.fetch_json(f"https://addons.mozilla.org/api/v5/addons/addon/{addon}/reviews/?lang=en-US")
        except SourceError as exc:
            raise SourceError(f"AMO reviews {addon}: {exc}") from exc
        results = amo_data.get("results") if isinstance(amo_data, dict) else None
        if not results:
            raise SourceError(f"AMO reviews {addon}: empty results")
        amo = []
        for row in results[:self.limit]:
            body = (row.get("body") or "").strip()
            if not body:
                continue
            user = row.get("user") or {}
            amo.append(raw_signal(source="amo_reviews", family=self.family, external_id=str(row["id"]), url=row.get("url") or f"https://addons.mozilla.org/en-US/firefox/addon/{addon}/reviews/{row['id']}/", query=query_context, title=f"{addon} review", body=body, author=user.get("username") or user.get("name"), published_at=row.get("created"), lang=detect_language(body)))
        if not amo:
            raise SourceError(f"AMO reviews {addon}: empty review bodies")
        return self.keep_since(wordpress + amo, since)
