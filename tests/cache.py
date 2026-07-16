import time

import pytest

from app.cache import ResponseCache


def test_cache_stores_and_returns_value():
    cache = ResponseCache(ttl_seconds=30)

    cache.set("Hello", "world")

    assert cache.get("Hello") == "world"


def test_cache_is_case_insensitive_and_trims_whitespace():
    cache = ResponseCache(ttl_seconds=30)

    cache.set("  Hello  ", "world")

    assert cache.get("hello") == "world"


def test_cache_returns_none_when_entry_is_expired():
    cache = ResponseCache(ttl_seconds=0)

    cache.set("Hello", "world")

    assert cache.get("Hello") is None


def test_cache_stats_report_hits_misses_and_cached_entries():
    cache = ResponseCache(ttl_seconds=30)

    cache.set("Hello", "world")
    assert cache.get("Hello") == "world"
    assert cache.get("Missing") is None

    stats = cache.stats

    assert stats["hits"] == 1
    assert stats["misses"] == 1
    assert stats["cached_entries"] == 1
    assert stats["hit_rate"] == pytest.approx(0.5)
