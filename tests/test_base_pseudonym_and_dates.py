from __future__ import annotations

import hashlib
from dataclasses import replace

import pytest

from radar.config import Config
from radar.sources import base
from radar.sources.base import (
    BaseSource,
    SourceError,
    author_pseudonym,
    author_salt,
    parse_timestamp,
    raw_signal,
)


@pytest.fixture
def cfg(tmp_path, monkeypatch):
    monkeypatch.setattr(base, "_salt_cache", {})
    return replace(Config(), db_path=tmp_path / "radar.db", cache_dir=tmp_path / "cache", salt_path=tmp_path / "secretsalt")


def test_salt_is_created_once_and_reused(cfg):
    salt = author_salt(cfg)

    assert cfg.salt_path.exists()
    assert len(salt) >= 32
    assert cfg.salt_path.read_bytes().strip() == salt
    assert author_salt(cfg) == salt


def test_pseudonym_is_salted_stable_and_distinct(cfg):
    first = author_pseudonym("maker", cfg)

    assert first == author_pseudonym("maker", cfg)
    assert first != author_pseudonym("other-maker", cfg)
    assert first != hashlib.sha256(b"maker").hexdigest()
    assert first == hashlib.sha256(author_salt(cfg) + b"maker").hexdigest()


def test_pseudonym_differs_across_salts(cfg, tmp_path):
    other = replace(cfg, salt_path=tmp_path / "other-salt")

    assert author_salt(other) != author_salt(cfg)
    assert author_pseudonym("maker", other) != author_pseudonym("maker", cfg)


def test_empty_salt_file_fails_loudly(cfg):
    cfg.salt_path.parent.mkdir(parents=True, exist_ok=True)
    cfg.salt_path.write_bytes(b"")

    with pytest.raises(SourceError):
        author_salt(cfg)


def test_raw_signal_stores_salted_pseudonym_not_the_handle(cfg):
    signal = raw_signal(source="devto", family="forums", external_id="42", url="https://dev.to/x",
                        title="t", body="b", author="maker", cfg=cfg)

    assert signal.author_pseudonym == author_pseudonym("maker", cfg)
    assert signal.author_pseudonym != hashlib.sha256(b"maker").hexdigest()
    assert "maker" not in str(signal)


def test_raw_signal_without_author_has_no_pseudonym(cfg):
    signal = raw_signal(source="wordpress", family="forums", external_id="1", url="https://x",
                        title="t", body="b", cfg=cfg)

    assert signal.author_pseudonym is None


def test_parse_timestamp_accepts_iso_and_rfc2822():
    iso = parse_timestamp("2026-08-16T10:00:00Z")
    rfc = parse_timestamp("Sun, 16 Aug 2026 10:00:00 GMT")

    assert iso == rfc
    assert iso.tzinfo is not None
    assert parse_timestamp("not a date") is None
    assert parse_timestamp("2026-08-16").tzinfo is not None


class _Signal:
    def __init__(self, published_at: str | None) -> None:
        self.published_at = published_at


def test_keep_since_filters_rfc2822_pubdates():
    source = BaseSource()
    signals = [_Signal("Sun, 16 Aug 2026 10:00:00 GMT"), _Signal("Fri, 01 Aug 2026 10:00:00 GMT")]

    kept = source.keep_since(signals, "2026-08-10")

    assert [s.published_at for s in kept] == ["Sun, 16 Aug 2026 10:00:00 GMT"]


def test_keep_since_keeps_unparseable_dates_instead_of_raising():
    source = BaseSource()

    kept = source.keep_since([_Signal("whenever"), _Signal(None)], "2026-08-10")

    assert len(kept) == 2
    assert len(source.keep_since([_Signal("2026-08-01T00:00:00Z")], "garbage")) == 1


def test_keep_since_mixes_iso_and_rfc2822_against_naive_cutoff():
    source = BaseSource()
    signals = [_Signal("2026-08-16T10:00:00Z"), _Signal("Fri, 01 Aug 2026 10:00:00 -0300")]

    kept = source.keep_since(signals, "2026-08-10T00:00:00")

    assert [s.published_at for s in kept] == ["2026-08-16T10:00:00Z"]
