import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from radar.db import Database
from radar.models import Pain, RawSignal, Score
from radar.run_cycle import _cluster_terms, deep_validate
from radar.validate import validate_cluster


class FakeSearch:
    def collect(self, query):
        return [
            {"url": "https://reddit.example/one", "title": "One", "body": "Manual work takes hours."},
            {"url": "https://news.ycombinator.com/two", "title": "Two", "body": "I hate stitching spreadsheets together every week."},
            {"url": "https://evidence.test/three", "title": "Three", "body": "Teams need automation."},
            {"url": "https://competitor.example/four", "title": "Four", "body": "Our current spreadsheet vendor charges $199/seat for the same manual workflow."},
        ]


# Confidence is calibrated from the evidence the thesis actually cites AND quotes, so a thesis
# that should reach A has to carry a verbatim excerpt of two independent demand items plus the
# commercial one. Each excerpt below is copied out of that exact item's body.
CITED_A = ('https://reddit.example/one ("manual work takes hours"), '
           'https://news.ycombinator.com/two ("hate stitching spreadsheets together every week") '
           'and https://competitor.example/four ("charges $199/seat for the same manual workflow")')
# The pain payload the model is shown; a pain-ID citation needs its own excerpt too.
PAIN_QUOTE = 'pain-1 ("manual spreadsheet work takes hours")'


class FakeLLM:
    def __init__(self, recommendation):
        self.recommendation = recommendation

    def classify(self, content, schema=None, max_tokens=None):
        if "Research evidence" in content:
            return {"competitors": [], "negative_patterns": [], "diy_alternatives": [], "acquisition_channels": [], "buyers": []}
        return {
            "recommendation": self.recommendation,
            "icp": "Operations teams",
            "offer": "Automate weekly intake using " + self.recommendation.split("using ", 1)[-1],
            "price": "$99/month",
            "mvp_48h": "Import a spreadsheet and produce a report.",
            "concierge": "Run the workflow manually for five teams.",
            "outreach_msgs": ["We saw this recurring workflow."],
            "kill_criteria": ["Fewer than three interviews booked."],
        }


def seed_signal(db, suffix, quote):
    """A pain only counts while its quote still occurs in the signal it was mined from."""
    db.upsert_signal(RawSignal(
        f"signal-{suffix}", "reddit", "reddit", suffix, f"https://reddit.example/{suffix}", "t",
        f"Honestly, {quote} and nobody owns it.", None, None, "2026-08-16", "q", "en", "c" * 64,
    ))


def seed_pain(db, total=18):
    now = datetime.now(timezone.utc).isoformat()
    quote = "manual spreadsheet work takes hours"
    seed_signal(db, "1", quote)
    pain = Pain(
        "pain-1", "signal-1", "Manual spreadsheet work takes hours", "Operations teams",
        "Finish weekly reporting", "Weekly reporting is manual", "weekly", "hours lost",
        "spreadsheets", "budget approved", "none", "too slow",
        ({"quote": quote, "url": "https://reddit.example/1", "verified": True},), (quote,), (),
        "A", "en", now, "test",
    )
    db.add_pain(pain)
    db.add_score(Score(pain.id, {"severity": 5}, total, "include", ("test",), now))


def test_cluster_terms_keep_content_words_only():
    """A live run searched 'The Model column is too' and got 60 irrelevant items back."""
    pain = SimpleNamespace(
        pain="The Model column is too computationally expensive to run on the scheduled cron path",
        icp="Data engineers maintaining cron pipelines",
    )

    terms = _cluster_terms([pain]).split()

    assert "model" in terms and "cron" in terms
    assert not {"the", "is", "to", "on"} & set(terms)
    assert all(len(term) >= 3 for term in terms)


def test_deep_persists_verified_thesis_and_cluster(tmp_path):
    db = Database(tmp_path / "radar.db")
    seed_pain(db)

    thesis = deep_validate(db, None, FakeLLM(f"Build this for {PAIN_QUOTE} using {CITED_A}."), FakeSearch())

    assert thesis is not None
    assert thesis.confidence == "A"
    assert db.connection.execute("SELECT COUNT(*) FROM clusters").fetchone()[0] == 1
    assert db.connection.execute("SELECT COUNT(*) FROM theses").fetchone()[0] == 1


