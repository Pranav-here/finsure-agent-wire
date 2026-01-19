"""Relevance scoring for news items based on dual-keyword matching."""

import logging
import re
from typing import List

from .models import NewsItem

logger = logging.getLogger(__name__)

# ===========================
# AI Agent Keywords
# ===========================
AGENT_KEYWORDS = [
    'agent', 'agents', 'agentic',
    'autonomous', 'autonomy',
    'multi-agent', 'multi agent', 'multiagent',
    'llm agent', 'ai agent', 'intelligent agent',
    'tool use', 'tool-use', 'tool calling',
    'function calling',
    'orchestration', 'orchestrator',
    'planner', 'planning',
    'reasoning', 'chain-of-thought', 'cot',
    'langchain', 'langgraph', 'autogen', 'crewai',
    'agent framework', 'agentic workflow',
    'agentic ai', 'agentic system',
]

# ===========================
# Finance/Insurance Keywords
# ===========================
FINANCE_KEYWORDS = [
    'fintech', 'insurtech',
    'finance', 'financial', 'banking', 'bank',
    'insurance', 'insurer', 'underwriting', 'underwriter',
    'claims', 'claim processing',
    'fraud', 'fraud detection', 'anti-fraud',
    'risk', 'risk management', 'risk assessment',
    'compliance', 'regulatory', 'regulation',
    'kyc', 'aml', 'know your customer', 'anti-money laundering',
    'policy', 'premium', 'policyholder',
    'trading', 'trader', 'investment', 'investing',
    'asset management', 'wealth management',
    'credit', 'lending', 'loan',
    'payment', 'payments', 'transaction',
    'cryptocurrency', 'crypto', 'blockchain',
    'robo-advisor', 'algorithmic trading',
]

# ===========================
# Exclude Keywords (hard filter)
# ===========================
EXCLUDE_KEYWORDS = [
    'sports', 'sport', 'football', 'soccer', 'basketball', 'baseball',
    'celebrity', 'celebrities', 'gossip',
    'astrology', 'horoscope',
    'entertainment', 'movie', 'film',
    'gaming', 'video game', 'esports',
    'fashion', 'beauty',
    'recipe', 'cooking',
    'travel agent',  # Not AI agent
]


def should_exclude(text: str) -> bool:
    """
    Hard filter: exclude items matching exclude keywords.
    
    Args:
        text: Combined title + description text
        
    Returns:
        True if item should be excluded
    """
    text_lower = text.lower()
    for keyword in EXCLUDE_KEYWORDS:
        if re.search(r'\b' + re.escape(keyword) + r'\b', text_lower):
            return True
    return False


def count_keyword_matches(text: str, keywords: List[str]) -> int:
    """
    Count how many keywords appear in text (case-insensitive, word boundaries).
    
    Args:
        text: Text to search
        keywords: List of keywords to search for
        
    Returns:
        Number of unique keywords matched
    """
    text_lower = text.lower()
    matches = 0
    for keyword in keywords:
        # Use word boundaries to avoid partial matches
        pattern = r'\b' + re.escape(keyword) + r'\b'
        if re.search(pattern, text_lower):
            matches += 1
    return matches


def calculate_relevance_score(
    item: NewsItem,
    agent_weight: float = 1.0,
    finance_weight: float = 1.0,
    recency_weight: float = 0.5,
) -> float:
    """
    Calculate relevance score for a news item.
    
    Scoring logic:
    1. Must have BOTH agent signals AND finance/insurance signals (multiplicative)
    2. Base score = (agent_matches * agent_weight) * (finance_matches * finance_weight)
    3. Recency boost = hours_ago * recency_weight (newer = higher)
    4. Hard exclusion filter applied first
    
    Args:
        item: NewsItem to score
        agent_weight: Weight for agent keyword matches
        finance_weight: Weight for finance keyword matches
        recency_weight: Weight for recency boost
        
    Returns:
        Relevance score (0.0 if excluded or missing category)
    """
    # Combine title and description for analysis
    text = item.title
    if item.description:
        text += " " + item.description
    
    # Hard exclusion filter
    if should_exclude(text):
        logger.debug(f"Excluded (filter): {item.title}")
        return 0.0
    
    # Count keyword matches
    agent_matches = count_keyword_matches(text, AGENT_KEYWORDS)
    finance_matches = count_keyword_matches(text, FINANCE_KEYWORDS)
    
    # Must have BOTH categories
    if agent_matches == 0 or finance_matches == 0:
        logger.debug(
            f"Excluded (missing category): {item.title} "
            f"(agent={agent_matches}, finance={finance_matches})"
        )
        return 0.0
    
    # Base score (multiplicative to enforce dual requirement)
    base_score = (agent_matches * agent_weight) * (finance_matches * finance_weight)
    
    # Recency boost (optional)
    # Newer items get slight boost; this is already handled by sorting later
    # but we include it in score for transparency
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    hours_ago = (now - item.published_at).total_seconds() / 3600
    recency_boost = max(0, (24 - hours_ago) * recency_weight)
    
    total_score = base_score + recency_boost
    
    logger.debug(
        f"Scored: {item.title} | "
        f"Agent={agent_matches}, Finance={finance_matches}, "
        f"Base={base_score:.1f}, Recency={recency_boost:.1f}, Total={total_score:.1f}"
    )
    
    return total_score


def score_items(
    items: List[NewsItem],
    agent_weight: float = 1.0,
    finance_weight: float = 1.0,
    recency_weight: float = 0.5,
) -> List[NewsItem]:
    """
    Score all items and update their relevance_score field.
    
    Args:
        items: List of NewsItems to score
        agent_weight: Weight for agent keywords
        finance_weight: Weight for finance keywords
        recency_weight: Weight for recency
        
    Returns:
        Same list with updated scores
    """
    for item in items:
        item.relevance_score = calculate_relevance_score(
            item,
            agent_weight=agent_weight,
            finance_weight=finance_weight,
            recency_weight=recency_weight,
        )
    
    return items
