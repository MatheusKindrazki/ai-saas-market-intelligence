"""Fail-closed evidence quality, confidence calibration and BUILD gate."""
from __future__ import annotations

from radar.evidence_quality import (
    Confidence,
    EvidenceItem,
    EvidenceKind,
    QualityVerdict,
    Recommendation,
    classify_evidence,
    is_relevant_to_cluster,
    is_monetizable_pain,
    score_confidence,
    score_recommendation,
    verbatim_excerpt,
)


def test_khmer_issue_irrelevant_to_dutch_holiday_park():
    """Regression: a Khmer language-learning issue must not count as evidence for holiday-park PMS."""
    cluster = {
        "key_terms": "holiday park campground pms channel manager dutch tourist tax",
        "pain": "Legacy park management software is too expensive and complex for small independent holiday parks",
        "icp": "small independent holiday park operators in the Netherlands",
    }
    item = EvidenceItem(
        url="https://github.com/Morningstar88/kalki-search/issues/223",
        title="Khmer language learning resources",
        body="I am trying to learn Khmer and need better search resources.",
        kind=EvidenceKind.DEMAND,
        supports_claim=False,
        independence="github",
    )
    assert not is_relevant_to_cluster(item, cluster)


def test_demand_pain_supports_cluster():
    cluster = {
        "key_terms": "holiday park campground pms channel manager",
        "pain": "small independent holiday parks need simple PMS",
        "icp": "holiday park operators",
    }
    item = EvidenceItem(
        url="https://news.ycombinator.com/item?id=48376362",
        title="Show HN: Odeva",
        body="Most park management software was built 10+ years ago for enterprise procurement, not for the receptionist or park manager.",
        kind=EvidenceKind.COMMERCIAL,
        supports_claim=True,
        independence="hackernews",
    )
    assert is_relevant_to_cluster(item, cluster)


def test_confidence_a_requires_two_demand_plus_independent_commercial():
    evidence = [
        EvidenceItem("u1", "Park operator complaint", "We pay too much for our PMS.", EvidenceKind.DEMAND, True, "reddit"),
        EvidenceItem("u2", "Another operator", "Channel manager fees are killing us.", EvidenceKind.DEMAND, True, "hackernews"),
        EvidenceItem("u3", "Competitor launch", "New Odeva PMS for holiday parks.", EvidenceKind.COMMERCIAL, True, "hackernews"),
    ]
    verdict = score_confidence(evidence, "Holiday park PMS", claims_supported=True)
    assert verdict.confidence == Confidence.A
    assert "2 demand-side" in verdict.reasons[0].lower() or "independent commercial" in verdict.reasons[0].lower()


def test_single_vendor_launch_is_not_confidence_a():
    """Vendor self-promotion alone cannot establish willingness to pay."""
    evidence = [
        EvidenceItem("u1", "Show HN: Odeva", "I built a PMS for holiday parks.", EvidenceKind.COMMERCIAL, True, "hackernews"),
    ]
    verdict = score_confidence(evidence, "Holiday park PMS", claims_supported=True)
    assert verdict.confidence != Confidence.A
    assert any("demand" in r.lower() for r in verdict.reasons)


def test_irrelevant_evidence_lowers_confidence_to_d():
    evidence = [
        EvidenceItem("u1", "Khmer learning", "I need Khmer resources.", EvidenceKind.IRRELEVANT, False, "github"),
    ]
    verdict = score_confidence(evidence, "Holiday park PMS", claims_supported=True)
    assert verdict.confidence == Confidence.D


def test_build_requires_confidence_a_and_buyer_candidates():
    quality = QualityVerdict(
        confidence=Confidence.A,
        recommendation=Recommendation.BUILD,
        evidence=[],
        reasons=["Strong evidence"],
        buyer_candidates=["park operator A"],
        competitor_pricing=[{"name": "Odeva", "pricing": "EUR 30/mo"}],
    )
    rec = score_recommendation(quality, has_buyer_validation=False)
    assert rec == Recommendation.VALIDATE


def test_build_needs_buyer_validation_or_explicit_market_signal():
    quality = QualityVerdict(
        confidence=Confidence.A,
        recommendation=Recommendation.BUILD,
        evidence=[],
        reasons=["Strong"],
        buyer_candidates=["park operator A"],
        competitor_pricing=[{"name": "Odeva", "pricing": "EUR 30/mo"}],
    )
    # Without buyer-validation interviews, fail-closed to VALIDATE.
    assert score_recommendation(quality, has_buyer_validation=False) == Recommendation.VALIDATE
    assert score_recommendation(quality, has_buyer_validation=True) == Recommendation.BUILD