def test_deep_ignores_a_pain_whose_quote_left_its_signal(tmp_path):
    """A thesis cites the pain IDs it was synthesized from, so a stale pain must not reach it."""
    db = Database(tmp_path / "radar.db")
    seed_pain(db)
    db.connection.execute("UPDATE signals SET body='The author rewrote this post.' WHERE id='signal-1'")
    db.connection.commit()

    thesis = deep_validate(db, None, FakeLLM(f"Build this for {PAIN_QUOTE} using {CITED_A}."), FakeSearch())

    assert thesis is None
    assert db.connection.execute("SELECT COUNT(*) FROM theses").fetchone()[0] == 0
    detail = json.loads(db.connection.execute("SELECT detail_json FROM runs WHERE kind='deep'").fetchone()[0])
    assert detail["monetizable_pains"] == 0


def test_deep_rejects_thesis_with_no_known_evidence_reference(tmp_path):
    db = Database(tmp_path / "radar.db")
    seed_pain(db)

    with pytest.raises(ValueError, match="evidence"):
        deep_validate(db, None, FakeLLM("Build this using https://invented.test/proof."), FakeSearch())

    assert db.connection.execute("SELECT COUNT(*) FROM theses").fetchone()[0] == 0
    assert db.connection.execute("SELECT COUNT(*) FROM signal_errors").fetchone()[0] == 1


def test_deep_rejects_invented_prose_with_a_real_url_appended(tmp_path):
    """Codex P1 (round 2): pasting any collected URL after invented prose used to satisfy the gate.

    Nothing in the claim — least of all the $499/seat price — comes from the item it cites.
    """
    db = Database(tmp_path / "radar.db")
    seed_pain(db)
    invented = ("Charge $499/seat for an AI intake copilot; buyers are already asking for it. "
                "https://reddit.example/one.")

    with pytest.raises(ValueError, match="verbatim"):
        deep_validate(db, None, FakeLLM(invented), FakeSearch())

    assert db.connection.execute("SELECT COUNT(*) FROM theses").fetchone()[0] == 0
    assert db.connection.execute("SELECT COUNT(*) FROM signal_errors").fetchone()[0] == 1


def test_deep_rejects_an_excerpt_borrowed_from_another_collected_item(tmp_path):
    """The excerpt has to belong to the source it is attached to, not to any collected item."""
    db = Database(tmp_path / "radar.db")
    seed_pain(db)
    borrowed = 'Vendors charge $499/seat using https://competitor.example/four ("manual work takes hours").'

    with pytest.raises(ValueError, match="verbatim"):
        deep_validate(db, None, FakeLLM(borrowed), FakeSearch())

    assert db.connection.execute("SELECT COUNT(*) FROM theses").fetchone()[0] == 0


def test_deep_rejects_an_excerpt_of_a_few_generic_words(tmp_path):
    """A two-word overlap fits almost any evidence item, so it cannot stand in for a quote."""
    db = Database(tmp_path / "radar.db")
    seed_pain(db)
    generic = 'Build this for pain-1 ("takes hours") using https://reddit.example/one ("takes hours").'

    with pytest.raises(ValueError, match="verbatim"):
        deep_validate(db, None, FakeLLM(generic), FakeSearch())

    assert db.connection.execute("SELECT COUNT(*) FROM theses").fetchone()[0] == 0


def test_confidence_counts_only_the_citations_the_claim_quotes(tmp_path):
    """Codex P1 (round 2): confidence A/B is unreachable by appending unquoted URLs.

    The same three URLs reach A in test_deep_persists_verified_thesis_and_cluster because each one
    is quoted there; here only the first is, so the other two are inert and the thesis is a C.
    """
    db = Database(tmp_path / "radar.db")
    seed_pain(db)
    padded = (f'Build this for {PAIN_QUOTE} using https://reddit.example/one ("manual work takes hours"), '
              "https://news.ycombinator.com/two and https://competitor.example/four.")

    thesis = deep_validate(db, None, FakeLLM(padded), FakeSearch())

    assert thesis is not None
    assert thesis.confidence == "C"
    assert {row["url"] for row in thesis.evidence_matrix} == {"https://reddit.example/one"}
    assert set(thesis.evidence_ids) == {"pain-1", "https://reddit.example/one"}


