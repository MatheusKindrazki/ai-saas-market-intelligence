"""Small, deterministic text processing utilities using only the stdlib."""
from __future__ import annotations
import re
from dataclasses import dataclass
from typing import Iterable
from .models import Signal

_STOPS = {"en": {"the","and","with","for","this","that","have","hours","manual","too"},
          "pt": {"que","para","com","uma","não","muito","planilha","horas","manual"},
          "es": {"que","para","con","una","muy","horas","manual","buscar","alternativa"}}
_COMMON = {"the","and","for","with","this","that","from","have","need","tool","software","how","are","was","but","not","all"}

def detect_language(text: str) -> str:
    words = set(re.findall(r"[\wáéíóúñç]+", text.lower()))
    scores = {lang: len(words & stop) for lang, stop in _STOPS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] else "unknown"

def normalize_keywords(text: str) -> set[str]:
    return {w for w in re.findall(r"[a-záéíóúñç]{3,}", text.lower()) if w not in _COMMON}

def jaccard(left: set[str], right: set[str]) -> float:
    return len(left & right) / len(left | right) if left | right else 0.0

def extract_quote(text: str, limit: int = 280) -> str:
    sentence = re.split(r"(?<=[.!?])\s+", re.sub(r"\s+", " ", text).strip())[0]
    return sentence[:limit]

@dataclass(frozen=True)
class Cluster:
    id: str
    signals: tuple[Signal, ...]
    keywords: frozenset[str]
    matched_keywords: tuple[str, ...]

def cluster_signals(signals: Iterable[Signal], threshold: float = .35) -> list[Cluster]:
    buckets: list[list[Signal]] = []; keys: list[set[str]] = []; matches: list[set[str]] = []
    for signal in sorted(signals, key=lambda s: (s.content_hash, s.id)):
        key = normalize_keywords(f"{signal.title} {signal.body}")
        found = next((i for i, existing in enumerate(keys) if jaccard(key, existing) >= threshold), None)
        if found is None: buckets.append([signal]); keys.append(key); matches.append(set())
        else: matches[found].update(key & keys[found]); buckets[found].append(signal); keys[found].update(key)
    return [Cluster(f"cluster-{i+1}", tuple(items), frozenset(keys[i]), tuple(sorted(matches[i])))
            for i, items in enumerate(buckets)]