def test_classify_detects_commercial_vs_demand():
    assert classify_evidence(
        "We pay EUR 500/month for our current PMS and it still misses channel manager integration.",
        source_family="hackernews",
    ) == EvidenceKind.COMMERCIAL
    assert classify_evidence(
        "I hate stitching together spreadsheets every weekend to reconcile bookings.",
        source_family="reddit",
    ) == EvidenceKind.DEMAND
    assert classify_evidence(
        "The backstab ability costs 12 mana which is too much for a thief.",
        source_family="github",
    ) == EvidenceKind.NOISE


def test_non_commercial_pain_is_filtered():
    pain = {
        "pain": "Backstab total mana cost is unsustainable",
        "icp": "end-game thief-class players in a hex-based MUD",
        "wtp_evidence": "",
    }
    assert not is_monetizable_pain(pain)


def test_political_pain_is_filtered():
    pain = {
        "pain": "Frustration over a misattributed quote",
        "icp": "Not applicable as a customer profile",
        "wtp_evidence": "",
    }
    assert not is_monetizable_pain(pain)


def test_b2b_supplier_catalog_normalization_pain_is_monetizable():
    """Codex P2: catalog/taxonomy/faceted-search work is a real commercial workflow, but the gate
    only knew 'manual/spreadsheet/integration' words and dropped it as non-monetizable.
    """
    pain = {
        "pain": "Supplier catalogue attributes arrive in a different taxonomy from each brand, so "
                "the team normalizes SKUs by hand before faceted search returns anything usable",
        "icp": "Merchandising lead at a B2B industrial distributor",
        "wtp_evidence": "",
    }
    assert is_monetizable_pain(pain)


def test_generalized_workflow_gate_still_rejects_gaming_noise():
    """The looser workflow words must not reopen the gaming/politics door."""
    gaming = {
        "pain": "Normalizing card deck attributes by hand before every raid is tedious",
        "icp": "Guild officers running raids in a hex-based MUD",
        "wtp_evidence": "",
    }
    political = {
        "pain": "Normalizing senate voting attributes by hand for each election cycle",
        "icp": "Volunteer team on a political campaign",
        "wtp_evidence": "",
    }
    assert not is_monetizable_pain(gaming)
    assert not is_monetizable_pain(political)


def test_b2b_workflow_pain_is_monetizable():
    pain = {
        "pain": "Manual spreadsheet reconciliation takes hours every week",
        "icp": "Operations teams at mid-market SaaS companies",
        "wtp_evidence": "We budgeted $500/month for automation.",
    }
    assert is_monetizable_pain(pain)


def test_verbatim_excerpt_ignores_html_punctuation_and_spacing():
    """The claim must repeat the source's wording, not its markup or its commas."""
    claim = 'Weekly intake is the wedge ("manual work takes hours") for operations teams.'

    assert verbatim_excerpt(claim, ["<p>Manual   work takes hours.</p>"]) == "manual work takes hours"


def test_verbatim_excerpt_returns_the_longest_supported_span():
    source = ["I hate stitching spreadsheets together every week."]
    claim = 'Ops teams "hate stitching spreadsheets together every week", so automate the intake.'

    assert verbatim_excerpt(claim, source) == "hate stitching spreadsheets together every week"


def test_verbatim_excerpt_rejects_a_paraphrase_of_the_source():
    """An invented restatement of the evidence is exactly what the gate exists to catch."""
    assert verbatim_excerpt("Manual spreadsheet work consumes many hours weekly.",
                            ["Manual work takes hours every single week."]) == ""


def test_verbatim_excerpt_rejects_spans_that_are_too_short_or_too_generic():
    """A handful of filler words overlaps almost any source, so it may not count as a quote."""
    assert verbatim_excerpt("Teams need a tool that fixes billing.", ["Teams need a tool."]) == ""
    assert verbatim_excerpt("It takes hours.", ["Manual work takes hours."]) == ""


def test_verbatim_excerpt_only_reads_the_texts_it_is_given():
    """Support is looked up per citation: another item's wording cannot back this one."""
    claim = 'Undercut the vendor ("manual work takes hours") at half the price.'

    assert verbatim_excerpt(claim, ["Our vendor charges $199/seat for the same workflow."]) == ""
