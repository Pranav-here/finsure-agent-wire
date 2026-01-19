"""Relevance scoring for news items based on dual-keyword matching."""

import logging
import re
from typing import List

from .models import NewsItem

logger = logging.getLogger(__name__)

# ===========================
# AI Keywords (Broadened from just agents)
# ===========================
AI_KEYWORDS = [
    # General AI
    'ai', 'artificial intelligence',
    'machine learning', 'ml', 'deep learning', 
    'neural network', 'neural net',
    'llm', 'large language model',
    'gpt', 'generative ai', 'gen ai',
    'transformer', 'chatbot', 'chat bot',
    'algorithm', 'algorithmic',
    'data science', 'predictive analytics',
    'nlp', 'natural language processing',
    'computer vision',
    # AI Agents (still important)
    'agent', 'agents', 'agentic',
    'autonomous', 'autonomy', 'automation',
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
    'credit', 'lending', 'loan', 'mortgage',
    'payment', 'payments', 'transaction',
    'cryptocurrency', 'crypto', 'blockchain',
    'robo-advisor', 'algorithmic trading',
    'portfolio', 'derivatives', 'defi',
    'hedge fund', 'actuary', 'actuarial',
]

# ===========================
# Exclude Keywords (hard filter)
# ===========================
EXCLUDE_KEYWORDS = [
    # Entertainment/Off-topic
    'sports', 'sport', 'football', 'soccer', 'basketball', 'baseball',
    'celebrity', 'celebrities', 'gossip',
    'astrology', 'horoscope',
    'entertainment', 'movie', 'film',
    'gaming', 'video game', 'esports',
    'fashion', 'beauty',
    'recipe', 'cooking',
    'travel agent',  # Not AI agent
    # Clickbait/Scams (NEW!)
    'passive income', 'easy money', 'get rich',
    'no work', 'no boss', 'work from home',
    'side hustle', 'make money fast',
    'clickbait', 'scam',
    '$20k', '$10k', '$5k', 'month passive',
    'real proof', 'no experience needed',
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
    ai_matches = count_keyword_matches(text, AI_KEYWORDS)
    finance_matches = count_keyword_matches(text, FINANCE_KEYWORDS)
    
    # Must have BOTH categories
    if ai_matches == 0 or finance_matches == 0:
        logger.debug(
            f"Excluded (missing category): {item.title} "
            f"(ai={ai_matches}, finance={finance_matches})"
        )
        return 0.0
    
    # Base score (multiplicative to enforce dual requirement)
    base_score = (ai_matches * agent_weight) * (finance_matches * finance_weight)
    
    # Recency boost (optional)
    # Newer items get slight boost; this is already handled by sorting later
    # but we include it in score for transparency
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc)
    hours_ago = (now - item.published_at).total_seconds() / 3600
    recency_boost = max(0, (168 - hours_ago) * recency_weight / 10)  # Adjusted for 7-day window
    
    # Source credibility boost
    # Research papers and premium news sources are higher quality
    source_boost = 0.0
    if item.source == 'arxiv':
        source_boost = 10.0  # Strong boost for academic papers
    elif item.source == 'rss':
        # Premium RSS feeds get modest boost
        if item.domain and any(premium in item.domain.lower() for premium in 
                               ['ft.com', 'reuters', 'bloomberg', 'wsj', 'americanbanker', 
                                'insurancejournal', 'technologyreview.com', 'wired.com', 
                                'techcrunch.com', 'venturebeat.com', 'coindesk.com']):
            source_boost = 5.0
    # GDELT gets no boost (baseline)
    
    total_score = base_score + recency_boost + source_boost
    
    logger.debug(
        f"Scored: {item.title} | "
        f"AI={ai_matches}, Finance={finance_matches}, "
        f"Base={base_score:.1f}, Recency={recency_boost:.1f}, Source={source_boost:.1f}, Total={total_score:.1f}"
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
