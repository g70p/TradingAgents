"""Canonical PT-PT/English decisions; invalid output requires REVIEW.

Adapted from upstream 43fc275. Narrative mentions must not become signals.
"""
from __future__ import annotations

import re
import unicodedata

RATINGS_5_TIER = ("Buy", "Overweight", "Hold", "Underweight", "Sell")
RATING_REVIEW = "REVIEW"
_ALIASES = {
    "buy": "Buy", "comprar": "Buy", "compra": "Buy",
    "overweight": "Overweight", "sobreponderar": "Overweight",
    "hold": "Hold", "manter": "Hold",
    "underweight": "Underweight", "subponderar": "Underweight",
    "sell": "Sell", "vender": "Sell", "venda": "Sell",
    "review": RATING_REVIEW, "rever": RATING_REVIEW,
}
_LABEL = re.compile(
    r"^\s*(?:(?:\d+[.)]|[-*])\s*)?(rating|classificação|classificacao|ação|acao|action|"
    r"recomendação|recomendacao)\s*[:：-]\s*(\w+)(.*)$", re.IGNORECASE,
)
_CHOICE_LIST = re.compile(r"[/|<>]|\b(?:ou|or)\b", re.IGNORECASE)


def extract_rating(text: str) -> str | None:
    """Read explicit fields, or a response consisting solely of one rating."""
    if not text:
        return None
    norm = unicodedata.normalize("NFKC", text).replace("**", "").replace("`", "")
    ratings = set()
    for line in norm.splitlines():
        match = _LABEL.match(line)
        if match:
            value = _ALIASES.get(match.group(2).casefold())
            if value is None and match.group(1).casefold() in {"ação", "acao", "action"}:
                # AVA action paragraphs are narrative, not a rating field.
                continue
            if value is None or _CHOICE_LIST.search(match.group(3)):
                return None
            ratings.add(value)
    if ratings:
        return ratings.pop() if len(ratings) == 1 else None
    return _ALIASES.get(norm.strip().rstrip(".!;").casefold())


def parse_rating(text: str, default: str = "Hold") -> str:
    """Compatibility wrapper. Operational consumers should use extract_rating."""
    rating = extract_rating(text)
    return rating if rating is not None else default


def is_review(signal: str) -> bool:
    return signal == RATING_REVIEW