def test_deep_accepts_a_thesis_that_quotes_every_source_it_cites(tmp_path):
    """Positive gate regression: excerpt tied to each cited URL and to the cited pain."""
    db = Database(tmp_path / "radar.db")
    seed_pain(db)

    thesis = deep_validate(db, None, FakeLLM(f"Build this for {PAIN_QUOTE} using {CITED_A}."), FakeSearch())

    assert thesis is not None and thesis.confidence == "A"
    assert set(thesis.evidence_ids) == {"pain-1", "https://reddit.example/one",
                                        "https://news.ycombinator.com/two",
                                        "https://competitor.example/four"}


def test_deep_accepts_recommendation_and_offer_quoting_different_sources(tmp_path):
    """The gate is claim-level: each field stands on its own citation and its own excerpt."""
    db = Database(tmp_path / "radar.db")
    seed_pain(db)

    class SplitCitationLLM(FakeLLM):
        def __init__(self):
            super().__init__(
                f'Build this for {PAIN_QUOTE} using https://reddit.example/one ("manual work takes hours") '
                'and https://news.ycombinator.com/two ("hate stitching spreadsheets together every week").')

        def classify(self, content, schema=None, max_tokens=None):
            result = super().classify(content, schema, max_tokens)
            if "recommendation" in result:
                result["offer"] = ('Undercut https://competitor.example/four '
                                   '("charges $199/seat for the same manual workflow") with a flat fee.')
            return result

    thesis = deep_validate(db, None, SplitCitationLLM(), FakeSearch())

    assert thesis is not None and thesis.confidence == "A"
    assert {row["url"] for row in thesis.evidence_matrix} == {
        "https://reddit.example/one", "https://news.ycombinator.com/two", "https://competitor.example/four"}


def test_deep_is_silent_when_no_cluster_clears_score_bar(tmp_path):
    db = Database(tmp_path / "radar.db")
    seed_pain(db, total=14)

    assert deep_validate(db, None, FakeLLM("Build this for pain-1."), FakeSearch()) is None
    assert db.connection.execute("SELECT COUNT(*) FROM theses").fetchone()[0] == 0


class BulkSearch:
    """Real adapters return up to 60 long items; the prompt must not carry them all.

    The three CITED_A urls lead so a bulk run can still reach A under the cited-and-quoted
    confidence rules; the other 57 exist to exercise the item cap and body truncation.
    """
    def collect(self, query):
        long_tail = "B" * 5000
        return [
            {"url": "https://reddit.example/one", "title": "Manual spreadsheet intake", "body": "Manual work takes hours. " + long_tail},
            {"url": "https://news.ycombinator.com/two", "title": "Weekly reporting bottleneck", "body": "I hate stitching spreadsheets together every week for the operations team. " + long_tail},
            {"url": "https://competitor.example/four", "title": "Vendor pricing page", "body": "Our current spreadsheet vendor charges $199/seat for the same manual workflow. " + long_tail},
        ] + [{"url": f"https://evidence.test/{i}", "title": "T" * 400, "body": "Manual intake is cited here. " + long_tail} for i in range(57)]


def test_validate_cluster_prompt_caps_items_and_excerpts_bodies():
    prompts = []
    claim = {"url": "https://evidence.test/0", "quote": "Manual intake is cited here.", "confidence": "A"}

    class RecordingLLM:
        def classify(self, content, schema=None):
            prompts.append(content)
            return {"competitors": [claim]}

    output = validate_cluster(SimpleNamespace(key_terms="manual work"), BulkSearch(), RecordingLLM())

    assert prompts[0].count("https://evidence.test/") <= 15
    assert len(prompts[0]) < 8000
    assert "B" * 400 not in prompts[0]
    assert output["competitors"] == [claim]


