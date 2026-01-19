#!/usr/bin/env python3
"""
Test script for validating relevance scoring.

Run this to see how different titles score with the current keyword configuration.
Use this to tune your scoring weights and keywords.
"""

import sys
from pathlib import Path
from datetime import datetime, timezone

# Add src to path so imports work
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from finsure_agent_wire.models import NewsItem
from finsure_agent_wire.scoring import calculate_relevance_score


# Test cases: mix of relevant and irrelevant
TEST_TITLES = [
    # Should score HIGH (both AI agents + finance/insurance)
    {
        "title": "Anthropic launches autonomous agents for fraud detection in banking sector",
        "description": "New AI agent framework helps financial institutions detect fraudulent transactions using multi-agent systems",
        "expected": "HIGH"
    },
    {
        "title": "LangChain agents revolutionize insurance claims processing at major insurtech startup",
        "description": "Agentic AI reduces claim processing time by 80% through autonomous underwriting",
        "expected": "HIGH"
    },
    {
        "title": "Goldman Sachs deploys multi-agent AI system for algorithmic trading",
        "description": "Investment bank uses LLM agents with tool-calling capabilities for real-time market analysis",
        "expected": "HIGH"
    },
    {
        "title": "Insurtech company builds agentic workflow for policy risk assessment",
        "description": "New autonomous system handles compliance checks and KYC verification for insurance policies",
        "expected": "HIGH"
    },
    
    # Should score MEDIUM (one category strong, other weak)
    {
        "title": "New AI agent framework released for general business automation",
        "description": "LangGraph enables building autonomous agents for various enterprise use cases",
        "expected": "MEDIUM/LOW"
    },
    {
        "title": "Fintech startup raises $50M for payment processing platform",
        "description": "New funding will expand digital banking services and improve transaction speed",
        "expected": "LOW"  # Finance but no AI agents
    },
    
    # Should score LOW/ZERO (irrelevant)
    {
        "title": "Sports agent signs new deal with basketball player",
        "description": "Entertainment industry news about celebrity contracts",
        "expected": "ZERO"  # Not AI agent, excluded by filter
    },
    {
        "title": "Travel agent offers deals on vacation packages",
        "description": "Tourism industry promotions for holiday season",
        "expected": "ZERO"  # Not AI agent, excluded by filter
    },
]


def print_score_breakdown(item: NewsItem, score: float) -> None:
    """Pretty print score breakdown."""
    print(f"\nTitle: {item.title}")
    print(f"Description: {item.description[:100]}..." if len(item.description or '') > 100 else f"Description: {item.description}")
    print(f"Score: {score:.2f}")
    
    if score == 0:
        print("Result: FILTERED OUT (excluded or missing required keywords)")
    elif score < 3:
        print("Result: LOW relevance")
    elif score < 6:
        print("Result: MEDIUM relevance")
    else:
        print("Result: HIGH relevance")
    
    print("-" * 80)


def main():
    """Run scoring tests."""
    print("=" * 80)
    print("RELEVANCE SCORING TEST")
    print("=" * 80)
    print("\nThis validates that the scoring system correctly identifies relevant content.")
    print("Items must have BOTH AI agent signals AND finance/insurance signals to score.\n")
    
    for i, test_case in enumerate(TEST_TITLES, 1):
        item = NewsItem(
            url=f"https://example.com/article-{i}",
            title=test_case["title"],
            description=test_case.get("description", ""),
            source="test",
            published_at=datetime.now(timezone.utc),
        )
        
        score = calculate_relevance_score(item)
        print_score_breakdown(item, score)
    
    print("\n" + "=" * 80)
    print("SCORING TEST COMPLETE")
    print("=" * 80)
    print("\nIf scores don't match expectations, adjust keywords in src/finsure_agent_wire/scoring.py")
    print("or tune weights in .env (AGENT_KEYWORD_WEIGHT, FINANCE_KEYWORD_WEIGHT)")


if __name__ == '__main__':
    main()
