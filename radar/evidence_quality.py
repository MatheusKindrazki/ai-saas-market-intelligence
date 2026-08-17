"""Fail-closed evidence quality calibration for thesis confidence and BUILD gate.

Confidence rules (fail-closed):
  A: ≥2 independent demand-side sources AND ≥1 independent commercial/pricing/competitor source,
     every claim supported by relevant evidence, sources span at least two distinct domains/authors.
  B: ≥1 demand-side source AND ≥1 commercial source, but independence is weak (same domain/family).
  C: ≥1 relevant source, but only anecdotal demand or a single vendor claim.
  D: no relevant evidence, unsupported claims, or evidence is irrelevant/noise.

Recommendation rules:
  BUILD: confidence A or B, buyer candidates exist, competitor/pricing evidence exists,
         and buyer-validation evidence is already present.
  VALIDATE: confidence B or C, plausible buyer candidates and workflow pain, but no buyer
            validation yet; this is the default positive path.
  WATCH: confidence C, no clear buyer candidates or pricing.
  PASS: confidence D or no monetizable pain.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable

from .textproc import normalize_keywords, normalize_space, strip_tags


class EvidenceKind(str, Enum):
    DEMAND = "demand"
    COMMERCIAL = "commercial"
    WORKAROUND = "workaround"
    CHANNEL = "channel"
    IRRELEVANT = "irrelevant"
    NOISE = "noise"


class Confidence(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"


class Recommendation(str, Enum):
    BUILD = "BUILD"
    VALIDATE = "VALIDATE"
    WATCH = "WATCH"
    PASS = "PASS"


@dataclass(frozen=True)
class EvidenceItem:
    url: str
    title: str
    body: str
    kind: EvidenceKind
    supports_claim: bool
    independence: str  # domain, author, or source-family fingerprint


@dataclass(frozen=True)
class QualityVerdict:
    confidence: Confidence
    recommendation: Recommendation
    evidence: list[EvidenceItem] = field(default_factory=list)
    reasons: list[str] = field(default_factory=list)
    buyer_candidates: list[str] = field(default_factory=list)
    competitor_pricing: list[dict[str, Any]] = field(default_factory=list)


# Heuristic stopwords for relevance: if the only overlap is these, the match is spurious.
_GENERIC = {
    "the", "and", "for", "with", "this", "that", "from", "have", "need", "tool", "software",
    "how", "are", "was", "but", "not", "all", "can", "you", "your", "use", "using", "used",
    "what", "when", "where", "why", "who", "they", "them", "their", "there", "then", "than",
    "one", "two", "new", "old", "get", "got", "way", "now", "also", "only", "just", "like",
    "about", "would", "could", "should", "make", "made", "does", "did", "well", "very", "much",
    "many", "some", "more", "most", "other", "another", "such", "each", "every", "own",
    "good", "bad", "best", "better", "worse", "great", "small", "big", "want", "help",
}

# Phrases that flag clearly non-B2B/no-workflow/no-buyer content.
_NOISE_WORDS = {
    "mana", "potion", "spell", "character", "class", "pvp", "pvm", "raid", "dungeon",
    "deck", "card game", "trump", "biden", "democrat", "republican", "senate", "congress",
    "election", "political",
}
_NOISE_PHRASES = (
    "misattributed quote", "not applicable as a customer",
)

# Commercial/pricing signals.
_COMMERCIAL = (
    "price", "pricing", "cost", "costs", "euro", "eur", "usd", "$", "€", "paid", "pay",
    "subscription", "month", "year", "vendor", "competitor", "competing", "launch",
    "product", "platform", "solution", "provider", "service", "saas", "startup",
)

# Demand/workflow signals.
_DEMAND = (
    "hate", "manual", "spreadsheet", "takes hours", "too expensive", "looking for alternative",
    "wish there was", "how do you handle", "is there a tool", "paying someone",
    "cancelled", "frustrated", "every week", "every month", "every day", "stitching",
    "reconcile", "reconciliation", "integration", "workflow", "bottleneck",
)


# Claim-level verbatim gate. A citation proves nothing on its own — the model can append any
# collected URL to invented prose — so a claim must also repeat that source's own wording. The
# floor is both a word count and a character count: four filler words ("teams need a tool") overlap
# almost any evidence item, and one long word is not a quotation either.
MIN_EXCERPT_WORDS = 4
MIN_EXCERPT_CHARS = 20

_NON_WORD = re.compile(r"[^0-9a-zÀ-ɏ]+")  # casefolded latin letters and digits only


def _excerpt_words(text: str) -> list[str]:
    """Wording only: markup, punctuation and spacing differ between a quote and its source."""
    return _NON_WORD.sub(" ", normalize_space(strip_tags(text or ""))).split()


def verbatim_excerpt(claim: str, source_texts: Iterable[str]) -> str:
    """Longest run of words from `source_texts` that `claim` repeats verbatim, or "" if none.

    Fail-closed by construction: only the texts of the source actually being cited are searched,
    so an excerpt copied from a different collected item cannot back this citation.
    """
    claim_words = _excerpt_words(claim)
    if len(claim_words) < MIN_EXCERPT_WORDS:
        return ""
    haystack = f" {' '.join(claim_words)} "
    best = ""
    for text in source_texts:
        words = _excerpt_words(text)
        for start in range(len(words)):
            for end in range(start + MIN_EXCERPT_WORDS, len(words) + 1):
                span = " ".join(words[start:end])
                if len(span) < MIN_EXCERPT_CHARS:
                    continue
                # Word-boundary padded so 'work takes hours' cannot match 'homework takes hours'.
                if f" {span} " not in haystack:
                    break  # any longer span contains this absent one, so it is absent too
                if len(span) > len(best):
                    best = span
    return best


def _normalized(text: str) -> set[str]:
    words = normalize_keywords(strip_tags(text or "")) - _GENERIC
    # Cheap plural/singular normalization so 'spreadsheet' matches 'spreadsheets'.
    return words | {w[:-1] for w in words if len(w) > 3 and w.endswith("s")}


def is_relevant_to_cluster(item: EvidenceItem, cluster: dict[str, str], threshold: float = 0.08) -> bool:
    """Keyword overlap between evidence and cluster topic. Low threshold by design: we fail closed,
    so a weak overlap is treated as irrelevant unless the model later explicitly confirms it.
    """
    if item.kind == EvidenceKind.IRRELEVANT or not item.supports_claim:
        return False
    cluster_text = " ".join(cluster.get(k, "") for k in ("key_terms", "pain", "icp"))
    cluster_keywords = _normalized(cluster_text)
    if not cluster_keywords:
        return True  # no cluster terms to compare -> pass to next gate
    item_keywords = _normalized(f"{item.title} {item.body}")
    if not item_keywords:
        return False
    overlap = len(cluster_keywords & item_keywords)
    total = len(cluster_keywords)
    # Require at least one content keyword in common and a minimum relative overlap.
    return overlap >= 1 and (overlap / max(total, 1)) >= threshold


def classify_evidence(body: str, title: str = "", source_family: str = "") -> EvidenceKind:
    """Heuristic but deterministic classification of an evidence item."""
    text = normalize_space(f"{title} {body}")
    lower = text.lower()

    # Explicit noise first.
    words = set(re.findall(r"\b[a-z]+\b", lower))
    if words & _NOISE_WORDS:
        return EvidenceKind.NOISE
    if any(phrase in lower for phrase in _NOISE_PHRASES):
        return EvidenceKind.NOISE

    # Commercial/pricing/competitor signals.
    if any(token in lower for token in _COMMERCIAL):
        # If it also expresses a user pain, it's still commercial-ish (vendor-side evidence).
        return EvidenceKind.COMMERCIAL

    # Demand-side signals from community sources.
    if any(token in lower for token in _DEMAND):
        return EvidenceKind.DEMAND

    # Workaround/DIY scripts are evidence of a workflow pain.
    if any(token in lower for token in ("script", "zapier", "automation", "workaround", "bot")):
        return EvidenceKind.WORKAROUND

    # Channel evidence (where buyers congregate).
    if source_family in {"reddit", "hackernews", "stackexchange", "forums"} and len(text) > 40:
        return EvidenceKind.CHANNEL

    return EvidenceKind.IRRELEVANT


def _independence_key(item: EvidenceItem) -> str:
    # Domain + source family is a cheap proxy for independence.
    from urllib.parse import urlparse
    domain = urlparse(item.url).netloc.replace("www.", "")
    return f"{domain}|{item.independence}"


def score_confidence(
    evidence: list[EvidenceItem],
    cluster_topic: str,
    claims_supported: bool = True,
) -> QualityVerdict:
    """Apply fail-closed confidence calibration."""
    relevant = [e for e in evidence if e.kind not in {EvidenceKind.IRRELEVANT, EvidenceKind.NOISE}]
    demand = [e for e in relevant if e.kind == EvidenceKind.DEMAND]
    commercial = [e for e in relevant if e.kind == EvidenceKind.COMMERCIAL]
    workarounds = [e for e in relevant if e.kind == EvidenceKind.WORKAROUND]

    demand_independence = {_independence_key(e) for e in demand}
    commercial_independence = {_independence_key(e) for e in commercial}

    reasons: list[str] = []
    if not claims_supported:
        reasons.append("thesis claims are not all supported by collected evidence")
    if not relevant:
        reasons.append("no relevant evidence found")

    confidence: Confidence
    if (
        claims_supported
        and len(demand) >= 2
        and len(demand_independence) >= 2
        and len(commercial) >= 1
        and len(demand_independence | commercial_independence) >= 2
    ):
        confidence = Confidence.A
        reasons.append(
            f"{len(demand)} independent demand-side sources and {len(commercial)} independent "
            "commercial/pricing source(s)"
        )
    elif claims_supported and len(demand) >= 1 and len(commercial) >= 1:
        confidence = Confidence.B
        reasons.append(
            f"demand evidence ({len(demand)}) and commercial evidence ({len(commercial)}) "
            "but limited independence"
        )
    elif claims_supported and (len(demand) >= 1 or len(commercial) >= 1 or len(workarounds) >= 1):
        confidence = Confidence.C
        reasons.append("only anecdotal demand, a single vendor claim, or workaround evidence")
    else:
        confidence = Confidence.D
        if not reasons:
            reasons.append("no relevant demand or commercial evidence")

    buyer_candidates = [e.url for e in demand]
    competitor_pricing = [
        {"url": e.url, "snippet": (e.title + " " + e.body)[:200]}
        for e in commercial
    ]

    return QualityVerdict(
        confidence=confidence,
        recommendation=Recommendation.WATCH,  # placeholder; refined by score_recommendation
        evidence=evidence,
        reasons=reasons,
        buyer_candidates=buyer_candidates,
        competitor_pricing=competitor_pricing,
    )


def score_recommendation(
    quality: QualityVerdict,
    has_buyer_validation: bool = False,
) -> Recommendation:
    """Default to VALIDATE; BUILD only when buyer validation is already proven."""
    if quality.confidence in {Confidence.A, Confidence.B} and quality.buyer_candidates and quality.competitor_pricing:
        return Recommendation.BUILD if has_buyer_validation else Recommendation.VALIDATE
    if quality.confidence in {Confidence.B, Confidence.C} and quality.buyer_candidates:
        return Recommendation.VALIDATE
    if quality.confidence == Confidence.C:
        return Recommendation.WATCH
    return Recommendation.PASS


def is_monetizable_pain(pain: dict[str, str]) -> bool:
    """Filter pains that are clearly non-commercial, have no buyer, or describe no workflow."""
    pain_text = normalize_space(pain.get("pain", "")).lower()
    icp_text = normalize_space(pain.get("icp", "")).lower()
    wtp_text = normalize_space(pain.get("wtp_evidence", "")).lower()
    combined = f"{pain_text} {icp_text}"

    # Reject clear noise/gaming/politics.
    if any(phrase in combined for phrase in _NOISE_PHRASES):
        return False
    noise_words = set(re.findall(r"\b[a-z]+\b", combined))
    if noise_words & _NOISE_WORDS:
        return False

    # ICP must be a plausible business buyer (role, team, company, operator, manager, developer).
    # Consumer-only profiles and abstract HR/culture topics are not B2B SaaS buyers.
    if not re.search(
        r"\b(developer|engineer|manager|operator|founder|team|company|business|startup|agency|"
        r"studio|consultant|professional|analyst|lead|head|cto|ceo|owner|merchant|seller|vendor|"
        r"clinic|practice|hospital|school|studio|firm|shop|store|restaurant|hotel|park|campground|"
        r"operations|finance|accounting|marketing|sales|support|it |devops|data |product|"
        r"commerce|e-commerce|saas|b2b|enterprise|mid-market|small business)\b",
        icp_text,
    ):
        return False

    # The pain itself must describe a workflow, tool, process, integration, or explicit cost.
    # We look only at the pain and ICP; wtp_evidence is used only as a positive currency signal.
    workflow_markers = (
        r"\bmanual\b", r"\bspreadsheet\b", r"\bspreadsheets\b", r"\bhours\b", r"\bworkflow\b",
        r"\bworkflows\b", r"\btool\b", r"\btools\b", r"\bsoftware\b", r"\bprocess\b",
        r"\bprocesses\b", r"\bintegration\b", r"\bintegrations\b", r"\bautomation\b",
        r"\bautomate\b", r"\bcost\b", r"\bcosts\b", r"\bprice\b", r"\bpricing\b",
        r"\bexpensive\b", r"\bbudget\b", r"\bsubscription\b", r"\bvendor\b", r"\bvendors\b",
        r"\balternative\b", r"\balternatives\b", r"\breconcile\b", r"\breconciliation\b",
        r"\bstitch\b", r"\bsync\b", r"\bexport\b", r"\bimport\b", r"\bcsv\b", r"\bapi\b",
        r"\bduplicate\b", r"\berror\b", r"\bbroken\b", r"\bfails\b", r"\bdisconnected\b",
        # Data-plumbing work is a workflow even when none of the words above appear: catalog
        # normalization, taxonomy/attribute mapping and faceted search are B2B operations pains.
        # The noise-word and ICP gates above still keep gaming/politics out.
        r"\bcatalogu?e?s?\b", r"\bnormali[sz]\w*\b", r"\btaxonom(?:y|ies)\b", r"\battributes?\b",
        r"\bfacet(?:s|ed|ing)?\b", r"\bskus?\b", r"\bby hand\b", r"\bdedup\w*\b",
        r"\bdata entry\b", r"\bmapping\b",
    )
    has_workflow_marker = any(re.search(marker, combined) for marker in workflow_markers)

    # Actual willingness-to-pay signal: currency symbol or explicit amount, not just the word "pay".
    has_wtp_signal = bool(
        re.search(r"[\$€£¥]|\b\d+\s*(?:usd|eur|gbp|month|mo|year|yr|seat|user|monthly|annually)\b", wtp_text)
    )

    return has_workflow_marker or has_wtp_signal
