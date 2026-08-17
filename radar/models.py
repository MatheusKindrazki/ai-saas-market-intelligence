"""Validated domain models for collected public signals."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
from typing import Any
from urllib.parse import urlparse
import uuid


@dataclass(frozen=True)
class RawSignal:
    id: str; source: str; source_family: str; external_id: str; url: str
    title: str; body: str; author_pseudonym: str | None; published_at: str | None
    collected_at: str; query: str | None; lang: str; content_hash: str
    fetch_status: str = "ok"; http_status: int | None = None


@dataclass(frozen=True)
class Pain:
    id: str; signal_id: str; pain: str; icp: str; jtbd: str; context: str
    frequency: str; impact: str; workaround: str; wtp_evidence: str
    current_solution: str; dissatisfaction_reason: str; quotes: tuple[dict[str, object], ...]
    observed: tuple[str, ...]; inference: tuple[str, ...]; confidence: str; lang: str
    classified_at: str; model: str


@dataclass(frozen=True)
class Cluster:
    id: str; key_terms: str; member_pain_ids: tuple[str, ...]; created_at: str


@dataclass(frozen=True)
class Score:
    pain_id: str; dimensions: dict[str, float]; total: float; verdict: str
    reasons: tuple[str, ...]; scored_at: str


@dataclass(frozen=True)
class Thesis:
    id: str; cycle_id: str; recommendation: str; icp: str; offer: str; price: str
    mvp_48h: str; concierge: str; outreach_msgs: tuple[str, ...]; kill_criteria: tuple[str, ...]
    evidence_ids: tuple[str, ...]; confidence: str; created_at: str; cycle_date: str
    evidence_matrix: tuple[dict[str, Any], ...] = ()
    confidence_reason: str = ""
    recommendation_kind: str = ""


@dataclass(frozen=True)
class CoverageEntry:
    run_id: str; source: str; family: str; attempted: int; collected: int; errors: int
    window_start: str; window_end: str; notes: str; ts: str; error_details: tuple[str, ...] = ()


@dataclass(frozen=True)
class RunRecord:
    id: str; kind: str; started_at: str; ended_at: str | None; status: str; detail: dict[str, object]


@dataclass(frozen=True)
class SignalError:
    source: str; run_id: str | None; error: str; ts: str


class SourceFamily(str, Enum):
    REDDIT = "reddit"; HACKERNEWS = "hackernews"; GITHUB = "github"; STACKEXCHANGE = "stackexchange"
    REVIEWS = "reviews"; FORUMS = "forums"; WEB_SEARCH = "web_search"; X_CURATED = "x_curated"


class Confidence(str, Enum):
    A_VERIFIED = "A_verified"; B_OFFICIAL = "B_official"; C_MARKETING = "C_marketing"; D_UNVERIFIED = "D_unverified"


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class Signal:
    id: str
    url: str
    source: str
    source_family: SourceFamily
    query: str
    title: str
    body: str
    author_pseudonym: str | None
    published_at: datetime | None
    collected_at: datetime
    content_hash: str
    language: str
    confidence: Confidence
    raw_metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id or not self.source or not self.query or not self.title or not self.body:
            raise ValueError("id, source, query, title, and body are required")
        if not urlparse(self.url).scheme in {"http", "https"}:
            raise ValueError("url must be an absolute HTTP(S) URL")
        if len(self.content_hash) != 64 or any(c not in "0123456789abcdef" for c in self.content_hash):
            raise ValueError("content_hash must be a SHA-256 hex digest")
        if self.collected_at.tzinfo is None:
            raise ValueError("collected_at must be timezone-aware")
        if self.published_at is not None and self.published_at.tzinfo is None:
            raise ValueError("published_at must be timezone-aware")
        if self.language not in {"en", "pt", "es", "unknown"}:
            raise ValueError("unsupported language")

    @classmethod
    def make(cls, *, url: str, source: str, source_family: SourceFamily, query: str,
             title: str, body: str, author_pseudonym: str | None = None,
             published_at: datetime | None = None, language: str = "unknown",
             confidence: Confidence = Confidence.D_UNVERIFIED,
             raw_metadata: dict[str, Any] | None = None) -> "Signal":
        digest = hashlib.sha256(f"{url.strip()}\n{title.strip()}\n{body.strip()}".encode()).hexdigest()
        return cls(str(uuid.uuid4()), url, source, source_family, query, title, body,
                   author_pseudonym, published_at, utcnow(), digest, language, confidence,
                   raw_metadata or {})
