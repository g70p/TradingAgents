"""RSS parsing with publication dates and a shared point-in-time boundary."""

from datetime import datetime
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

from .date_window import in_window, to_utc


def parse_publication_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return to_utc(parsedate_to_datetime(value))
    except (TypeError, ValueError, OverflowError):
        try:
            return to_utc(datetime.fromisoformat(value.replace("Z", "+00:00")))
        except ValueError:
            return None


def parse_rss_entries(xml_text: str, limit: int = 20, *,
                      start_date: str | None = None,
                      end_date: str | None = None) -> list[dict]:
    """Filter before limiting. Undated entries cannot substantiate a historical run."""
    if bool(start_date) != bool(end_date):
        raise ValueError("Supply both start_date and end_date")
    start = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
    end = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
    if start and end < start:
        raise ValueError("end_date must not precede start_date")
    if limit <= 0:
        return []
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        return []
    entries, seen = [], set()
    for item in root.iter("item"):
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        published = parse_publication_date(item.findtext("pubDate") or "")
        if not title or title in seen:
            continue
        if start is not None and not in_window(published, start, end):
            continue
        seen.add(title)
        entries.append({"title": title, "link": link, "pub_date": published,
                        "summary": (item.findtext("description") or "").strip()})
        if len(entries) >= limit:
            break
    return entries


def rss_lines(xml_text: str, limit: int = 20, *,
              start_date: str | None = None, end_date: str | None = None) -> list[str]:
    """Keep source URLs and publication time visible to the analyst and reader."""
    lines = []
    for item in parse_rss_entries(xml_text, limit, start_date=start_date, end_date=end_date):
        stamp = item["pub_date"].isoformat() if item["pub_date"] else "data indisponível"
        link = f" | {item['link']}" if item["link"] else ""
        lines.append(f"{item['title']} — publicado: {stamp}{link}")
    return lines