class CitationLLM:
    def __init__(self, claims):
        self.claims = claims

    def classify(self, content, schema=None):
        return {"competitors": self.claims}


class TaggedSearch:
    def collect(self, query):
        return [{"url": "https://evidence.test/one", "title": "Weekly intake", "body": "Our <b>manual</b> intake   takes hours every week."}]


def test_validate_cluster_drops_claims_citing_urls_outside_the_evidence():
    """The model invents plausible URLs; only collected evidence may back a claim."""
    output = validate_cluster(SimpleNamespace(key_terms="manual work"), TaggedSearch(),
                              CitationLLM([{"url": "https://invented.test/report", "quote": "manual intake takes hours every week"}]))

    assert output["competitors"] == []


def test_validate_cluster_drops_claims_whose_quote_is_not_in_that_evidence_item():
    output = validate_cluster(SimpleNamespace(key_terms="manual work"), TaggedSearch(),
                              CitationLLM([{"url": "https://evidence.test/one", "quote": "priced at $49 per seat"}, {"url": "https://evidence.test/one"}]))

    assert output["competitors"] == []


def test_validate_cluster_keeps_quotes_found_in_the_cited_evidence():
    claims = [{"url": "https://evidence.test/one", "quote": "manual intake takes hours every week"},
              {"url": "https://evidence.test/one", "quote": "Weekly intake"}]

    output = validate_cluster(SimpleNamespace(key_terms="manual work"), TaggedSearch(), CitationLLM(claims))

    assert output["competitors"] == claims


def test_deep_thesis_prompt_is_bounded_and_json_serialisable(tmp_path):
    db = Database(tmp_path / "radar.db")
    seed_pain(db)
    prompts = []

    class RecordingLLM(FakeLLM):
        def classify(self, content, schema=None, max_tokens=None):
            prompts.append(content)
            return super().classify(content, schema)

    thesis = deep_validate(db, None, RecordingLLM(f"Build this for {PAIN_QUOTE} using {CITED_A}."), BulkSearch())

    assert thesis is not None and thesis.confidence == "A"
    payload = json.loads(prompts[-1].split("(DATA): ", 1)[1])
    assert len(payload["evidence"]) <= 20
    assert all(len(item["body"]) <= 200 for item in payload["evidence"])
    assert len(prompts[-1]) < 12000


def test_deep_thesis_call_asks_for_a_bigger_output_budget_than_validation(tmp_path):
    """The thesis JSON is large; at the 4k client default it came back cut mid-string."""
    db = Database(tmp_path / "radar.db")
    seed_pain(db)
    budgets = []

    class RecordingLLM(FakeLLM):
        def classify(self, content, schema=None, max_tokens=None):
            budgets.append(max_tokens)
            return super().classify(content, schema)

    assert deep_validate(db, None, RecordingLLM(f"Build this for {PAIN_QUOTE} using {CITED_A}."), FakeSearch()) is not None
    assert budgets[-1] == 16000
    assert budgets[:-1] == [None] * (len(budgets) - 1)


def test_pain_id_citation_alone_cannot_borrow_uncited_topical_evidence(tmp_path):
    """Codex P1: an empty cited-URL set is vacuously a subset of the evidence, so four topical
    search hits (two independent demand + one commercial) used to hand a pain-ID-only thesis an A.
    """
    db = Database(tmp_path / "radar.db")
    seed_pain(db)

    class PainIdOnlyLLM(FakeLLM):
        def classify(self, content, schema=None, max_tokens=None):
            result = super().classify(content, schema, max_tokens)
            if "recommendation" in result:
                result["offer"] = f"Automate weekly intake for {PAIN_QUOTE}."
            return result

    thesis = deep_validate(db, None, PainIdOnlyLLM(f"Build this for {PAIN_QUOTE}."), FakeSearch())

    assert thesis is None
    assert db.connection.execute("SELECT COUNT(*) FROM theses").fetchone()[0] == 0


