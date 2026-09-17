"""The fork's extra news must obey the same dates as the primary vendor."""

from io import BytesIO

import pytest

from tradingagents.dataflows import google_news, news_aggregator, portuguese_rss, yfinance_news
from tradingagents.dataflows.rss_utils import parse_rss_entries

XML = """<rss><channel><title>Feed</title>
<item><title>FUTURE</title><pubDate>Sat, 10 May 2025 00:00:00 +0000</pubDate></item>
<item><title>UNDATED</title></item>
<item><title>VALID</title><link>https://example.com/evidence</link>
<pubDate>Fri, 09 May 2025 23:59:59 +0000</pubDate></item>
<item><title>OFFSET</title><pubDate>2025-05-10T01:00:00+05:00</pubDate></item>
</channel></rss>"""
DATES = {"start_date": "2025-05-01", "end_date": "2025-05-09"}


def test_filter_precedes_limit_and_keeps_provenance():
    entries = parse_rss_entries(XML, limit=1, **DATES)
    assert [entry["title"] for entry in entries] == ["VALID"]
    assert entries[0]["link"] == "https://example.com/evidence"
    assert entries[0]["pub_date"].isoformat() == "2025-05-09T23:59:59+00:00"
    assert len(parse_rss_entries(XML, **DATES)) == 2


@pytest.mark.parametrize("module,function", [
    (google_news, google_news.fetch_google_news_sentiment),
    (news_aggregator, news_aggregator.fetch_news_multi_source),
])
def test_all_extra_sources_filter_future_and_undated(monkeypatch, module, function):
    monkeypatch.setattr(module, "_fetch_rss", lambda *a, **k: XML)
    result = function("BCP.LS", **DATES)
    assert "VALID" in result and "OFFSET" in result
    assert "FUTURE" not in result and "UNDATED" not in result
    assert "https://example.com/evidence" in result
    assert "2025-05-09T23:59:59+00:00" in result


def test_portuguese_feeds_use_requested_window(monkeypatch):
    monkeypatch.setattr(portuguese_rss.urllib.request, "urlopen",
                        lambda *a, **k: BytesIO(XML.encode()))
    result = portuguese_rss.get_portuguese_news(**DATES)
    assert "VALID" in result and "FUTURE" not in result and "UNDATED" not in result
    assert "https://example.com/evidence" in result


def test_yahoo_passes_dates_to_portuguese_extension(monkeypatch):
    class Search:
        news = [{"title": "Past", "providerPublishTime": 1746748800}]

    calls = []
    monkeypatch.setattr(yfinance_news.yf, "Search", lambda *a, **k: Search())
    monkeypatch.setattr(yfinance_news, "get_portuguese_news",
                        lambda **kw: calls.append(kw) or "RSS VERIFICADO")
    result = yfinance_news.get_global_news_yfinance("2025-05-09", look_back_days=8)
    assert calls == [DATES]
    assert "RSS VERIFICADO" in result


@pytest.mark.parametrize("kwargs", [
    {"start_date": "2025-05-01"},
    {"start_date": "2025-05-10", "end_date": "2025-05-01"},
])
def test_invalid_windows_are_rejected(kwargs):
    with pytest.raises(ValueError):
        parse_rss_entries(XML, **kwargs)
