from typing import Iterable, List

from .config import Settings
from .models import Item


def _contains(text: str, keywords: Iterable[str]) -> List[str]:
    hits = []
    for kw in keywords:
        if kw.lower() in text:
            hits.append(kw)
    return hits


def score_item(item: Item, settings: Settings) -> float:
    """Return a relevance score; 0 means not relevant."""
    text = f"{item.title} {item.description or ''}".lower()
    if not text:
        return 0.0

    if any(bad in text for bad in settings.exclude_keywords):
        return 0.0

    agent_hits = _contains(text, settings.agent_keywords)
    finance_hits = _contains(text, settings.finance_keywords)

    if not agent_hits or not finance_hits:
        return 0.0

    score = settings.weight_agent * len(agent_hits) + settings.weight_finance * len(finance_hits)
    # Slight boost for longer descriptions that contain multiple signals
    if len(text) > 140 and len(agent_hits) + len(finance_hits) > 2:
        score += 0.5
    return score


def apply_scoring(items: List[Item], settings: Settings) -> List[Item]:
    scored: List[Item] = []
    for item in items:
        item.score = score_item(item, settings)
        if item.score >= settings.min_score:
            scored.append(item)
    scored.sort(key=lambda i: (i.score or 0, i.published_at), reverse=True)
    return scored


__all__ = ["score_item", "apply_scoring"]