def test_watch_grade_thesis_without_buyers_is_not_persisted(tmp_path):
    """The contract needs reachable buyers AND commercial evidence. One cited vendor page and no
    buyers scores WATCH, which must fail closed to 'no thesis' instead of shipping a weak thesis.
    """
    db = Database(tmp_path / "radar.db")
    seed_pain(db)

    vendor_only = (f'Build this for {PAIN_QUOTE} using https://competitor.example/four '
                   '("charges $199/seat for the same manual workflow").')

    thesis = deep_validate(db, None, FakeLLM(vendor_only), FakeSearch())

    assert thesis is None
    assert db.connection.execute("SELECT COUNT(*) FROM theses").fetchone()[0] == 0
    detail = json.loads(db.connection.execute("SELECT detail_json FROM runs WHERE kind='deep'").fetchone()[0])
    assert detail["rejected"] is True and detail["recommendation_kind"] == "WATCH"
    assert "buyer" in detail["reason"].lower()


# "excerpt" is the span of that item's own body the fixture claims quote; the adapters ignore it.
VENDOR_ONLY_EVIDENCE = [
    {"url": "https://vendor.example/invoices", "title": "BillStack pricing",
     "body": "BillStack charges $199/seat for invoice reconciliation across billing vendors.",
     "excerpt": "charges $199/seat for invoice reconciliation"},
]
BUYER_EVIDENCE = [
    {"url": "https://reddit.example/warehouse-1", "title": "Label printing pain",
     "body": "Warehouse label printing is manual and takes hours every week.",
     "excerpt": "warehouse label printing is manual and takes hours"},
    {"url": "https://news.ycombinator.com/warehouse-2", "title": "Shipment bottleneck",
     "body": "Our shipment label workflow is a bottleneck; we stitch it by hand every week.",
     "excerpt": "shipment label workflow is a bottleneck"},
    {"url": "https://labelvendor.example/pricing", "title": "LabelFlow pricing",
     "body": "LabelFlow charges $149/seat for warehouse shipment label printing.",
     "excerpt": "charges $149/seat for warehouse shipment label printing"},
]
PAIN_QUOTES = {
    "pain-vendor": 'pain-vendor ("invoice reconciliation across billing vendors is manual")',
    "pain-buyers": 'pain-buyers ("warehouse shipment label printing workflow breaks every week")',
}


def cite(evidence):
    """Render the citation+excerpt pairs a claim needs to clear the verbatim gate."""
    return " and ".join(f'{item["url"]} ("{item["excerpt"]}")' for item in evidence)


class TwoClusterSearch:
    """Each cluster searches its own key terms, so evidence is keyed off the query."""
    def collect(self, query):
        return list(VENDOR_ONLY_EVIDENCE if "invoice" in query else BUYER_EVIDENCE)


class TwoClusterLLM(FakeLLM):
    """Cites whichever cluster's evidence the thesis payload was built from."""
    def __init__(self):
        super().__init__("")

    def classify(self, content, schema=None, max_tokens=None):
        if "Research evidence" in content:
            return super().classify(content, schema, max_tokens)
        vendor = "pain-vendor" in content
        pain_id = "pain-vendor" if vendor else "pain-buyers"
        urls = cite(VENDOR_ONLY_EVIDENCE if vendor else BUYER_EVIDENCE)
        self.recommendation = f"Build this for {PAIN_QUOTES[pain_id]} using {urls}."
        return super().classify(content, schema, max_tokens)


def seed_two_clusters(db):
    now = datetime.now(timezone.utc).isoformat()
    rows = [
        # Higher score, but the search only ever returns a vendor page: no reachable buyers.
        ("pain-vendor", "Invoice reconciliation across billing vendors is manual",
         "Finance teams at agencies", 30.0),
        # Lower score, but backed by independent demand plus commercial evidence.
        ("pain-buyers", "Warehouse shipment label printing workflow breaks every week",
         "Logistics operations managers", 20.0),
    ]
    for pain_id, text, icp, total in rows:
        seed_signal(db, pain_id, text)
        pain = Pain(pain_id, f"signal-{pain_id}", text, icp, "Ship on time", "Recurring weekly work",
                    "weekly", "hours lost", "spreadsheets", "budget approved", "none", "too slow",
                    ({"quote": text, "url": f"https://reddit.example/{pain_id}", "verified": True},),
                    (text,), (), "A", "en", now, "test")
        db.add_pain(pain)
        db.add_score(Score(pain_id, {"severity": 5}, total, "include", ("test",), now))


def test_deep_falls_through_a_rejected_top_cluster_to_a_viable_lower_ranked_one(tmp_path):
    """Codex P2: only validations[0] was ever synthesized, so a WATCH-grade top cluster
    suppressed a lower-ranked candidate that clears the VALIDATE/BUILD gate.
    """
    db = Database(tmp_path / "radar.db")
    seed_two_clusters(db)

    thesis = deep_validate(db, None, TwoClusterLLM(), TwoClusterSearch())

    assert thesis is not None
    assert thesis.confidence == "A"
    assert thesis.recommendation_kind == "VALIDATE"
    assert {row["url"] for row in thesis.evidence_matrix} == {item["url"] for item in BUYER_EVIDENCE}
    assert "https://vendor.example/invoices" not in thesis.evidence_ids
    # Single thesis per cycle, and a single deep run recording it.
    assert db.connection.execute("SELECT COUNT(*) FROM theses").fetchone()[0] == 1
    runs = db.connection.execute("SELECT detail_json FROM runs WHERE kind='deep'").fetchall()
    assert len(runs) == 1
    detail = json.loads(runs[0][0])
    assert detail["thesis"] == thesis.id and detail["qualified"] == 2
    # The skipped candidate is reported, not silently dropped.
    assert [r["recommendation_kind"] for r in detail["rejections"]] == ["WATCH"]


def test_deep_reports_one_aggregate_rejection_when_every_candidate_fails(tmp_path):
    """No candidate clears the gate: one deep run, one honest aggregate rejection, no thesis."""
    db = Database(tmp_path / "radar.db")
    seed_two_clusters(db)

    class VendorOnlySearch:
        def collect(self, query):
            return list(VENDOR_ONLY_EVIDENCE)

    class VendorOnlyLLM(FakeLLM):
        def __init__(self):
            super().__init__("")

        def classify(self, content, schema=None, max_tokens=None):
            if "Research evidence" not in content:
                pain_id = "pain-vendor" if "pain-vendor" in content else "pain-buyers"
                self.recommendation = f"Build this for {PAIN_QUOTES[pain_id]} using {cite(VENDOR_ONLY_EVIDENCE)}."
            return super().classify(content, schema, max_tokens)

    assert deep_validate(db, None, VendorOnlyLLM(), VendorOnlySearch()) is None
    assert db.connection.execute("SELECT COUNT(*) FROM theses").fetchone()[0] == 0
    runs = db.connection.execute("SELECT detail_json FROM runs WHERE kind='deep'").fetchall()
    assert len(runs) == 1
    detail = json.loads(runs[0][0])
    assert detail["rejected"] is True and detail["qualified"] == 2
    # Both candidates are named, in score order, with their own verdicts.
    assert [r["recommendation_kind"] for r in detail["rejections"]] == ["WATCH", "PASS"]
    assert "buyer" in detail["reason"].lower()


def test_confidence_uses_only_the_evidence_the_thesis_cites(tmp_path):
    """One cited demand URL is C, even when uncited demand and commercial hits sit in the search."""
    db = Database(tmp_path / "radar.db")
    seed_pain(db)

    cited_one = f'Build this for {PAIN_QUOTE} using https://reddit.example/one ("manual work takes hours").'

    thesis = deep_validate(db, None, FakeLLM(cited_one), FakeSearch())

    assert thesis is not None
    assert thesis.confidence not in {"A", "B"}
    assert thesis.confidence == "C"
    matrix_urls = {row["url"] for row in thesis.evidence_matrix}
    assert matrix_urls == {"https://reddit.example/one"}
    assert "https://competitor.example/four" not in thesis.evidence_ids
